import asyncio

import pytest

from yemen_customer_service.agent.state import Journal
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError
from yemen_customer_service.ui.service import Controller


def test_duplicate_submit_and_busy_state_do_not_start_new_tasks(database):
    controller = Controller(database.path, "demo-a", demo_enabled=True)
    controller.submit("Show headphones", "same-event", "en")
    with database.connect() as conn:
        before = conn.execute("SELECT count(*) FROM cost_records").fetchone()[0]
        sessions = conn.execute("SELECT count(*) FROM sessions").fetchone()[0]
    controller.submit("Show headphones", "same-event", "en")
    controller._lock.acquire()
    try:
        controller.submit("Show headphones again", "different-event", "en")
    finally:
        controller._lock.release()
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM cost_records").fetchone()[0] == before
        assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == sessions


def test_edit_revokes_old_wire_confirmation_and_stale_ui_approval(database):
    controller = Controller(database.path, "demo-a", demo_enabled=True)
    controller.submit("Open a synthetic ticket", "event", "en")
    original = controller._pending
    journal = Journal(controller.store, original.token)
    previous = journal.load(original.task_id)
    old_reference = controller.store.register_confirmation(
        original.token, original.draft, confirmed=True
    )
    old_revision = controller.revision
    assert controller.edit("Revised subject", "Edited synthetic message", "", "en")
    current = journal.load(original.task_id)
    assert (current.turns, current.held_usd, current.active_seconds, current.limits) == (
        previous.turns,
        previous.held_usd,
        previous.active_seconds,
        previous.limits,
    )
    assert current.queue[0]["arguments"]["idempotency_key"] == original.draft.idempotency_key

    async def try_old_grant():
        async with connect(
            database.path, controller.store, original.token, enable_demo_auth=True
        ) as client:
            result = await client._session.call_tool(
                "create_support_ticket",
                {
                    **original.draft.model_dump(),
                    "confirmation_reference": old_reference,
                },
            )
            assert (
                result.isError
                and result.structuredContent["error"]["code"] == "CONFIRMATION_REQUIRED"
            )

    asyncio.run(try_old_grant())
    controller.decide(confirm=True, revision=old_revision, locale="en")
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
    controller.decide(confirm=True, revision=controller.revision, locale="en")
    assert controller.status == "completed"
    replay_revision = controller.revision
    controller.decide(confirm=True, revision=replay_revision, locale="en")
    with database.connect() as conn:
        tickets = conn.execute("SELECT subject, message FROM tickets").fetchall()
        assert [tuple(row) for row in tickets] == [("Revised subject", "Edited synthetic message")]
        assert conn.execute("SELECT count(*) FROM cost_records").fetchone()[0] == 2


def test_cancel_does_not_require_available_provider(database):
    controller = Controller(database.path, "demo-a", demo_enabled=True)
    controller.submit("Create a ticket", "event", "en")
    pending = controller._pending
    before = Journal(controller.store, pending.token).load(pending.task_id)

    def unavailable():
        pytest.fail("Cancellation must not create a provider")

    controller._provider_factory = unavailable
    controller.decide(confirm=False, revision=controller.revision, locale="en")
    after = Journal(controller.store, pending.token).load(pending.task_id)
    assert after.status == "confirmation_declined"
    assert (before.turns, before.held_usd, before.active_seconds) == (
        after.turns,
        after.held_usd,
        after.active_seconds,
    )


def test_other_browser_session_cannot_adopt_pending_task(database):
    first = Controller(database.path, "demo-a", demo_enabled=True)
    second = Controller(database.path, "demo-a", demo_enabled=True)
    first.submit("Create a ticket", "first", "en")
    second.decide(confirm=True, revision=first.revision, locale="en")
    second.submit("Create a different ticket", "second", "en")
    assert first._pending.task_id != second._pending.task_id
    with pytest.raises(SafeError):
        Journal(second.store, second._pending.token).load(first._pending.task_id)
    assert first.messages != second.messages
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


@pytest.mark.parametrize("enabled", [False, True])
def test_production_or_unapproved_fixture_auth_refused(database, monkeypatch, enabled):
    monkeypatch.setenv("APP_ENV", "production" if enabled else "development")
    with pytest.raises(SafeError):
        Controller(database.path, "demo-a", demo_enabled=enabled)


def test_failed_draft_save_cannot_leave_confirmation_enabled(database, monkeypatch):
    import sqlite3

    controller = Controller(database.path, "demo-a", demo_enabled=True)
    controller.submit("Create a ticket", "event", "en")

    def failed(*args):
        raise sqlite3.OperationalError("synthetic database unavailable")

    monkeypatch.setattr(Journal, "edit_ticket", failed)
    assert controller.edit("Changed", "Changed message", "", "en") is False
    assert controller.error
    controller.decide(confirm=True, revision=controller.revision, locale="en")
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM cost_records").fetchone()[0] == 1


def test_customer_product_budget_question_is_preserved(database):
    controller = Controller(database.path, "demo-a", demo_enabled=True)
    question = "My shopping budget is $30. Please show headphones."
    controller.submit(question, "event", "en")
    assert controller.messages[0] == ("user", question)
