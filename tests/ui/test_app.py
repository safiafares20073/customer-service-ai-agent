from streamlit import config


def visible_text(app):
    return "\n".join(
        str(e.value)
        for kind in (
            "title",
            "caption",
            "info",
            "warning",
            "error",
            "text",
            "subheader",
        )
        for e in getattr(app, kind)
    )


def test_english_chat_real_agent_mcp_no_internal_metrics(app):
    assert not app.exception
    assert "Synthetic store" in visible_text(app)
    assert "Scripted demonstration" in visible_text(app)
    app.chat_input[0].set_value("Find headphones under $30 and explain returns").run()
    assert not app.exception
    text = visible_text(app)
    assert "Example Headphones" in text and "14 days" in text
    assert "Request completed" in text
    assert all(
        value not in text
        for value in (
            "cost_usd",
            "max_turns",
            "0.05",
            "access_reference",
            "confirmation_reference",
            "input_tokens",
            "output_tokens",
            "fixture-not-a-real-key",
        )
    )
    controller = app.session_state["_controller"]
    with controller.store.db.connect() as conn:
        calls = [row[0] for row in conn.execute("SELECT tool FROM audits WHERE outcome='allow'")]
        assert calls == ["search_products", "get_store_policies", "agent"]


def test_arabic_text_and_rtl_controls(app):
    app.radio[0].set_value("العربية").run()
    assert not app.exception and "كيف يمكننا مساعدتك" in app.title[0].value
    app.chat_input[0].set_value("أريد سماعات وسياسة الإرجاع").run()
    assert not app.exception
    assert "الإرجاع خلال 14" in visible_text(app)
    html = app.get("html")
    assert any("direction:rtl" in e.proto.body for e in html)
    app.radio[0].set_value("English").run()
    assert any("direction:ltr" in e.proto.body for e in app.get("html"))


def test_exact_ticket_draft_edit_confirm_and_replay(app):
    app.chat_input[0].set_value("Create a ticket for damaged headphones").run()
    assert not app.exception
    controller = app.session_state["_controller"]
    pending = controller._pending
    before = controller.store
    from yemen_customer_service.agent.state import Journal

    journal = Journal(before, pending.token)
    state = journal.load(pending.task_id)
    assert state.status == "awaiting_confirmation"
    assert app.chat_input[0].disabled
    assert app.text_input(key="draft_subject").value == pending.draft.subject
    with before.db.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
    app.text_area(key="draft_message").set_value("Edited synthetic earcup issue").run()
    assert not app.exception
    current = journal.load(pending.task_id)
    assert current.queue[0]["arguments"]["message"] == "Edited synthetic earcup issue"
    assert (current.turns, current.held_usd, current.active_seconds, current.limits) == (
        state.turns,
        state.held_usd,
        state.active_seconds,
        state.limits,
    )
    revision = controller.revision
    app.button(key="confirm_ticket").click().run()
    assert not app.exception
    after = journal.load(pending.task_id)
    assert after.status == "completed" and after.turns == state.turns + 1
    assert after.active_seconds >= state.active_seconds and after.held_usd > state.held_usd
    assert "Support ticket" in visible_text(app) and "was created" in visible_text(app)
    assert not app.button
    controller.decide(confirm=True, revision=revision, locale="en")
    with before.db.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
        assert (
            conn.execute("SELECT message FROM tickets").fetchone()[0]
            == "Edited synthetic earcup issue"
        )


def test_cancel_never_creates_ticket_or_adds_provider_request(app):
    app.chat_input[0].set_value("Open a support ticket").run()
    controller = app.session_state["_controller"]
    with controller.store.db.connect() as conn:
        requests = conn.execute("SELECT count(*) FROM cost_records").fetchone()[0]
    app.button(key="cancel_ticket").click().run()
    assert not app.exception and "Ticket request cancelled" in visible_text(app)
    assert not app.chat_input[0].disabled
    with controller.store.db.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM cost_records").fetchone()[0] == requests


def test_cross_customer_order_denial_is_customer_friendly(app):
    app.chat_input[0].set_value("Where is DEMO-200?").run()
    assert not app.exception
    text = visible_text(app)
    assert "could not verify access" in text
    assert "processing" not in text and "ACCESS_DENIED" not in text
    assert "Traceback" not in text and "Request completed" not in text


def test_non_loopback_configuration_refuses_demo_identity(app):
    config.set_option("server.address", "0.0.0.0")
    app.run()
    assert not app.exception and "unavailable" in visible_text(app)
    assert not app.chat_input


def test_invalid_edit_disables_confirmation(app):
    app.chat_input[0].set_value("Create a support ticket").run()
    app.text_input(key="draft_subject").set_value("").run()
    assert not app.exception and app.button(key="confirm_ticket").disabled
    app.button(key="cancel_ticket").click().run()
    assert not app.exception


def test_script_html_is_plain_customer_text(app):
    app.chat_input[0].set_value('<script>alert("synthetic")</script>').run()
    assert not app.exception
    assert any('<script>alert("synthetic")</script>' in e.value for e in app.text)
    assert all("alert(" not in e.proto.body for e in app.get("html"))


def test_raw_backend_error_is_not_rendered(ui_environment, monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    from yemen_customer_service.ui import service

    def broken():
        raise RuntimeError("do-not-render-private-backend-detail")

    monkeypatch.setattr(service, "make_provider", broken)
    app = AppTest.from_file(
        Path("src/yemen_customer_service/ui/app.py").resolve(), default_timeout=20
    ).run()
    app.chat_input[0].set_value("Show headphones").run()
    assert not app.exception
    assert "could not complete" in visible_text(app)
    assert "do-not-render" not in visible_text(app) and "Traceback" not in visible_text(app)


def test_arabic_ticket_confirm_and_cancel_controls(app):
    app.radio[0].set_value("العربية").run()
    app.chat_input[0].set_value("أريد إنشاء تذكرة لمنتج تالف").run()
    assert not app.exception
    assert app.button(key="confirm_ticket").label == "تأكيد التذكرة"
    assert app.button(key="cancel_ticket").label == "إلغاء"
    app.button(key="cancel_ticket").click().run()
    assert "تم إلغاء" in visible_text(app)
