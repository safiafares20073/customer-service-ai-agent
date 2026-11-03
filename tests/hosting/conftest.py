"""Synthetic identities/JWTs/providers only. No real reviewer accounts or IdP calls."""

import time
from dataclasses import replace
from decimal import Decimal

import pytest

from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.settings import Settings
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database


@pytest.fixture
def hosted_settings(monkeypatch, tmp_path):
    values = {
        "APP_ENV": "production",
        "ENABLE_DEMO_AUTH": "false",
        "UI_PROVIDER": "openai",
        "HOSTED_DATA_DIR": str(tmp_path),
        "HOSTED_ORIGIN": "https://demo.example.invalid",
        "OIDC_ISSUER": "https://oidc.example.invalid",
        "OIDC_METADATA_URL": "https://oidc.example.invalid/.well-known/openid-configuration",
        "OIDC_CLIENT_ID": "fixture-client",
        "OIDC_CLIENT_SECRET": "fixture-client-secret",
        "HOSTED_COOKIE_SECRET": "fixture-cookie-" + "x" * 50,
        "HOSTED_PRINCIPAL_SECRET": "fixture-principal-" + "y" * 50,
        "HOSTED_REVIEWERS_JSON": '[{"iss":"https://oidc.example.invalid","sub":"fixture-A"},'
        '{"iss":"https://oidc.example.invalid","sub":"fixture-B"}]',
        "HOSTED_PAID_ENABLED": "false",
        "HOSTED_GLOBAL_BUDGET_USD": "0",
        "HOSTED_PRINCIPAL_BUDGET_USD": "0",
        "HOSTED_APPROVAL_UNTIL": "0",
    }
    for k, v in values.items():
        monkeypatch.setenv(k, v)
    return Settings.load()


@pytest.fixture
def claims(hosted_settings):
    now = int(time.time())
    return {
        "is_logged_in": True,
        "iss": hosted_settings.issuer,
        "sub": "fixture-A",
        "aud": hosted_settings.client_id,
        "iat": now - 1,
        "exp": now + 3600,
        "nonce": "fixture-nonce-A",
    }


@pytest.fixture
def hosted_store(hosted_settings):
    store = HostedStore(Database(hosted_settings.data_dir / "customer_service.sqlite3"))
    store.initialize_hosted(evidence_mode="fixture")
    store.configure(hosted_settings)
    return store


@pytest.fixture
def login(hosted_store, hosted_settings, claims):
    identity = authorize_native_user(claims, hosted_settings, time.time())
    hosted_store.register_login(identity)
    return identity


@pytest.fixture
def enabled(hosted_store, hosted_settings):
    settings = replace(
        hosted_settings,
        paid_enabled=True,
        approval_until=time.time() + 3600,
        global_budget=Decimal("1"),
        principal_budget=Decimal("0.10"),
    )
    hosted_store.configure(settings)
    hosted_store.set_kill(enabled=True)
    return settings
