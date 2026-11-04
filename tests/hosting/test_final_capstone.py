"""Final regressions: scripted SDK providers, actual hosted controller and genuine MCP.

No live Google/OpenAI/Railway calls; every database and identity is synthetic.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest
import streamlit as st
from streamlit import config
from streamlit.testing.v1 import AppTest

from tests.agent_support import SDKScript, completion
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.hosting.controller import HostedController
from yemen_customer_service.ui.presentation import assistant_markdown

DRAFT = {
    "subject": "Headphones stopped working",
    "message": "My synthetic headphones stopped working.",
    "order_id": None,
    "idempotency_key": "headphones-support",
}


@pytest.fixture
def final_ui(hosted_store, enabled, login, claims, monkeypatch):
    class User(dict):
        def to_dict(self):
            return dict(self)

    previous = config.get_option("server.address")
    config.set_option("server.address", "127.0.0.1")
    monkeypatch.setattr(st, "user", User(claims))

    def build(batches, settings=enabled):
        scripts = []

        def factory():
            script = SDKScript(batches.pop(0))
            scripts.append(script)
            return script.provider

        controller = HostedController(hosted_store, login, settings, provider_factory=factory)
        app = AppTest.from_file(
            Path("src/yemen_customer_service/ui/hosted_app.py").resolve(), default_timeout=20
        )
        app.session_state["_controller"] = controller
        app.session_state["_submission_id"] = "final-hosted-fixture"
        return app.run(), controller, scripts

    yield build
    config.set_option("server.address", previous)


def visible(app):
    return "\n".join(
        str(e.value)
        for kind in ("text", "markdown", "info", "error", "caption")
        for e in getattr(app, kind)
    )


@pytest.mark.parametrize("locale", ["en", "ar"])
@pytest.mark.parametrize("confirm", [True, False])
def test_hosted_actual_form_edit_confirm_cancel_and_replay(final_ui, hosted_store, locale, confirm):
    def final(payload):
        result = json.loads(payload["messages"][-1]["content"])
        return completion("**Support ticket created:** " + result["data"]["ticket_id"])

    batches = [[completion(calls=[("create_support_ticket", DRAFT)])], [final]]
    app, controller, scripts = final_ui(batches)
    if locale == "ar":
        app.radio[0].set_value("العربية").run()
    request = (
        "Create a support ticket for headphones that stopped working."
        if locale == "en"
        else "أريد فتح تذكرة دعم لأن السماعات توقفت عن العمل."
    )
    app.chat_input[0].set_value(request).run()
    assert not app.exception and controller.draft is not None
    pending = controller._pending
    journal = Journal(hosted_store, pending.token)
    before = journal.load(pending.task_id)
    assert before.status == "awaiting_confirmation"
    assert app.chat_input[0].disabled
    assert app.text_input(key="draft_subject").value == DRAFT["subject"]
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
    # Conversational yes never invokes the trusted Confirm route.
    controller.submit("yes", "conversational-yes", locale)
    assert len(scripts) == 1 and controller._pending == pending
    app.text_area(key="draft_message").set_value("Edited synthetic issue").run()
    edited = journal.load(pending.task_id)
    assert (edited.turns, edited.held_usd, edited.active_seconds, edited.limits) == (
        before.turns,
        before.held_usd,
        before.active_seconds,
        before.limits,
    )
    old_revision = controller.revision - 1
    controller.decide(confirm=True, revision=old_revision, locale=locale)
    assert len(scripts) == 1  # stale revision rejected
    app.button(key="confirm_ticket" if confirm else "cancel_ticket").click().run()
    assert not app.exception
    after = journal.load(pending.task_id)
    assert after.task_id == before.task_id and after.limits == before.limits
    assert after.status == ("completed" if confirm else "confirmation_declined")
    assert after.turns == before.turns + int(confirm)
    assert after.active_seconds >= before.active_seconds and after.held_usd >= before.held_usd
    controller.decide(confirm=True, revision=controller.revision - 1, locale=locale)
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == int(confirm)
        rows = c.execute(
            "SELECT tool,outcome FROM audits WHERE tool='create_support_ticket'"
        ).fetchall()
        assert [tuple(r) for r in rows] == ([("create_support_ticket", "allow")] if confirm else [])
        if confirm:
            assert (
                c.execute("SELECT message FROM tickets").fetchone()[0] == "Edited synthetic issue"
            )
    # Prompt and safe discovered tool distinguish proposing from actually writing.
    payload = scripts[0].requests[0]
    assert "Do not substitute a prose proposal" in payload["messages"][0]["content"]
    schema = next(t for t in payload["tools"] if t["function"]["name"] == "create_support_ticket")
    assert "pauses BEFORE" in schema["function"]["description"]
    assert "confirmation_reference" not in json.dumps(schema)


def test_text_only_model_proposal_is_not_consent_or_a_persisted_ticket(final_ui, hosted_store):
    app, controller, scripts = final_ui(
        [
            [completion("I can propose a support ticket. Would you like to confirm?")],
            [completion(calls=[("create_support_ticket", DRAFT)])],
        ]
    )
    app.chat_input[0].set_value(
        "I want to open a support ticket because my headphones stopped working."
    ).run()
    assert controller.status == "completed" and controller.draft is None
    # Models can still ignore instructions: preserve this limitation as a test.
    app.chat_input[0].set_value("yes").run()
    assert controller.draft is not None and len(scripts) == 2
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0


@pytest.mark.parametrize("locale", ["en", "ar"])
def test_task_rate_limit_is_helpful_and_preserves_limits(
    final_ui, enabled, hosted_store, login, locale
):
    cfg = replace(enabled, tasks_per_hour=1)
    hosted_store.provision(login, tasks_per_hour=1)
    app, controller, scripts = final_ui([], settings=cfg)
    if locale == "ar":
        app.radio[0].set_value("العربية").run()
    app.chat_input[0].set_value("Create a support ticket for headphones").run()
    assert controller.status == "rate_limited" and not scripts
    assert ("Please wait" if locale == "en" else "يرجى الانتظار") in visible(app)
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 1
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


@pytest.mark.parametrize("locale", ["en", "ar"])
def test_safe_assistant_markdown_preserves_basic_formatting_and_redaction(
    final_ui, monkeypatch, locale
):
    monkeypatch.setenv("LLM_API_KEY", "synthetic-sensitive-value-for-redaction")
    answer = (
        "**Headphones / سماعات**\n\n- USD $25\n- إرجاع خلال 14 يومًا\n\n"
        '<img src="https://example.invalid/x"> ![remote](https://example.invalid/x) '
        "synthetic-sensitive-value-for-redaction"
    )
    app, controller, _ = final_ui([[completion(answer)]])
    if locale == "ar":
        app.radio[0].set_value("العربية").run()
    app.chat_input[0].set_value("Show headphones").run()
    assert not app.exception
    markdown = app.markdown[-1]
    assert "**Headphones / سماعات**" in markdown.value and "- USD \\$25" in markdown.value
    assert "example.invalid" not in markdown.value
    assert "synthetic-sensitive" not in markdown.value
    assert not markdown.proto.allow_html
    assert "&lt;img" in markdown.value and r"\[redacted\]" in markdown.value
    assert any(
        "direction:" + ("rtl" if locale == "ar" else "ltr") in e.proto.body for e in app.get("html")
    )
    assert controller.status == "completed"


@pytest.mark.parametrize(
    "payload",
    [
        r"\![x](https://example.invalid)",
        "![x][r]\n\n[r]: https://example.invalid",
        '<script>alert("x")</script>',
    ],
)
def test_markdown_external_media_and_html_cannot_become_active(payload):
    result = assistant_markdown(payload, "en")
    assert "https://" not in result and "<script>" not in result
    if "[" in payload:
        assert "\\[" in result


@pytest.mark.parametrize("change", [{"order_id": ""}, {"idempotency_key": "invalid key!"}])
def test_malformed_model_ticket_arguments_fail_closed(final_ui, hosted_store, change):
    app, controller, scripts = final_ui(
        [[completion(calls=[("create_support_ticket", {**DRAFT, **change})])]]
    )
    app.chat_input[0].set_value(
        "Create a support ticket for headphones that stopped working."
    ).run()
    assert not app.exception and controller.status == "invalid_tool_arguments"
    assert controller.draft is None and len(scripts[0].requests) == 1
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
        assert (
            c.execute("SELECT count(*) FROM audits WHERE tool='create_support_ticket'").fetchone()[
                0
            ]
            == 0
        )


@pytest.mark.parametrize("locale", ["en", "ar"])
def test_unknown_product_has_safe_customer_message(final_ui, locale):
    app, controller, scripts = final_ui(
        [[completion(calls=[("get_product_details", {"product_id": "P-999"})])]]
    )
    if locale == "ar":
        app.radio[0].set_value("العربية").run()
    app.chat_input[0].set_value("P-999?").run()
    assert controller.status == "not_found" and len(scripts[0].requests) == 1
    assert ("could not find" if locale == "en" else "لم نعثر") in visible(app)
    assert "USD" not in visible(app) and "NOT_FOUND" not in visible(app)
