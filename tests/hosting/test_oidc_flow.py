"""Offline OIDC authorization-code/PKCE fixtures using the actual SDK client class."""

import base64
import hashlib
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from authlib.integrations import starlette_client
from authlib.integrations.base_client.errors import OAuthError
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from starlette.routing import Route
from streamlit.web.server.starlette import starlette_auth_routes as native

from yemen_customer_service.hosting.auth import authorize_native_user


@pytest.mark.parametrize("attack", [None, "state", "nonce", "signature"])
async def test_native_client_code_exchange_pkce_state_and_jwt_offline(hosted_settings, attack):
    issuer = hosted_settings.issuer
    key = RSAKey.generate_key(2048, parameters={"kid": "fixture-oidc-key"})
    authorization = {}
    calls = []

    def provider(request):
        assert request.url.host == "oidc.example.invalid"
        calls.append(request.url.path)
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "issuer": issuer,
                    "authorization_endpoint": issuer + "/authorize",
                    "token_endpoint": issuer + "/token",
                    "jwks_uri": issuer + "/jwks",
                    "response_types_supported": ["code"],
                    "id_token_signing_alg_values_supported": ["RS256"],
                    "code_challenge_methods_supported": ["S256"],
                },
            )
        if request.url.path == "/jwks":
            return httpx.Response(200, json={"keys": [key.as_dict(private=False)]})
        assert request.url.path == "/token"
        params = parse_qs(request.content.decode())
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(params["code_verifier"][0].encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        assert challenge == authorization["code_challenge"][0]
        now = int(time.time())
        payload = {
            "iss": issuer,
            "sub": "fixture-A",
            "aud": "fixture-client",
            "iat": now - 1,
            "exp": now + 300,
            "nonce": "wrong-nonce" if attack == "nonce" else authorization["nonce"][0],
        }
        signing = (
            RSAKey.generate_key(2048, parameters={"kid": "fixture-oidc-key"})
            if attack == "signature"
            else key
        )
        encoded = jwt.encode({"alg": "RS256", "kid": "fixture-oidc-key"}, payload, signing)
        return httpx.Response(
            200,
            json={
                "id_token": encoded,
                "access_token": "offline-fixture-access",
                "token_type": "Bearer",
                "expires_in": 300,
            },
        )

    oauth = native._create_streamlit_oauth_class(starlette_client)()
    client = oauth.register(
        "reviewer",
        client_id="fixture-client",
        client_secret="fixture-client-secret",
        server_metadata_url=hosted_settings.metadata_url,
        client_kwargs={"scope": "openid", "transport": httpx.MockTransport(provider)},
    )

    async def login(request):
        return await client.authorize_redirect(request, "https://app.example.invalid/callback")

    async def callback(request):
        try:
            token = await client.authorize_access_token(request)
            claims = dict(token["userinfo"], is_logged_in=True)
            authorize_native_user(claims, hosted_settings, time.time())
            return Response("AUTHENTICATED")
        except (OAuthError, JoseError):
            return Response("DENIED", status_code=403)

    app = Starlette(routes=[Route("/login", login), Route("/callback", callback)])
    app.add_middleware(
        SessionMiddleware, secret_key="offline-fixture-state-cookie-secret", https_only=True
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="https://app.example.invalid"
    ) as browser:
        response = await browser.get("/login")
        assert response.status_code == 302
        authorization.update(parse_qs(urlsplit(response.headers["location"]).query))
        assert authorization["code_challenge_method"] == ["S256"]
        state = "forged-state" if attack == "state" else authorization["state"][0]
        result = await browser.get(
            "/callback", params={"code": "offline-fixture-code", "state": state}
        )
        assert result.status_code == (200 if attack is None else 403)
        if attack == "state":
            assert "/token" not in calls
        if attack is None:
            assert result.text == "AUTHENTICATED"
            # The state is consumed: replay does not authorize another exchange.
            replay = await browser.get(
                "/callback", params={"code": "offline-fixture-code", "state": state}
            )
            assert replay.status_code == 403
