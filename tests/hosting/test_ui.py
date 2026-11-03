from pathlib import Path

import pytest
import streamlit as st
from streamlit import config
from streamlit.testing.v1 import AppTest

from tests.agent_support import SDKScript, completion
from yemen_customer_service.hosting.controller import HostedController


class NativeUserFixture(dict):
    def to_dict(self):
        return dict(self)


@pytest.fixture
def hosted_ui(hosted_settings, monkeypatch):
    previous = config.get_option("server.address")
    config.set_option("server.address", "127.0.0.1")
    monkeypatch.setattr(st, "user", NativeUserFixture(is_logged_in=False))
    yield lambda: AppTest.from_file(
        Path("src/yemen_customer_service/ui/hosted_app.py").resolve(), default_timeout=20
    )
    config.set_option("server.address", previous)


def text(app):
    return "\n".join(
        str(e.value)
        for kind in ["title", "caption", "info", "warning", "error", "text"]
        for e in getattr(app, kind)
    )


def test_public_login_page_english_arabic_and_no_provider(hosted_ui, monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("Provider before login")

    monkeypatch.setattr(HostedController, "_real_provider", forbidden)
    app = hosted_ui().run()
    assert not app.exception
    assert "invited reviewers only" in text(app) and not app.chat_input
    assert app.button(key="hosted_login")
    app.radio[0].set_value("العربية").run()
    assert "للمراجعين المدعوين" in text(app)
    assert any("direction:rtl" in e.proto.body for e in app.get("html"))


def test_uninvited_and_expired_users_never_get_chat(hosted_ui, claims, monkeypatch):
    for changes in [{"sub": "uninvited"}, {"exp": 0}]:
        monkeypatch.setattr(st, "user", NativeUserFixture({**claims, **changes}))
        app = hosted_ui().run()
        assert not app.exception and not app.chat_input
        assert "Access is not permitted" in text(app)


def test_invited_paid_disabled_and_logout_replay(
    hosted_ui, hosted_store, login, claims, monkeypatch
):
    monkeypatch.setattr(st, "user", NativeUserFixture(claims))
    calls = []
    monkeypatch.setattr(st, "logout", lambda: calls.append("logout"))
    app = hosted_ui().run()
    assert not app.exception
    assert app.chat_input[0].disabled and "temporarily unavailable" in text(app)
    controller = app.session_state["_controller"]
    app.button(key="hosted_logout").click().run()
    assert calls == ["logout"]
    with hosted_store.db.connect() as c:
        assert (
            c.execute(
                "SELECT revoked FROM hosted_logins WHERE fingerprint=?",
                (controller.login.fingerprint,),
            ).fetchone()[0]
            == 1
        )
    replay = hosted_ui().run()
    assert not replay.chat_input


def test_hosted_chat_uses_real_agent_mcp_fixture_and_no_internal_metrics(
    hosted_ui, hosted_store, enabled, login, claims, monkeypatch
):
    monkeypatch.setattr(st, "user", NativeUserFixture(claims))
    scripts = []

    def factory():
        script = SDKScript(
            [
                completion(calls=[("list_products", {})]),
                completion("Example Headphones cost USD 25.00."),
            ]
        )
        scripts.append(script)
        return script.provider

    controller = HostedController(hosted_store, login, enabled, provider_factory=factory)
    app = hosted_ui()
    app.session_state["_controller"] = controller
    app.session_state["_submission_id"] = "hosted-ui-fixture"
    app.run()
    assert not app.exception
    app.chat_input[0].set_value("List headphones").run()
    assert not app.exception
    assert "Example Headphones" in text(app)
    assert all(
        s not in text(app)
        for s in ["cost_usd", "input_tokens", "0.05", "session_hash", "fixture-not-a-real-key"]
    )
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 2
        assert (
            c.execute(
                "SELECT count(*) FROM audits WHERE tool='list_products' AND outcome='allow'"
            ).fetchone()[0]
            == 1
        )
