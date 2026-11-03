import asyncio
import json
from decimal import Decimal

import pytest

from tests.agent_support import completion
from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing
from yemen_customer_service.agent.state import Journal, Limits
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError


@pytest.mark.parametrize(
    ("customer_request", "actions", "expected_tools", "expected_answer"),
    [
        (
            "List the products",
            [
                completion(calls=[("list_products", {})]),
                completion("Example Headphones cost USD 25."),
            ],
            ["list_products"],
            "USD 25",
        ),
        (
            "Find headphones under $30 and explain returns",
            [
                completion(
                    calls=[
                        ("search_products", {"query": "headphones"}),
                        ("get_store_policies", {"topic": "returns"}),
                    ]
                ),
                completion(
                    "Example Headphones cost USD 25; returns within 14 days with a receipt."
                ),
            ],
            ["search_products", "get_store_policies"],
            "14 days",
        ),
        (
            "Tell me about P-100",
            [
                completion(calls=[("get_product_details", {"product_id": "P-100"})]),
                completion("Example Headphones are in stock at USD 25."),
            ],
            ["get_product_details"],
            "in stock",
        ),
        (
            "Where is my order DEMO-100?",
            [
                completion(calls=[("verify_order_access", {"order_id": "DEMO-100"})]),
                completion(calls=[("get_order_status", {"order_id": "DEMO-100"})]),
                completion("DEMO-100 has shipped; no delivery estimate is available."),
            ],
            ["verify_order_access", "get_order_status"],
            "shipped",
        ),
    ],
)
async def test_official_read_scenarios_real_mcp_fixture_provider(
    customer_request,
    actions,
    expected_tools,
    expected_answer,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script(actions)
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        outcome = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path / "evidence",
        ).start(customer_request)
    assert outcome.status == "completed" and expected_answer in outcome.answer
    assert outcome.turns == len(script.requests) == len(actions)
    for payload in script.requests:
        assert len(payload["tools"]) == 7
        schemas = json.dumps(payload["tools"])
        assert "access_reference" not in schemas and "confirmation_reference" not in schemas
    with database.connect() as conn:
        invoked = [row[0] for row in conn.execute("SELECT tool FROM audits WHERE outcome='allow'")]
        assert invoked == [*expected_tools, "agent"]
        costs = conn.execute("SELECT * FROM cost_records").fetchall()
        assert all(row["provider"] == "fixture" and row["status"] == "recorded" for row in costs)
        assert all(row["input_tokens"] == 100 and row["output_tokens"] == 20 for row in costs)
        assert sum(Decimal(row["cost_usd"]) for row in costs) == Decimal(
            outcome.estimated_or_recorded_usd
        )
    records = [
        json.loads(line)
        for p in (tmp_path / "evidence").glob("*.jsonl")
        for line in p.read_text().splitlines()
    ]
    assert all(event["evidence"] == "provider_fixture" for event in records)
    assert records[-1]["status"] == "completed"


async def test_fifth_scenario_confirmed_ticket_preserves_task_and_limits(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    draft = {
        "subject": "Damaged headphones",
        "message": "Synthetic damaged earcup",
        "order_id": "DEMO-100",
        "idempotency_key": "agent-ticket",
    }
    script = sdk_script(
        [
            completion(calls=[("create_support_ticket", draft)]),
            completion("Your support ticket was created."),
        ]
    )
    journal = Journal(store, tokens["demo-a"])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        agent = Agent(
            client, journal, script.provider, pricing, trace_directory=tmp_path / "evidence"
        )
        paused = await agent.start("Open a ticket about my damaged headphones")
        assert paused.status == "awaiting_confirmation" and paused.turns == 1
        assert paused.draft.model_dump() == draft
        before = journal.load(paused.task_id)
        with database.connect() as conn:
            assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
        await asyncio.sleep(0.03)  # Human think time must not enter active time accounting.
        resumed = await agent.resume(paused.task_id, confirmed=True)
        assert resumed.task_id == paused.task_id and resumed.status == "completed"
        assert resumed.turns == 2 and resumed.active_seconds >= before.active_seconds
        assert journal.load(paused.task_id).limits == before.limits
        assert Decimal(resumed.estimated_or_recorded_usd) > Decimal(
            paused.estimated_or_recorded_usd
        )
        with database.connect() as conn:
            assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
            assert conn.execute("SELECT consumed FROM confirmations").fetchone()[0] == 1


async def test_declined_ticket_never_writes_or_requests_again(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script(
        [
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Synthetic",
                            "message": "Synthetic",
                            "idempotency_key": "decline",
                        },
                    )
                ]
            )
        ]
    )
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        agent = Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path,
        )
        paused = await agent.start("Prepare a synthetic support ticket")
        result = await agent.resume(paused.task_id, confirmed=False)
        assert result.status == "confirmation_declined" and result.turns == 1
        assert len(script.requests) == 1
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (("verify_order_access", {"order_id": "DEMO-200"}), "access_denied"),
        (
            ("verify_order_access", {"order_id": "DEMO-100", "customer_id": "demo-b"}),
            "invalid_tool_arguments",
        ),
        (
            ("get_order_status", {"order_id": "DEMO-100", "access_reference": "x" * 43}),
            "invalid_tool_arguments",
        ),
        (("register_confirmation", {"confirmed": True}), "invalid_model_response"),
        (
            (
                "create_support_ticket",
                {
                    "subject": "Synthetic",
                    "message": "Synthetic",
                    "idempotency_key": "forged",
                    "confirmed": True,
                },
            ),
            "invalid_tool_arguments",
        ),
    ],
)
async def test_model_cannot_select_identity_refs_or_consent(
    call,
    expected,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([completion(calls=[call])])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        result = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path,
        ).start("Check my synthetic request")
    assert result.status == expected and len(script.requests) == 1
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0


async def test_resume_cannot_reset_turn_limit_or_change_customer(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script(
        [
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Synthetic",
                            "message": "Synthetic",
                            "idempotency_key": "bounded",
                        },
                    )
                ]
            )
        ]
    )
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        agent = Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            limits=Limits(turns=1),
            trace_directory=tmp_path,
        )
        paused = await agent.start("Create a synthetic ticket")
        # A newly constructed controller with default limits cannot raise saved limits.
        fresh = Agent(client, agent.journal, script.provider, pricing, trace_directory=tmp_path)
        result = await fresh.resume(paused.task_id, confirmed=True)
        assert result.status == "turn_limit" and result.turns == 1
        assert len(script.requests) == 1
    with pytest.raises(SafeError):
        Journal(store, tokens["demo-b"]).load(paused.task_id)


async def test_raw_session_capability_is_redacted_from_provider_memory_and_trace(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    token = tokens["demo-a"]
    script = sdk_script([completion("Synthetic answer " + token)])
    async with connect(database.path, store, token, enable_demo_auth=True) as client:
        result = await Agent(
            client, Journal(store, token), script.provider, pricing, trace_directory=tmp_path
        ).start("Synthetic request token=" + token)
    assert result.status == "completed"
    with database.connect() as conn:
        saved = "\n".join(conn.iterdump())
    evidence = "\n".join(p.read_text() for p in tmp_path.glob("*.jsonl"))
    assert all(
        token not in text
        for text in (
            result.answer,
            json.dumps(script.requests),
            saved,
            evidence,
        )
    )


@pytest.mark.parametrize("cached", [80, None])
async def test_reported_cache_usage_and_pricing_snapshot_are_durable(
    cached,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    response = completion(
        "Synthetic answer",
        prompt_tokens_details=({"cached_tokens": cached} if cached is not None else None),
    )
    script = sdk_script([response])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        result = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=tmp_path,
        ).start("Synthetic request")
    assert result.status == "completed"
    with database.connect() as conn:
        row = conn.execute("SELECT value FROM metadata WHERE key='agent_cost:1'").fetchone()
        snapshot = json.loads(row[0])
        assert snapshot["cached_input_tokens"] == cached
        assert snapshot["pricing_version"] == pricing.version
        assert snapshot["input_usd_per_million"] == "0.10"
        assert snapshot["usage_source"] == "fixture"
        value = conn.execute("SELECT cost_usd FROM cost_records").fetchone()[0]
    expected = Decimal("0.0000128") if cached is not None else Decimal("0.000020")
    assert Decimal(value) == expected


async def test_corrected_pricing_cannot_silently_reprice_or_reset_pending_task(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    previous = Pricing(
        pricing.model,
        pricing.input_rate / 2,
        pricing.output_rate / 2,
        pricing.cached_rate / 2,
        "fixture_previous_flex_mislabeled_standard",
    )
    script = sdk_script(
        [
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Synthetic",
                            "message": "Synthetic",
                            "idempotency_key": "price-change",
                        },
                    )
                ]
            )
        ]
    )
    journal = Journal(store, tokens["demo-a"])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        paused = await Agent(
            client, journal, script.provider, previous, trace_directory=tmp_path
        ).start("Prepare a synthetic ticket")
        assert paused.status == "awaiting_confirmation"
        result = await Agent(
            client, journal, script.provider, pricing, trace_directory=tmp_path
        ).resume(paused.task_id, confirmed=True)
        assert result.status == "pricing_unavailable"
        assert result.task_id == paused.task_id and result.turns == paused.turns == 1
        assert result.estimated_or_recorded_usd == paused.estimated_or_recorded_usd
        assert len(script.requests) == 1
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
