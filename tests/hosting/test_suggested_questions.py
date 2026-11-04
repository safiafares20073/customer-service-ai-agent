"""Suggested inputs use real hosted submit/MCP with explicit SDK provider fixtures."""

from contextlib import nullcontext
from pathlib import Path

import pytest
import streamlit as st
from streamlit import config
from streamlit.testing.v1 import AppTest

from tests.agent_support import SDKScript, completion
from yemen_customer_service.hosting.controller import HostedController
from yemen_customer_service.ui.chat import _submit_suggestion

QUESTIONS = {
    "en": (
        (
            "products",
            "Products & prices",
            "What products are currently in stock? Include their prices.",
        ),
        ("returns", "Return policy", "What is your return policy?"),
        (
            "ticket",
            "Create support ticket",
            "Create a support ticket for headphones that stopped working.",
        ),
    ),
    "ar": (
        ("products", "المنتجات والأسعار", "ما المنتجات المتوفرة حاليًا وما أسعارها؟"),
        ("returns", "سياسة الإرجاع", "ما سياسة الإرجاع؟"),
        ("ticket", "إنشاء تذكرة دعم", "أريد إنشاء تذكرة دعم لأن السماعات توقفت عن العمل."),
    ),
}


def buttons(app):
    return [b for b in app.button if b.key and b.key.startswith("suggestion_")]


@pytest.fixture
def suggested_app(hosted_store, enabled, login, claims, monkeypatch):
    class NativeUser(dict):
        def to_dict(self):
            return dict(self)

    monkeypatch.setattr(st, "user", NativeUser(claims))
    previous = config.get_option("server.address")
    config.set_option("server.address", "127.0.0.1")

    def create(kind):
        scripts = []
        if kind == "products":
            actions = [
                completion(
                    calls=[
                        ("get_product_details", {"product_id": "P-100"}),
                        ("get_product_details", {"product_id": "P-200"}),
                        ("get_product_details", {"product_id": "P-300"}),
                    ]
                ),
                completion(
                    "Headphones USD 25 and Keyboard USD 40 are in stock; Mouse is out of stock."
                ),
            ]
        elif kind == "returns":
            actions = [
                completion(calls=[("get_store_policies", {"topic": "returns"})]),
                completion("Returns within 14 days with the original receipt."),
            ]
        else:
            actions = [
                completion(
                    calls=[
                        (
                            "create_support_ticket",
                            {
                                "subject": "Headphones stopped working",
                                "message": "Synthetic headphones stopped working.",
                                "idempotency_key": "suggested-ticket",
                            },
                        )
                    ]
                )
            ]
        batches = (
            [actions, [completion("The confirmed support ticket was created.")]]
            if kind == "ticket"
            else [actions, actions]
        )

        def factory():
            script = SDKScript(batches.pop(0))
            scripts.append(script)
            return script.provider

        controller = HostedController(hosted_store, login, enabled, provider_factory=factory)
        calls = []
        original = controller.submit

        def observed(question, submission, locale):
            calls.append((question, submission, locale))
            return original(question, submission, locale)

        controller.submit = observed
        app = AppTest.from_file(
            Path("src/yemen_customer_service/ui/hosted_app.py").resolve(), default_timeout=20
        )
        app.session_state["_controller"] = controller
        app.session_state["_submission_id"] = "suggested-initial-id"
        return app.run(), controller, scripts, calls

    yield create
    config.set_option("server.address", previous)


@pytest.mark.parametrize("kind", ["products", "returns", "ticket"])
@pytest.mark.parametrize("locale", ["en", "ar"])
def test_localized_button_submits_exact_question_once_through_real_hosted_path(
    suggested_app, hosted_store, kind, locale
):
    app, controller, scripts, calls = suggested_app(kind)
    if locale == "ar":
        app.radio[0].set_value("العربية").run()
    assert not app.exception
    assert [b.label for b in buttons(app)] == [entry[1] for entry in QUESTIONS[locale]]
    question = next(entry[2] for entry in QUESTIONS[locale] if entry[0] == kind)
    with hosted_store.db.connect() as c:
        control = tuple(c.execute("SELECT * FROM hosted_control").fetchone())
    app.button(key="suggestion_" + kind).click().run()
    assert not app.exception
    assert calls == [(question, "suggested-initial-id", locale)]
    assert controller.messages[0] == ("user", question)
    assert app.session_state["_submission_id"] != "suggested-initial-id"
    assert len(buttons(app)) == 3 and scripts
    assert all(b.disabled for b in buttons(app)) == (kind == "ticket")
    app.run()
    app.run()
    assert len(calls) == 1 and len(scripts) == 1
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 1
        assert tuple(c.execute("SELECT * FROM hosted_control").fetchone()) == control
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
        assert (
            c.execute(
                "SELECT count(*) FROM hosted_calls WHERE provider!=?", ("fixture",)
            ).fetchone()[0]
            == 0
        )
    if kind == "ticket":
        pending = controller._pending
        assert pending and app.chat_input[0].disabled
        # Suggested ticket is only a proposal, never a consent shortcut.
        app.button(key="confirm_ticket").click().run()
        assert not app.exception and len(scripts) == 2
        assert len(buttons(app)) == 3 and all(not b.disabled for b in buttons(app))
        with hosted_store.db.connect() as c:
            assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
            assert (
                c.execute(
                    "SELECT count(*) FROM audits "
                    "WHERE tool='create_support_ticket' AND outcome='allow'"
                ).fetchone()[0]
                == 1
            )


@pytest.mark.parametrize("locale", ["en", "ar"])
def test_suggestions_stay_visible_and_can_be_reused_after_response(
    suggested_app, hosted_store, locale
):
    app, controller, scripts, calls = suggested_app("products")
    if locale == "ar":
        app.radio[0].set_value("العربية").run()
    app.button(key="suggestion_products").click().run()
    assert not app.exception and len(calls) == 1
    assert len(buttons(app)) == 3 and all(not b.disabled for b in buttons(app))
    # A deliberate later click is a separate task, with a fresh submission ID.
    app.button(key="suggestion_products").click().run()
    assert not app.exception and len(calls) == 2 and len(scripts) == 2
    assert calls[0][0] == calls[1][0] == QUESTIONS[locale][0][2]
    assert calls[0][1] != calls[1][1]
    assert len(buttons(app)) == 3 and all(not b.disabled for b in buttons(app))
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 2


def test_multiple_queued_buttons_produce_only_one_submission(suggested_app, hosted_store):
    app, _, scripts, calls = suggested_app("products")
    app.button(key="suggestion_products").click()
    app.button(key="suggestion_returns").click()
    app.run()
    app.run()
    assert not app.exception and len(calls) == len(scripts) == 1
    assert calls[0][0] == QUESTIONS["en"][0][2]
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 1


@pytest.mark.parametrize("gate", ["budget", "kill", "paid"])
def test_unavailable_hosted_chat_disables_suggestions_without_spend(
    suggested_app, hosted_store, gate
):
    app, _, scripts, calls = suggested_app("returns")
    with hosted_store.db.connect(write=True) as c:
        if gate == "budget":
            c.execute("UPDATE hosted_control SET global_budget='0',principal_budget='0'")
        if gate == "kill":
            c.execute("UPDATE hosted_control SET kill=1")
        if gate == "paid":
            c.execute("UPDATE hosted_control SET paid=0")
        before = tuple(c.execute("SELECT * FROM hosted_control").fetchone())
    app.run()
    assert len(buttons(app)) == 3 and all(b.disabled for b in buttons(app))
    assert not calls and not scripts
    with hosted_store.db.connect() as c:
        assert tuple(c.execute("SELECT * FROM hosted_control").fetchone()) == before
        assert c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 0


def test_expired_login_does_not_offer_suggestions(suggested_app, hosted_store, login):
    app, _, scripts, calls = suggested_app("returns")
    with hosted_store.db.connect(write=True) as c:
        c.execute("UPDATE hosted_logins SET expires=0 WHERE fingerprint=?", (login.fingerprint,))
    app.run()
    assert not buttons(app) and not calls and not scripts


class State(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class DecliningController:
    busy = False
    draft = None
    messages = ()

    def __init__(self):
        self.calls = []

    def submit(self, *args):
        self.calls.append(args)


def test_claim_prevents_another_click_even_if_backend_adds_no_user_message(monkeypatch):
    state = State(_submission_id="existing-id")
    monkeypatch.setattr(st, "session_state", state)
    monkeypatch.setattr(st, "spinner", lambda _: nullcontext())
    controller = DecliningController()
    assert _submit_suggestion(controller, "First", "en", enabled=True)
    rotated = state["_submission_id"]
    assert not _submit_suggestion(controller, "Other button", "en", enabled=True)
    assert controller.calls == [("First", "existing-id", "en")]
    assert rotated != "existing-id" and state["_submission_id"] == rotated


@pytest.mark.parametrize("condition", ["disabled", "busy", "draft"])
def test_suggestion_guard_rechecks_disabled_busy_and_pending(monkeypatch, condition):
    state = State(_submission_id="existing-id")
    monkeypatch.setattr(st, "session_state", state)
    controller = DecliningController()
    if condition == "busy":
        controller.busy = True
    if condition == "draft":
        controller.draft = {"subject": "pending"}
    assert not _submit_suggestion(controller, "Ignored", "ar", enabled=condition != "disabled")
    assert not controller.calls and state["_submission_id"] == "existing-id"
    assert not state.get("_suggestion_used", False)
