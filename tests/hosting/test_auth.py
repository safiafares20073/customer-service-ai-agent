import time

import pytest
from authlib.integrations.starlette_client import OAuth
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey

from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.settings import Settings
from yemen_customer_service.tool_server.models import SafeError


@pytest.mark.parametrize(
    "change",
    [
        {"is_logged_in": False},
        {"sub": "demo-a"},
        {"sub": "fixture-foreign"},
        {"iss": "https://attacker.example.invalid"},
        {"aud": "wrong-client"},
        {"exp": 0},
        {"iat": 0},
        {"nonce": ""},
        {"iat": True},
        {"exp": float("inf")},
        {"iat": 9999999999},
        {"aud": ["fixture-client", "other"], "azp": "other"},
    ],
)
def test_untrusted_or_expired_claims_rejected(hosted_settings, claims, change):
    claims.update(change)
    with pytest.raises(SafeError):
        authorize_native_user(claims, hosted_settings, time.time())


def test_identity_is_issuer_subject_scoped_not_email(hosted_settings, claims):
    a = authorize_native_user(claims, hosted_settings, time.time())
    claims.update(email="forged@example.invalid", name="Other person")
    b = authorize_native_user(claims, hosted_settings, time.time())
    assert a == b and a.principal.startswith("R-")
    assert "fixture-A" not in a.principal
    claims.update(sub="fixture-B")
    assert authorize_native_user(claims, hosted_settings, time.time()).principal != a.principal


def test_native_cookie_age_is_not_app_session_lifetime(hosted_settings, claims):
    now = claims["iat"] + 901
    assert claims["exp"] > now
    with pytest.raises(SafeError):
        authorize_native_user(claims, hosted_settings, now)


@pytest.mark.parametrize(
    "key,value",
    [
        ("APP_ENV", "development"),
        ("ENABLE_DEMO_AUTH", "true"),
        ("UI_PROVIDER", "fixture"),
        ("HOSTED_ORIGIN", "http://example.invalid"),
        ("HOSTED_COOKIE_SECRET", "short"),
        ("HOSTED_GLOBAL_BUDGET_USD", "NaN"),
        ("HOSTED_SESSION_SECONDS", "3600"),
        ("HOSTED_PAID_ENABLED", "true"),
        ("OIDC_METADATA_URL", "https://other.example.invalid/config"),
    ],
)
def test_insecure_settings_fail_closed(hosted_settings, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises((ValueError, KeyError)):
        Settings.load()


@pytest.fixture(scope="module")
def jwt_key():
    return RSAKey.generate_key(2048, parameters={"kid": "offline-fixture-key"})


@pytest.mark.parametrize("attack", [None, "signature", "audience", "issuer", "nonce", "expired"])
async def test_actual_authlib_oidc_crypto_validation_offline(jwt_key, attack):
    # Same Authlib parse_id_token used by native Streamlit; generated offline keys.
    now = int(time.time())
    payload = {
        "iss": "https://oidc.example.invalid",
        "sub": "fixture-A",
        "aud": "fixture-client",
        "iat": now - 1,
        "exp": now + 600,
        "nonce": "offline-fixture-nonce",
    }
    if attack == "audience":
        payload["aud"] = "wrong-client"
    if attack == "issuer":
        payload["iss"] = "https://attacker.example.invalid"
    if attack == "nonce":
        payload["nonce"] = "wrong-nonce"
    if attack == "expired":
        payload["exp"] = now - 1000
    signing = (
        RSAKey.generate_key(2048, parameters={"kid": "offline-fixture-key"})
        if attack == "signature"
        else jwt_key
    )
    token = jwt.encode({"alg": "RS256", "kid": "offline-fixture-key"}, payload, signing)
    client = OAuth().register("reviewer", client_id="fixture-client")
    client.server_metadata.update(
        issuer="https://oidc.example.invalid",
        id_token_signing_alg_values_supported=["RS256"],
        jwks={"keys": [jwt_key.as_dict(private=False)]},
        _loaded_at=time.time(),
    )
    if attack:
        with pytest.raises(JoseError):
            await client.parse_id_token({"id_token": token}, "offline-fixture-nonce", leeway=0)
    else:
        user = await client.parse_id_token({"id_token": token}, "offline-fixture-nonce", leeway=0)
        assert user["sub"] == "fixture-A" and user["nonce"] == "offline-fixture-nonce"
