import json
import time
from dataclasses import replace

import pytest

from tests.agent_support import SDKScript, completion
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.controller import HostedController
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError, TicketDraft


def test_no_development_data_and_cannot_promote_fixture_db(hosted_store):
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM products").fetchone()[0] == 3
        for table in ["customers", "orders", "tickets", "sessions", "memory"]:
            assert c.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
        assert c.execute("PRAGMA user_version").fetchone()[0] == 2
    with pytest.raises(ValueError):
        hosted_store.initialize_hosted()  # fixture != openai


def test_existing_development_database_refused(tmp_path):
    db = Database(tmp_path / "dev.sqlite3")
    db.initialize(seed_demo=True)
    with pytest.raises(ValueError):
        HostedStore(db).initialize_hosted()


def test_development_auth_rejected_even_with_existing_customer(hosted_store, login):
    with pytest.raises(SafeError):
        Store(hosted_store.db).provision_demo_session(
            login.principal, enable_demo_auth=True, app_env="development"
        )


@pytest.mark.parametrize("ending", ["logout", "expiry", "invitation"])
async def test_production_mcp_ownership_and_revocation(
    hosted_store, hosted_settings, claims, login, ending
):
    other = authorize_native_user(
        {**claims, "sub": "fixture-B", "nonce": "nonce-B"}, hosted_settings, time.time()
    )
    hosted_store.register_login(other)
    with hosted_store.db.connect(write=True) as c:
        c.execute("INSERT INTO orders VALUES ('H-A',?,'shipped',NULL)", (login.principal,))
        c.execute("INSERT INTO orders VALUES ('H-B',?,'processing',NULL)", (other.principal,))
    token = hosted_store.provision(login, tasks_per_hour=5)
    async with connect(
        hosted_store.db.path, hosted_store, token, enable_hosted_auth=True
    ) as client:
        assert len(await client.tools_for_model()) == 7
        assert (await client.invoke("verify_order_access", {"order_id": "H-B"}))["error"][
            "code"
        ] == "ACCESS_DENIED"
        assert (await client.invoke("verify_order_access", {"order_id": "H-A"}))["ok"]
        assert (await client.invoke("get_order_status", {"order_id": "H-A"}))["data"][
            "status"
        ] == "shipped"
        if ending == "logout":
            hosted_store.revoke(login)
        elif ending == "expiry":
            with hosted_store.db.connect(write=True) as c:
                c.execute(
                    "UPDATE hosted_logins SET expires=0 WHERE fingerprint=?", (login.fingerprint,)
                )
        else:
            hosted_store.configure(
                replace(hosted_settings, invites=((hosted_settings.issuer, "fixture-B"),))
            )
        assert (await client.invoke("get_order_status", {"order_id": "H-A"}))["error"][
            "code"
        ] == "ACCESS_DENIED"


async def test_forged_or_unbound_production_connection_denied(hosted_store, login):
    token = hosted_store.provision(login, tasks_per_hour=5)
    for kwargs, capability in [
        ({}, token),
        ({"enable_demo_auth": True}, token),
        ({"enable_hosted_auth": True}, "forged"),
    ]:
        with pytest.raises(SafeError):
            async with connect(hosted_store.db.path, hosted_store, capability, **kwargs):
                pytest.fail("Unsafe production connection")


def test_logout_expiry_and_cookie_replay(hosted_store, login):
    token = hosted_store.provision(login, tasks_per_hour=5)
    hosted_store.revoke(login)
    with pytest.raises(SafeError):
        hosted_store.register_login(login)
    with hosted_store.db.connect() as c:
        with pytest.raises(SafeError):
            hosted_store.session(c, token)


def test_rate_limit_does_not_reset_on_relogin(hosted_store, login, claims, hosted_settings):
    hosted_store.provision(login, tasks_per_hour=1)
    fresh = authorize_native_user({**claims, "nonce": "new-nonce"}, hosted_settings, time.time())
    hosted_store.register_login(fresh)
    with pytest.raises(SafeError):
        hosted_store.provision(fresh, tasks_per_hour=1)


def test_paid_disabled_constructs_no_provider(hosted_store, hosted_settings, login):
    def forbidden():
        pytest.fail("Paid provider constructed")

    controller = HostedController(hosted_store, login, hosted_settings, provider_factory=forbidden)
    controller.submit("List products", "disabled-event", "en")
    assert controller.error and not controller.available
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 0


def test_exact_draft_confirm_edit_cancel_and_same_task(hosted_store, enabled, login):
    scripts = []

    def final(payload):
        result = json.loads(payload["messages"][-1]["content"])
        return completion("Support ticket " + result["data"]["ticket_id"] + " was created.")

    batches = [
        [
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Fixture damage",
                            "message": "Synthetic damaged headphones",
                            "idempotency_key": "hosted-fixture",
                        },
                    )
                ]
            )
        ],
        [final],
    ]

    def factory():
        script = SDKScript(batches.pop(0))
        scripts.append(script)
        return script.provider

    controller = HostedController(hosted_store, login, enabled, provider_factory=factory)
    controller.submit("Open a support ticket", "event-1", "en")
    pending = controller._pending
    assert pending is not None and len(scripts) == 1
    before = Journal(hosted_store, pending.token).load(pending.task_id)
    assert controller.edit("Fixture damage", "Edited synthetic damage", "", "en")
    edited = Journal(hosted_store, pending.token).load(pending.task_id)
    assert (before.turns, before.held_usd, before.active_seconds) == (
        edited.turns,
        edited.held_usd,
        edited.active_seconds,
    )
    controller.decide(confirm=True, revision=controller.revision, locale="en")
    after = Journal(hosted_store, pending.token).load(pending.task_id)
    assert after.status == "completed" and after.turns == 2 and after.held_usd > before.held_usd
    assert after.active_seconds >= before.active_seconds
    controller.decide(confirm=True, revision=controller.revision - 1, locale="en")
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
        assert c.execute("SELECT message FROM tickets").fetchone()[0] == "Edited synthetic damage"
        assert c.execute("SELECT count(*) FROM hosted_calls").fetchone()[0] == 2
    assert all(s.provider.mode == "fixture" for s in scripts)


def test_kill_switch_blocks_confirmation_cancel_preserves_cost(hosted_store, enabled, login):
    scripts = []

    def factory():
        s = SDKScript(
            [
                completion(
                    calls=[
                        (
                            "create_support_ticket",
                            {
                                "subject": "Fixture support",
                                "message": "Synthetic question",
                                "idempotency_key": "cancel-fixture",
                            },
                        )
                    ]
                )
            ]
        )
        scripts.append(s)
        return s.provider

    controller = HostedController(hosted_store, login, enabled, provider_factory=factory)
    controller.submit("Open a ticket", "event-cancel", "ar")
    pending = controller._pending
    assert pending
    before = Journal(hosted_store, pending.token).load(pending.task_id)
    hosted_store.set_kill(enabled=False)
    controller.decide(confirm=True, revision=controller.revision, locale="ar")
    assert len(scripts) == 1
    controller.decide(confirm=False, revision=controller.revision, locale="ar")
    after = Journal(hosted_store, pending.token).load(pending.task_id)
    assert (
        after.status == "confirmation_declined"
        and after.turns == before.turns
        and after.held_usd == before.held_usd
    )
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0


def test_kill_blocks_direct_mcp_ticket_write_and_unconfirmed_calls(hosted_store, enabled, login):
    token = hosted_store.provision(login, tasks_per_hour=5)
    draft = TicketDraft(
        subject="Synthetic", message="Synthetic only", idempotency_key="write-guard"
    )
    ref = hosted_store.register_confirmation(token, draft, confirmed=True)
    hosted_store.set_kill(enabled=False)
    with pytest.raises(SafeError):
        hosted_store.create_support_ticket(
            token, **draft.model_dump(exclude_none=True), confirmation_reference=ref
        )


def test_pending_capability_cannot_move_to_another_login(hosted_store, enabled, login, claims):
    def factory():
        return SDKScript(
            [
                completion(
                    calls=[
                        (
                            "create_support_ticket",
                            {
                                "subject": "Synthetic",
                                "message": "Synthetic only",
                                "idempotency_key": "bound-login",
                            },
                        )
                    ]
                )
            ]
        ).provider

    first = HostedController(hosted_store, login, enabled, provider_factory=factory)
    first.submit("Open a synthetic ticket", "bound-1", "en")
    assert first._pending
    fresh = authorize_native_user({**claims, "nonce": "separate-browser"}, enabled, time.time())

    def forbidden():
        pytest.fail("Another login resumed a private pending task")

    second = HostedController(hosted_store, fresh, enabled, provider_factory=forbidden)
    second._pending = first._pending  # Simulate accidental server-side state mixing.
    second.decide(confirm=True, revision=second.revision, locale="en")
    assert second.error
    with hosted_store.db.connect() as c:
        assert c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
