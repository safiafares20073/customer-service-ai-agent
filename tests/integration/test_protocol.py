import json

import pytest
from jsonschema import Draft202012Validator

from yemen_customer_service.tool_server.models import TicketDraft

TOOLS = {
    "list_products",
    "search_products",
    "get_product_details",
    "get_store_policies",
    "verify_order_access",
    "get_order_status",
    "create_support_ticket",
}


def body(response, *, error=False, code=None):
    assert response.isError is error
    assert response.structuredContent == json.loads(response.content[0].text)
    if error:
        assert response.structuredContent["ok"] is False
        assert response.structuredContent["error"]["code"] == code
    else:
        assert response.structuredContent["ok"] is True
    return response.structuredContent


async def test_discovery_and_all_public_tools(wire):
    async with wire() as session:
        tools = (await session.list_tools()).tools
        assert {tool.name for tool in tools} == TOOLS
        assert len(tools) == 7
        for tool in tools:
            assert tool.inputSchema["additionalProperties"] is False
            Draft202012Validator.check_schema(tool.inputSchema)
            Draft202012Validator.check_schema(tool.outputSchema)
        first = body(await session.call_tool("list_products", {"limit": 1}))["data"]
        assert first["products"][0]["product_id"] == "P-100"
        second = body(
            await session.call_tool("list_products", {"limit": 1, "cursor": first["next_cursor"]})
        )["data"]
        assert second["products"][0]["product_id"] == "P-200"
        all_products = body(await session.call_tool("list_products", {}))["data"]
        assert len(all_products["products"]) == 3 and all_products["next_cursor"] is None
        found = body(await session.call_tool("search_products", {"query": "HEADPHONES"}))
        assert [p["product_id"] for p in found["data"]["products"]] == ["P-100"]
        injection = body(await session.call_tool("search_products", {"query": "' OR 1=1 --"}))
        assert injection["data"]["products"] == []
        product = body(await session.call_tool("get_product_details", {"product_id": "P-100"}))
        assert product["data"]["price"] == "25.00"
        assert product["data"]["availability"] == "in_stock"
        body(
            await session.call_tool("get_product_details", {"product_id": "missing"}),
            error=True,
            code="NOT_FOUND",
        )
        policies = body(await session.call_tool("get_store_policies", {"topic": "all"}))
        assert len(policies["data"]["policies"]) == 4
        returns = body(await session.call_tool("get_store_policies", {"topic": "returns"}))
        assert returns["data"]["policies"][0]["version"] == "demo-v1"
        assert "14 days" in returns["data"]["policies"][0]["text"]


async def test_private_tools_confirmation_and_idempotency(wire, tokens, store, database):
    async with wire(tokens["demo-a"]) as session:
        access = body(await session.call_tool("verify_order_access", {"order_id": "DEMO-100"}))
        reference = access["data"]["access_reference"]
        order = body(
            await session.call_tool(
                "get_order_status",
                {
                    "order_id": "DEMO-100",
                    "access_reference": reference,
                },
            )
        )
        assert order["data"] == {
            "order_id": "DEMO-100",
            "status": "shipped",
            "estimated_delivery": None,
        }
        draft = TicketDraft(
            subject="Damaged headphones",
            message="Synthetic broken earcup",
            order_id="DEMO-100",
            idempotency_key="test-ticket-1",
        )
        args = {
            **draft.model_dump(),
            "access_reference": reference,
            "confirmation_reference": "x" * 43,
        }
        body(
            await session.call_tool("create_support_ticket", args),
            error=True,
            code="CONFIRMATION_REQUIRED",
        )
        args["confirmation_reference"] = store.register_confirmation(
            tokens["demo-a"], draft, confirmed=True
        )
        created = body(await session.call_tool("create_support_ticket", args))
        repeated = body(await session.call_tool("create_support_ticket", args))
        assert created == repeated
        body(
            await session.call_tool("create_support_ticket", {**args, "message": "Changed"}),
            error=True,
            code="IDEMPOTENCY_CONFLICT",
        )
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
        assert conn.execute("SELECT consumed FROM confirmations").fetchone()[0] == 1
        events = conn.execute("SELECT outcome, result_code FROM audits").fetchall()
        assert ("deny", "CONFIRMATION_REQUIRED") in [tuple(row) for row in events]
        assert ("allow", "OK") in [tuple(row) for row in events]


async def test_anonymous_and_forged_session_private_calls_denied(wire):
    for token in (None, "forged-session-token"):
        async with wire(token) as session:
            body(
                await session.call_tool("verify_order_access", {"order_id": "DEMO-100"}),
                error=True,
                code="ACCESS_DENIED",
            )
            body(
                await session.call_tool(
                    "get_order_status",
                    {
                        "order_id": "DEMO-100",
                        "access_reference": "x" * 43,
                    },
                ),
                error=True,
                code="ACCESS_DENIED",
            )
            body(
                await session.call_tool(
                    "create_support_ticket",
                    {
                        "subject": "Demo",
                        "message": "Demo only",
                        "idempotency_key": "key",
                        "confirmation_reference": "x" * 43,
                    },
                ),
                error=True,
                code="ACCESS_DENIED",
            )


async def test_missing_and_foreign_orders_have_same_denial(wire, tokens):
    async with wire(tokens["demo-a"]) as session:
        foreign = body(
            await session.call_tool("verify_order_access", {"order_id": "DEMO-200"}),
            error=True,
            code="ACCESS_DENIED",
        )
        missing = body(
            await session.call_tool("verify_order_access", {"order_id": "MISSING"}),
            error=True,
            code="ACCESS_DENIED",
        )
        assert foreign == missing
        body(
            await session.call_tool(
                "get_order_status",
                {
                    "order_id": "DEMO-200",
                    "access_reference": "x" * 43,
                },
            ),
            error=True,
            code="ACCESS_DENIED",
        )


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("list_products", {"limit": 0}),
        ("list_products", {"limit": 21}),
        ("list_products", {"limit": True}),
        ("list_products", {"limit": "1"}),
        ("list_products", {"cursor": "not-base64"}),
        ("list_products", {"cursor": "a" * 129}),
        ("search_products", {"query": ""}),
        ("search_products", {"query": "   "}),
        ("search_products", {"query": "a" * 201}),
        ("search_products", {"query": {"malicious": "object"}}),
        ("get_product_details", {"product_id": None}),
        ("get_product_details", {"product_id": "P-100", "extra": "ignored?"}),
        ("get_store_policies", {"topic": "admin"}),
        ("verify_order_access", {"order_id": "DEMO-100", "customer_id": "demo-a"}),
        ("get_order_status", {"order_id": "DEMO-100"}),
        ("get_order_status", {"order_id": "DEMO-100", "access_reference": "short"}),
        ("create_support_ticket", {"subject": "Demo", "message": "Demo", "idempotency_key": "k"}),
        (
            "create_support_ticket",
            {
                "subject": "x" * 121,
                "message": "Demo",
                "idempotency_key": "k",
                "confirmation_reference": "x" * 43,
            },
        ),
    ],
)
async def test_malformed_wire_arguments(wire, tool, args):
    async with wire() as session:
        body(await session.call_tool(tool, args), error=True, code="INVALID_INPUT")


async def test_unknown_tool_rejected(wire):
    async with wire() as session:
        body(
            await session.call_tool("run_sql", {"query": "DELETE FROM orders"}),
            error=True,
            code="UNKNOWN_TOOL",
        )
