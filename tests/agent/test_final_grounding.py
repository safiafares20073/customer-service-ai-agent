"""Source-grounding samples use scripted provider decisions and real MCP results.

These verify data/tool plumbing, not universal live-model hallucination resistance.
"""

import json

import pytest

from tests.agent_support import completion
from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.tool_server.client import connect


@pytest.mark.parametrize("locale", ["en", "ar"])
@pytest.mark.parametrize(
    "product,price,stock",
    [
        ("P-100", "25.00", "in_stock"),
        ("P-200", "40.00", "in_stock"),
        ("P-300", "15.00", "out_of_stock"),
    ],
)
async def test_price_and_availability_come_from_actual_mcp_details(
    database, store, tokens, pricing, sdk_script, tmp_path, locale, product, price, stock
):
    def grounded(payload):
        data = json.loads(payload["messages"][-1]["content"])["data"]
        assert data["product_id"] == product and data["price"] == price
        assert data["availability"] == stock
        available = data["availability"] == "in_stock"
        label = (
            ("متوفر" if available else "غير متوفر")
            if locale == "ar"
            else ("in stock" if available else "out of stock")
        )
        return completion(f"**{data['name']}**: USD {data['price']}; {label}.")

    script = sdk_script(
        [completion(calls=[("get_product_details", {"product_id": product})]), grounded]
    )
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        outcome = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path,
        ).start(
            "هل المنتج متوفر وما سعره؟"
            if locale == "ar"
            else "Is the item in stock and what is its price?"
        )
    assert outcome.status == "completed" and price in outcome.answer
    if stock == "out_of_stock":
        assert ("غير متوفر" if locale == "ar" else "out of stock") in outcome.answer


@pytest.mark.parametrize("locale", ["en", "ar"])
async def test_unsupported_return_period_uses_receipt_policy_not_user_claim(
    database, store, tokens, pricing, sdk_script, tmp_path, locale
):
    def grounded(payload):
        data = json.loads(payload["messages"][-1]["content"])["data"]
        policy = data["policies"][0]["text"]
        assert "14 days" in policy and "original receipt" in policy
        return completion(policy if locale == "en" else "الإرجاع خلال 14 يومًا بالإيصال الأصلي.")

    script = sdk_script(
        [completion(calls=[("get_store_policies", {"topic": "returns"})]), grounded]
    )
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        outcome = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path,
        ).start("Can I return after 90 days?")
    assert outcome.status == "completed" and "14" in outcome.answer and "90" not in outcome.answer


async def test_unknown_product_stops_without_invented_answer(
    database, store, tokens, pricing, sdk_script, tmp_path
):
    script = sdk_script([completion(calls=[("get_product_details", {"product_id": "P-999"})])])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        outcome = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path,
        ).start("Tell me about P-999")
    assert outcome.status == "not_found" and len(script.requests) == 1
    assert "USD" not in outcome.answer
