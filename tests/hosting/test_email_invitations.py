"""Synthetic Google claims and real SQLite: no real identity/provider calls."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal

import httpx
import pytest
from authlib.integrations.starlette_client import OAuth
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import RSAKey

from yemen_customer_service.agent.pricing import Pricing, Usage
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.settings import GOOGLE_ISSUER, Settings
from yemen_customer_service.hosting.spending import Spending
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database
from yemen_customer_service.tool_server.models import SafeError


@pytest.fixture
def invitation(hosted_settings, tmp_path):
    cfg = replace(
        hosted_settings,
        issuer=GOOGLE_ISSUER,
        metadata_url=GOOGLE_ISSUER + "/.well-known/openid-configuration",
        invites=((GOOGLE_ISSUER, "legacy-subject"),),
        email_invites=("professor@example.invalid",),
    )
    store = HostedStore(Database(tmp_path / "email.sqlite3"))
    store.initialize_hosted(evidence_mode="fixture")
    store.configure(cfg)
    now = int(time.time())
    claims = dict(
        is_logged_in=True,
        iss=GOOGLE_ISSUER,
        sub="new-professor-subject",
        aud=cfg.client_id,
        iat=now - 1,
        exp=now + 600,
        nonce="first-login-nonce",
        email="Professor@Example.Invalid",
        email_verified=True,
    )
    return cfg, store, claims


def authorize(invitation, **changes):
    cfg, store, claims = invitation
    return authorize_native_user({**claims, **changes}, cfg, time.time(), store=store)


def test_first_login_is_private_case_normalized_and_stable(invitation):
    cfg, store, claims = invitation
    login = authorize(invitation)
    store.register_login(login)
    token = store.provision(login, tasks_per_hour=5)
    Journal(store, token).remember("Synthetic principal-scoped fact")
    assert login.principal == cfg.principal(GOOGLE_ISSUER, claims["sub"])
    with store.db.connect() as c:
        row = c.execute("SELECT * FROM hosted_email_invites").fetchone()
        assert row["email_hash"] == cfg.email_hash("professor@example.invalid")
        assert row["principal"] == login.principal and row["bound_at"] > 0
    assert b"professor@example.invalid" not in store.db.path.read_bytes().lower()
    # Subsequent identity authority is the bound issuer/subject, not a changed email.
    renamed = authorize(invitation, nonce="renamed", email="renamed@example.invalid")
    assert renamed.principal == login.principal
    without_email = {k: v for k, v in claims.items() if k not in {"email", "email_verified"}}
    assert (
        authorize_native_user(without_email, cfg, time.time(), store=store).principal
        == login.principal
    )
    reopened = HostedStore(Database(store.db.path))
    reopened.initialize_hosted(evidence_mode="fixture")
    reopened.configure(cfg)
    assert Journal(reopened, token).memory() == ["Synthetic principal-scoped fact"]
    assert authorize(invitation, nonce="restart").principal == login.principal


@pytest.mark.parametrize(
    "change",
    [
        {"email": "other@example.invalid"},
        {"email": "professor+extra@example.invalid"},
        {"email": "prof.essor@example.invalid"},
        {"email": " professor@example.invalid"},
        {"email": None},
        {"email_verified": False},
        {"email_verified": "true"},
        {"email_verified": 1},
        {"iss": "https://attacker.example.invalid"},
        {"aud": "other-client"},
        {"nonce": ""},
        {"iat": True},
        {"exp": 0},
        {"iat": 9999999999},
        {"sub": ""},
        {"sub": "x" * 257},
        {"is_logged_in": False},
    ],
)
def test_bad_claims_cannot_bind_or_create_accounts(invitation, change):
    _, store, _ = invitation
    with pytest.raises(SafeError):
        authorize(invitation, **change)
    with store.db.connect() as c:
        assert (
            c.execute(
                "SELECT count(*) FROM hosted_email_invites WHERE principal IS NOT NULL"
            ).fetchone()[0]
            == 0
        )
        assert c.execute("SELECT count(*) FROM customers").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 0


def test_subject_substitution_and_bound_unverified_claim_are_denied(invitation):
    _, store, _ = invitation
    first = authorize(invitation)
    store.register_login(first)
    for changes in [
        {"sub": "substitute", "nonce": "fresh"},
        {"email_verified": False, "nonce": "fresh"},
    ]:
        with pytest.raises(SafeError):
            authorize(invitation, **changes)
    with store.db.connect() as c:
        assert (
            c.execute("SELECT principal FROM hosted_email_invites").fetchone()[0] == first.principal
        )


def test_logout_cookie_replay_cannot_enroll_or_reauthorize(invitation):
    cfg, store, claims = invitation
    legacy = replace(cfg, invites=(*cfg.invites, (cfg.issuer, claims["sub"])))
    store.configure(legacy)
    old = authorize_native_user(claims, legacy, time.time(), store=store)
    store.register_login(old)
    store.revoke(old)
    store.configure(cfg)
    with pytest.raises(SafeError):
        authorize(invitation)
    with store.db.connect() as c:
        assert c.execute("SELECT principal FROM hosted_email_invites").fetchone()[0] is None
    fresh = authorize(invitation, nonce="genuinely-new-login")
    store.register_login(fresh)
    with pytest.raises(SafeError):
        authorize(invitation)
    with pytest.raises(SafeError):
        store.register_login(old)


def test_concurrent_first_logins_only_one_subject_wins(invitation):
    def attempt(sub):
        try:
            return authorize(invitation, sub=sub, nonce=sub).principal
        except SafeError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        result = list(executor.map(attempt, ["race-A", "race-B"]))
    assert len([r for r in result if r]) == 1
    with invitation[1].db.connect() as c:
        assert c.execute("SELECT principal FROM hosted_email_invites").fetchone()[0] in result


def test_additive_migration_preserves_legacy_sessions_memory_and_spend(invitation):
    cfg, store, claims = invitation
    cfg = replace(
        cfg,
        paid_enabled=True,
        global_budget=Decimal("3"),
        principal_budget=Decimal(".1"),
        approval_until=time.time() + 600,
    )
    store.configure(cfg)
    store.set_kill(enabled=True)
    legacy = authorize_native_user({**claims, "sub": "legacy-subject"}, cfg, time.time())
    store.register_login(legacy)
    token = store.provision(legacy, tasks_per_hour=5)
    Journal(store, token).remember("Legacy private fixture fact")
    price = Pricing.load("config/model_pricing.json", "gpt-6-luna")
    spending = Spending(store, token)
    record = spending.reserve(Decimal(".001"), price, "fixture")
    spending.reconcile(record, price, Usage(100, 20, 0), bound=1000, output_limit=512)
    tables = [
        "customers",
        "hosted_logins",
        "sessions",
        "tasks",
        "memory",
        "hosted_calls",
        "hosted_control",
    ]
    with store.db.connect(write=True) as c:
        c.execute("DROP TABLE hosted_email_invites")
        c.execute("DELETE FROM metadata WHERE key='hosted_email_invitation_version'")
        before = {t: [tuple(r) for r in c.execute("SELECT * FROM " + t)] for t in tables}
    reopened = HostedStore(Database(store.db.path))
    for _ in range(2):
        reopened.initialize_hosted(evidence_mode="fixture")
        reopened.configure(cfg)
    with reopened.db.connect() as c:
        assert before == {t: [tuple(r) for r in c.execute("SELECT * FROM " + t)] for t in tables}
        assert c.execute("PRAGMA user_version").fetchone()[0] == 2
        assert (
            c.execute("SELECT value FROM metadata WHERE key='hosted_schema_version'").fetchone()[0]
            == "1"
        )
        assert (
            c.execute(
                "SELECT value FROM metadata WHERE key='hosted_email_invitation_version'"
            ).fetchone()[0]
            == "1"
        )
    assert Journal(reopened, token).memory() == ["Legacy private fixture fact"]
    assert (
        authorize_native_user({**claims, "sub": "legacy-subject"}, cfg, time.time()).principal
        == legacy.principal
    )
    # Removal, content purge and re-addition never recycle a bound email to a new subject.
    login = authorize_native_user(claims, cfg, time.time(), store=reopened)
    reopened.register_login(login)
    removed = replace(cfg, email_invites=())
    reopened.configure(removed)
    with reopened.db.connect() as c:
        with pytest.raises(SafeError):
            reopened.check_login(c, login)
    reopened.purge_content(before=time.time() + 1)
    reopened.configure(cfg)
    with pytest.raises(SafeError):
        authorize_native_user(
            {**claims, "sub": "replacement", "nonce": "new"}, cfg, time.time(), store=reopened
        )
    with reopened.db.connect() as c:
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 1
        assert c.execute("SELECT global_budget FROM hosted_control").fetchone()[0] == "3"


@pytest.mark.parametrize(
    "value", ["{}", "[null]", '["bad"]', '["user@example.invalid","USER@example.invalid"]']
)
def test_invalid_email_config_fails_closed(hosted_settings, monkeypatch, value):
    monkeypatch.setenv("OIDC_ISSUER", GOOGLE_ISSUER)
    monkeypatch.setenv("OIDC_METADATA_URL", GOOGLE_ISSUER + "/.well-known/openid-configuration")
    monkeypatch.setenv("HOSTED_REVIEWERS_JSON", "[]")
    monkeypatch.setenv("HOSTED_REVIEWER_EMAILS_JSON", value)
    with pytest.raises(ValueError):
        Settings.load()


def test_email_config_requires_google_and_defaults_do_not_change_legacy(
    hosted_settings, monkeypatch
):
    assert hosted_settings.email_invites == ()
    monkeypatch.setenv("HOSTED_REVIEWER_EMAILS_JSON", '["professor@example.invalid"]')
    with pytest.raises(ValueError):
        Settings.load()


@pytest.mark.parametrize(
    "attack", [None, "signature", "issuer", "audience", "nonce", "expiry", "unverified"]
)
async def test_real_authlib_crypto_before_email_binding(invitation, attack):
    cfg, store, claims = invitation
    key = RSAKey.generate_key(2048, parameters={"kid": "email-offline-key"})
    payload = {k: v for k, v in claims.items() if k != "is_logged_in"}
    if attack == "issuer":
        payload["iss"] = "https://attacker.example.invalid"
    if attack == "audience":
        payload["aud"] = "other-client"
    if attack == "nonce":
        payload["nonce"] = "wrong"
    if attack == "expiry":
        payload["exp"] = int(time.time()) - 300
    if attack == "unverified":
        payload["email_verified"] = False
    signed = jwt.encode(
        {"alg": "RS256", "kid": "email-offline-key"},
        payload,
        RSAKey.generate_key(2048) if attack == "signature" else key,
    )
    client = OAuth().register(
        "google",
        client_id=cfg.client_id,
        server_metadata_url=cfg.metadata_url,
        client_kwargs={
            "scope": "openid email",
            "transport": httpx.MockTransport(
                lambda request: (_ for _ in ()).throw(AssertionError("Unexpected offline HTTP"))
            ),
        },
    )
    client.server_metadata.update(
        issuer=cfg.issuer,
        jwks={"keys": [key.as_dict(private=False)]},
        id_token_signing_alg_values_supported=["RS256"],
        _loaded_at=time.time(),
    )

    async def validate():
        verified = await client.parse_id_token({"id_token": signed}, nonce=claims["nonce"])
        return authorize_native_user(
            dict(verified, is_logged_in=True), cfg, time.time(), store=store
        )

    if attack is None:
        login = await validate()
        store.register_login(login)
    else:
        with pytest.raises((JoseError, SafeError)):
            await validate()
        with store.db.connect() as c:
            assert c.execute("SELECT principal FROM hosted_email_invites").fetchone()[0] is None


def test_valid_private_config_normalizes_only_case(hosted_settings, monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER", GOOGLE_ISSUER)
    monkeypatch.setenv("OIDC_METADATA_URL", GOOGLE_ISSUER + "/.well-known/openid-configuration")
    monkeypatch.setenv("HOSTED_REVIEWERS_JSON", "[]")
    monkeypatch.setenv("HOSTED_REVIEWER_EMAILS_JSON", '["Professor@Example.Invalid"]')
    assert Settings.load().email_invites == ("professor@example.invalid",)


def test_unknown_invitation_migration_is_refused_without_reset(invitation):
    _, store, _ = invitation
    with store.db.connect(write=True) as c:
        c.execute("UPDATE metadata SET value='99' WHERE key='hosted_email_invitation_version'")
        original = tuple(c.execute("SELECT * FROM hosted_control").fetchone())
    with pytest.raises(ValueError):
        store.initialize_hosted(evidence_mode="fixture")
    with store.db.connect() as c:
        assert tuple(c.execute("SELECT * FROM hosted_control").fetchone()) == original
        assert (
            c.execute(
                "SELECT value FROM metadata WHERE key='hosted_email_invitation_version'"
            ).fetchone()[0]
            == "99"
        )


def test_email_scope_and_native_dark_startup_config(invitation, monkeypatch):
    import tomllib

    from yemen_customer_service.hosting import launch

    cfg, _, _ = invitation
    # Isolated fixture directory only; no real host volume is touched.
    cfg = replace(cfg, data_dir=cfg.data_dir / "private-runtime")
    cfg.data_dir.mkdir(mode=0o700)
    monkeypatch.setattr(launch, "validate_data_path", lambda path: path)
    monkeypatch.setattr(launch.os, "geteuid", lambda: cfg.data_dir.stat().st_uid)
    runtime = launch.prepare(cfg)
    settings = tomllib.loads((runtime / ".streamlit/secrets.toml").read_text())
    assert settings["auth"]["reviewer"]["client_kwargs"]["scope"] == "openid email"
    assert "expose_tokens" not in settings["auth"]
    assert (runtime / ".streamlit/secrets.toml").stat().st_mode & 0o777 == 0o600
    assert "--theme.base=dark" in __import__("inspect").getsource(launch.worker)


def test_hosted_email_login_uses_existing_ui_and_no_provider(invitation, monkeypatch):
    from pathlib import Path

    import streamlit as st
    from streamlit import config
    from streamlit.testing.v1 import AppTest

    from yemen_customer_service.hosting.controller import HostedController

    cfg, store, claims = invitation
    monkeypatch.setenv("OIDC_ISSUER", cfg.issuer)
    monkeypatch.setenv("OIDC_METADATA_URL", cfg.metadata_url)
    monkeypatch.setenv(
        "HOSTED_REVIEWERS_JSON", json.dumps([{"iss": cfg.issuer, "sub": "legacy-subject"}])
    )
    monkeypatch.setenv("HOSTED_REVIEWER_EMAILS_JSON", '["professor@example.invalid"]')
    # The UI's fixed database filename is copied only inside this synthetic fixture.
    target = cfg.data_dir / "customer_service.sqlite3"
    import sqlite3

    with sqlite3.connect(store.db.path) as source, sqlite3.connect(target) as dest:
        source.backup(dest)

    class NativeUser(dict):
        def to_dict(self):
            return dict(self)

    monkeypatch.setattr(st, "user", NativeUser(claims))

    def forbidden():
        pytest.fail("A login must not construct a paid provider")

    monkeypatch.setattr(HostedController, "_real_provider", forbidden)
    previous = config.get_option("server.address")
    config.set_option("server.address", "127.0.0.1")
    try:
        app = AppTest.from_file(Path("src/yemen_customer_service/ui/hosted_app.py").resolve()).run()
        assert not app.exception and app.chat_input[0].disabled
        principal = app.session_state["_controller"].login.principal
        assert principal == cfg.principal(cfg.issuer, claims["sub"])
        assert "professor@example.invalid" not in str(app)
    finally:
        config.set_option("server.address", previous)


@pytest.mark.parametrize("confirm", [True, False])
def test_enrolled_professor_real_mcp_chat_ticket_and_isolation(invitation, confirm):
    from tests.agent_support import SDKScript, completion
    from yemen_customer_service.hosting.controller import HostedController

    cfg, store, claims = invitation
    cfg = replace(
        cfg,
        paid_enabled=True,
        global_budget=Decimal("3"),
        principal_budget=Decimal(".1"),
        approval_until=time.time() + 600,
    )
    store.configure(cfg)
    store.set_kill(enabled=True)
    login = authorize_native_user(claims, cfg, time.time(), store=store)
    scripts = []
    draft = dict(
        subject="Synthetic headphones",
        message="Synthetic question",
        idempotency_key="email-professor-fixture",
    )
    batches = [
        [
            completion(
                calls=[
                    ("search_products", {"query": "headphones"}),
                    ("get_store_policies", {"topic": "returns"}),
                ]
            ),
            completion("Headphones cost USD 25; returns within 14 days with original receipt."),
        ],
        [completion(calls=[("create_support_ticket", draft)])],
        [completion("The confirmed support ticket was created.")],
    ]

    def factory():
        script = SDKScript(batches.pop(0))
        scripts.append(script)
        return script.provider

    controller = HostedController(store, login, cfg, provider_factory=factory)
    controller.submit("Find headphones and returns", "email-read", "en")
    assert controller.status == "completed"
    controller.submit("Create a support ticket", "email-ticket", "en")
    pending = controller._pending
    assert pending is not None and controller.draft["subject"] == draft["subject"]
    before = Journal(store, pending.token).load(pending.task_id)
    controller.decide(confirm=confirm, revision=controller.revision, locale="en")
    after = Journal(store, pending.token).load(pending.task_id)
    assert after.task_id == before.task_id and after.turns == before.turns + int(confirm)
    assert after.status == ("completed" if confirm else "confirmation_declined")
    with store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == int(confirm)
        assert c.execute(
            "SELECT count(*) FROM audits WHERE tool='create_support_ticket' AND outcome='allow'"
        ).fetchone()[0] == int(confirm)
        assert c.execute("SELECT global_budget FROM hosted_control").fetchone()[0] == "3"
    legacy = authorize_native_user({**claims, "sub": "legacy-subject"}, cfg, time.time())
    store.register_login(legacy)
    other = store.provision(legacy, tasks_per_hour=5)
    assert Journal(store, other).memory() == []
    store.revoke(login)
    with pytest.raises(SafeError):
        authorize_native_user(claims, cfg, time.time(), store=store)
    assert all(s.provider.mode == "fixture" for s in scripts)
