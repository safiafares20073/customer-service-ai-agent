"""Scripted demonstration responses, NOT live model inference. MCP stays real."""

import json
import re
import uuid

import httpx
from openai import AsyncOpenAI

from yemen_customer_service.agent.provider import OpenAIProvider


def demonstration_provider() -> OpenAIProvider:
    ticket_key = "demo-" + uuid.uuid4().hex[:16]

    async def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.host == "fixture.invalid"
        assert body["reasoning_effort"] == "none" and body["service_tier"] == "default"
        messages = body["messages"]
        customer = next(m["content"] for m in reversed(messages) if m["role"] == "user")
        arabic = bool(re.search(r"[\u0600-\u06ff]", customer))
        tool_results = []
        names = {}
        for message in messages:
            if message["role"] == "assistant":
                names = {c["id"]: c["function"]["name"] for c in message.get("tool_calls", [])}
            if message["role"] == "tool":
                tool_results.append(
                    (names.get(message["tool_call_id"]), json.loads(message["content"]))
                )
        last_name, last_result = tool_results[-1] if tool_results else (None, None)
        call, content = None, None
        ticket = any(word in customer.casefold() for word in ("ticket", "damaged", "تذكرة", "تالف"))
        order = re.search(r"\bDEMO-\d+\b", customer, re.I)
        if last_name == "create_support_ticket":
            ticket_id = last_result["data"]["ticket_id"]
            content = (
                f"تم إنشاء تذكرة الدعم {ticket_id}."
                if arabic
                else f"Support ticket {ticket_id} was created."
            )
        elif ticket:
            call = (
                "create_support_ticket",
                {
                    "subject": "منتج تالف — طلب تجريبي"
                    if arabic
                    else "Damaged product — synthetic request",
                    "message": customer,
                    "idempotency_key": ticket_key,
                    "order_id": order[0].upper() if order else None,
                },
            )
        elif order:
            if last_name == "get_order_status":
                status = last_result["data"]["status"]
                translated = {"shipped": "تم الشحن", "processing": "قيد التجهيز"}.get(
                    status, status
                )
                content = (
                    f"حالة الطلب {order[0].upper()}: {translated}."
                    if arabic
                    else f"Order {order[0].upper()} is {status}. No delivery estimate is available."
                )
            elif last_name == "verify_order_access":
                call = ("get_order_status", {"order_id": order[0].upper()})
            else:
                call = ("verify_order_access", {"order_id": order[0].upper()})
        elif last_name == "get_store_policies":
            products = next(
                (
                    r["data"]["products"]
                    for n, r in tool_results
                    if n in {"search_products", "list_products"}
                ),
                [],
            )
            policy = last_result["data"]["policies"][0]["text"]
            if arabic:
                content = "\n".join(f"{p['name']}: {p['price']} {p['currency']}" for p in products)
                days = re.search(r"\b(\d+)\s+days\b", policy)
                content += (
                    f"\nالإرجاع خلال {days[1]} يومًا مع الإيصال الأصلي."
                    if days and "original receipt" in policy
                    else "\n" + policy
                )
            else:
                content = "\n".join(f"{p['name']}: {p['price']} {p['currency']}" for p in products)
                content += "\n" + policy
        elif last_name in {"list_products", "search_products"}:
            call = ("get_store_policies", {"topic": "returns"})
        else:
            call = ("search_products", {"query": "headphones"})
        message = {"role": "assistant", "content": content}
        if call:
            message["tool_calls"] = [
                {
                    "id": "call_" + uuid.uuid4().hex[:16],
                    "type": "function",
                    "function": {"name": call[0], "arguments": json.dumps(call[1])},
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": "scripted-demo",
                "object": "chat.completion",
                "created": 0,
                "model": body["model"],
                "service_tier": "default",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": "tool_calls" if call else "stop",
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 30, "total_tokens": 130},
            },
        )

    sdk = AsyncOpenAI(
        api_key="fixture-not-a-real-key",
        max_retries=0,
        base_url="https://fixture.invalid/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    )
    return OpenAIProvider(sdk, "gpt-6-luna", mode="fixture")
