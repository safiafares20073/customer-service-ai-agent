import asyncio
import json

import pytest

from yemen_customer_service.storage.store import digest
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError, TicketDraft


def draft(**changes):
    return TicketDraft.model_validate(
        {
            "subject": "Synthetic support",
            "message": "Synthetic broken product",
            "idempotency_key": "permission-test",
            **changes,
        }
    )


async def access(session):
    response = await session.call_tool("verify_order_access", {"order_id": "DEMO-100"})
    assert not response.isError
    return response.structuredContent["data"]["access_reference"]


def denied(response, code):
    assert response.isError
    assert response.structuredContent["error"]["code"] == code
    assert "data" not in response.structuredContent


async def test_reference_cannot_cross_principal_or_session(wire, store, tokens):
    same_customer_session = store.provision_demo_session(
        "demo-a", enable_demo_auth=True, app_env="development"
    )
    async with wire(tokens["demo-a"]) as owner:
        reference = await access(owner)
    for token in (tokens["demo-b"], same_customer_session):
        async with wire(token) as other:
            denied(
                await other.call_tool(
                    "get_order_status",
                    {
                        "order_id": "DEMO-100",
                        "access_reference": reference,
                    },
                ),
                "ACCESS_DENIED",
            )


async def test_expired_reference_and_rechecked_ownership(wire, tokens, database):
    async with wire(tokens["demo-a"]) as session:
        reference = await access(session)
        args = {"order_id": "DEMO-100", "access_reference": reference}
        with database.connect(write=True) as conn:
            conn.execute("UPDATE order_access SET expires_at=0")
        denied(await session.call_tool("get_order_status", args), "ACCESS_DENIED")
        reference = await access(session)
        with database.connect(write=True) as conn:
            conn.execute("UPDATE orders SET customer_id='demo-b' WHERE order_id='DEMO-100'")
        denied(
            await session.call_tool(
                "get_order_status",
                {
                    **args,
                    "access_reference": reference,
                },
            ),
            "ACCESS_DENIED",
        )


async def test_confirmation_is_payload_and_session_bound(wire, tokens, store):
    original = draft()
    confirmation = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    args = {**original.model_dump(), "confirmation_reference": confirmation}
    async with wire(tokens["demo-b"]) as other:
        denied(await other.call_tool("create_support_ticket", args), "CONFIRMATION_REQUIRED")
    async with wire(tokens["demo-a"]) as session:
        for changed in (
            {"message": "Edited"},
            {"subject": "Edited"},
            {"idempotency_key": "changed-key"},
        ):
            denied(
                await session.call_tool("create_support_ticket", {**args, **changed}),
                "CONFIRMATION_REQUIRED",
            )
        assert not (await session.call_tool("create_support_ticket", args)).isError


async def test_expired_and_replaced_confirmation_denied(wire, tokens, store, database):
    original = draft()
    old = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    replacement = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    async with wire(tokens["demo-a"]) as session:
        denied(
            await session.call_tool(
                "create_support_ticket",
                {
                    **original.model_dump(),
                    "confirmation_reference": old,
                },
            ),
            "CONFIRMATION_REQUIRED",
        )
        with database.connect(write=True) as conn:
            conn.execute("UPDATE confirmations SET expires_at=0")
        denied(
            await session.call_tool(
                "create_support_ticket",
                {
                    **original.model_dump(),
                    "confirmation_reference": replacement,
                },
            ),
            "CONFIRMATION_REQUIRED",
        )


async def test_linked_order_requires_paired_fields_and_real_access(wire, store, tokens):
    original = draft(order_id="DEMO-100")
    confirmation = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    args = {**original.model_dump(), "confirmation_reference": confirmation}
    async with wire(tokens["demo-a"]) as session:
        denied(await session.call_tool("create_support_ticket", args), "INVALID_INPUT")
        denied(
            await session.call_tool(
                "create_support_ticket",
                {
                    **args,
                    "access_reference": "x" * 43,
                },
            ),
            "ACCESS_DENIED",
        )
        denied(
            await session.call_tool(
                "create_support_ticket",
                {
                    **args,
                    "order_id": None,
                    "access_reference": "x" * 43,
                },
            ),
            "INVALID_INPUT",
        )
        reference = await access(session)
        assert not (
            await session.call_tool(
                "create_support_ticket",
                {
                    **args,
                    "access_reference": reference,
                },
            )
        ).isError


async def test_ticket_insert_failure_rolls_back_consent(wire, tokens, store, database):
    original = draft()
    confirmation = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    args = {**original.model_dump(), "confirmation_reference": confirmation}
    with database.connect(write=True) as conn:
        conn.execute("""CREATE TRIGGER fail_ticket BEFORE INSERT ON tickets
                        BEGIN SELECT RAISE(ABORT, 'sensitive internal detail'); END""")
    async with wire(tokens["demo-a"]) as session:
        response = await session.call_tool("create_support_ticket", args)
        denied(response, "INTERNAL_ERROR")
        assert "sensitive internal detail" not in response.model_dump_json()
        assert confirmation not in response.model_dump_json()
        with database.connect(write=True) as conn:
            assert conn.execute("SELECT consumed FROM confirmations").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
            conn.execute("DROP TRIGGER fail_ticket")
        assert not (await session.call_tool("create_support_ticket", args)).isError


async def test_concurrent_retries_create_one_ticket(wire, tokens, store, database):
    original = draft()
    confirmation = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    args = {**original.model_dump(), "confirmation_reference": confirmation}
    async with wire(tokens["demo-a"]) as first, wire(tokens["demo-a"]) as second:
        responses = await asyncio.gather(
            first.call_tool("create_support_ticket", args),
            second.call_tool("create_support_ticket", args),
        )
        assert all(not response.isError for response in responses)
        assert responses[0].structuredContent == responses[1].structuredContent
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1


async def test_expired_session_denies_existing_ticket_retry(wire, tokens, store, database):
    original = draft()
    confirmation = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    args = {**original.model_dump(), "confirmation_reference": confirmation}
    async with wire(tokens["demo-a"]) as session:
        assert not (await session.call_tool("create_support_ticket", args)).isError
        with database.connect(write=True) as conn:
            conn.execute("UPDATE sessions SET expires_at=0")
        denied(await session.call_tool("create_support_ticket", args), "ACCESS_DENIED")


async def test_adapter_hides_refs_and_rejects_model_consent(database, store, tokens):
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        schemas = await client.tools_for_model()
        assert len(schemas) == 7
        schema_text = json.dumps(schemas)
        assert "access_reference" not in schema_text
        assert "confirmation_reference" not in schema_text
        verified = await client.invoke("verify_order_access", {"order_id": "DEMO-100"})
        assert verified == {"ok": True, "data": {"authorized": True}}
        assert (await client.invoke("get_order_status", {"order_id": "DEMO-100"}))["ok"]
        original = draft(order_id="DEMO-100")
        with pytest.raises(SafeError, match="confirmation"):
            await client.invoke("create_support_ticket", original.model_dump())
        with pytest.raises(SafeError):
            await client.invoke(
                "get_order_status",
                {
                    "order_id": "DEMO-100",
                    "access_reference": "x" * 43,
                },
            )
        with pytest.raises(SafeError):
            await client.invoke("register_confirmation", {"confirmed": True})
        with pytest.raises(SafeError):
            client.confirm_ticket(original, confirmed=False)
        client.confirm_ticket(original, confirmed=True)
        response = await client.invoke("create_support_ticket", original.model_dump())
        assert response["ok"]
        assert "reference" not in json.dumps(response)
        assert response == await client.invoke("create_support_ticket", original.model_dump())
        with pytest.raises(SafeError, match="confirmation"):
            await client.invoke(
                "create_support_ticket",
                {
                    **original.model_dump(),
                    "message": "Edited without consent",
                },
            )


async def test_errors_audits_and_stderr_do_not_leak_refs(wire, store, tokens, database, tmp_path):
    original = draft()
    confirmation = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    async with wire(tokens["demo-a"]) as session:
        reference = await access(session)
        # Extra-field errors must not echo input values or SDK validation details.
        response = await session.call_tool(
            "get_order_status",
            {
                "order_id": "DEMO-100",
                "access_reference": reference,
                "extra": confirmation,
            },
        )
        denied(response, "INVALID_INPUT")
        assert all(
            token not in response.model_dump_json()
            for token in (
                tokens["demo-a"],
                reference,
                confirmation,
            )
        )
    with database.connect() as conn:
        audits = json.dumps([dict(row) for row in conn.execute("SELECT * FROM audits")])
        saved = "\n".join(conn.iterdump())
        assert digest(tokens["demo-a"]) in saved
        assert all(token not in saved for token in (tokens["demo-a"], reference, confirmation))
    stderr = (tmp_path / "server-stderr.log").read_text()
    assert all(
        token not in audits + stderr for token in (tokens["demo-a"], reference, confirmation)
    )
    assert original.message not in audits and "demo-a" not in audits


@pytest.mark.parametrize("action", ["edit", "decline"])
async def test_trusted_edit_or_decline_revokes_wire_consent(wire, store, tokens, action):
    original = draft()
    reference = store.register_confirmation(tokens["demo-a"], original, confirmed=True)
    if action == "edit":
        store.revoke_confirmations(tokens["demo-a"])
    else:
        with pytest.raises(SafeError):
            store.register_confirmation(tokens["demo-a"], original, confirmed=False)
    async with wire(tokens["demo-a"]) as session:
        denied(
            await session.call_tool(
                "create_support_ticket",
                {
                    **original.model_dump(),
                    "confirmation_reference": reference,
                },
            ),
            "CONFIRMATION_REQUIRED",
        )


async def test_adapter_cancel_revokes_server_side_consent(database, store, tokens):
    original = draft()
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        client.confirm_ticket(original, confirmed=True)
        client.cancel_ticket()
        with pytest.raises(SafeError):
            await client.invoke("create_support_ticket", original.model_dump())
    with database.connect() as conn:
        assert (
            conn.execute("SELECT count(*) FROM confirmations WHERE consumed=0").fetchone()[0] == 0
        )
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


async def test_adapter_requires_demo_opt_in_and_never_downgrades_production(
    database, store, tokens, monkeypatch
):
    with pytest.raises(SafeError):
        async with connect(database.path, store, tokens["demo-a"]):
            pytest.fail("Authenticated session launched without demo opt-in")
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(SafeError):
        async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True):
            pytest.fail("Production mode was downgraded to development")
