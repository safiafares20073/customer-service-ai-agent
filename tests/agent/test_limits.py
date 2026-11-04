import asyncio
from decimal import Decimal

import httpx
import pytest

from tests.agent_support import completion
from yemen_customer_service.agent.loop import SYSTEM, Agent
from yemen_customer_service.agent.state import Journal, Limits
from yemen_customer_service.tool_server.client import connect


async def execute(database, store, token, provider, pricing, tmp_path, *, limits=None):
    async with connect(database.path, store, token, enable_demo_auth=True) as client:
        return await Agent(
            client,
            Journal(store, token),
            provider,
            pricing,
            limits=limits,
            trace_directory=tmp_path / "evidence",
        ).start("List products")


async def test_exactly_eight_requests_then_no_extra_final_call(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([completion(calls=[("list_products", {})]) for _ in range(8)])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "turn_limit" and outcome.turns == 8 and len(script.requests) == 8
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM cost_records").fetchone()[0] == 8


async def test_budget_preflight_refuses_first_request(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([])
    outcome = await execute(
        database,
        store,
        tokens["demo-a"],
        script.provider,
        pricing,
        tmp_path,
        limits=Limits(budget_usd=Decimal("0.00000001")),
    )
    assert outcome.status == "budget_limit" and outcome.turns == 0 and script.requests == []
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM cost_records").fetchone()[0] == 0


async def test_budget_is_reserved_before_each_subsequent_request(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        schemas = await client.tools_for_model()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": s["name"],
                    "description": s["description"],
                    "parameters": s["inputSchema"],
                    "strict": False,
                },
            }
            for s in schemas
        ]
        bound, reserve = pricing.reserve(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "List products"}],
            tools,
            512,
        )
        script = sdk_script(
            [completion(calls=[("list_products", {})], prompt_tokens=bound, completion_tokens=512)]
        )
        outcome = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            limits=Limits(budget_usd=reserve * Decimal("1.5")),
            trace_directory=tmp_path,
        ).start("List products")
        assert outcome.status == "budget_limit" and len(script.requests) == 1
        assert Decimal(outcome.estimated_or_recorded_usd) == reserve


@pytest.mark.parametrize(
    "action",
    [
        completion("Unusable answer", usage=False),
        completion("Unusable answer", prompt_tokens_details={"cached_tokens": 101}),
    ],
)
async def test_unknown_usage_retains_reservation_and_stops(
    action,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([action])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "unknown_usage" and not outcome.cost_known
    assert Decimal(outcome.estimated_or_recorded_usd) > 0 and len(script.requests) == 1
    with database.connect() as conn:
        row = conn.execute("SELECT * FROM cost_records").fetchone()
        assert row["status"] == "unknown" and row["cost_usd"] is None


async def test_unknown_pricing_makes_no_request(database, store, tokens, sdk_script, tmp_path):
    script = sdk_script([])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, None, tmp_path)
    assert outcome.status == "pricing_unavailable" and outcome.turns == 0
    assert len(script.requests) == 0


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_provider_errors_have_no_hidden_retries_or_fake_zero_cost(
    status,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    error = httpx.Response(
        status,
        json={
            "error": {"message": "do-not-disclose-provider-detail", "type": "test", "code": "test"}
        },
    )
    script = sdk_script([error])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "provider_error" and len(script.requests) == 1
    assert not outcome.cost_known and "do-not-disclose" not in outcome.answer
    with database.connect() as conn:
        row = conn.execute("SELECT status, cost_usd FROM cost_records").fetchone()
        assert tuple(row) == ("unknown", None)
    events = "".join(p.read_text() for p in (tmp_path / "evidence").glob("*.jsonl"))
    assert "do-not-disclose-provider-detail" not in events


async def test_cumulative_active_timeout_stops_pending_provider_and_records_unknown(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    cancelled = False

    async def slow_provider(_):
        nonlocal cancelled
        try:
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            cancelled = True
            raise
        return completion("Late answer")

    script = sdk_script([slow_provider])
    outcome = await execute(
        database,
        store,
        tokens["demo-a"],
        script.provider,
        pricing,
        tmp_path,
        # Cold SDK serialization can exceed 100 ms before dispatch. Leave setup
        # headroom while still timing out a real in-flight fixture request.
        limits=Limits(active_seconds=1),
    )
    assert outcome.status == "time_limit" and len(script.requests) == 1
    assert not outcome.cost_known and 1 <= outcome.active_seconds < 2
    assert cancelled


async def test_resume_does_not_reset_elapsed_allowance(
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
                            "idempotency_key": "time-test",
                        },
                    )
                ]
            )
        ]
    )
    journal = Journal(store, tokens["demo-a"])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        agent = Agent(client, journal, script.provider, pricing, trace_directory=tmp_path)
        paused = await agent.start("Prepare a ticket")
        state = journal.load(paused.task_id)
        state.active_seconds = 60
        journal.save(state)
        result = await agent.resume(paused.task_id, confirmed=True)
        assert result.status == "time_limit" and result.turns == 1
        assert len(script.requests) == 1 and result.active_seconds >= 60
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


async def test_usage_above_reservation_is_recorded_and_stops(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([completion("Late accounting", prompt_tokens=1_000_000)])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "usage_bound_exceeded" and len(script.requests) == 1
    with database.connect() as conn:
        row = conn.execute("SELECT status, input_tokens, cost_usd FROM cost_records").fetchone()
        assert row["status"] == "recorded" and row["input_tokens"] == 1_000_000
        assert Decimal(row["cost_usd"]) > Decimal("0.05")


async def test_empty_choices_still_accounts_available_usage(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    response = completion("Unused")
    response["choices"] = []
    script = sdk_script([response])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "invalid_model_response" and outcome.cost_known
    with database.connect() as conn:
        assert conn.execute("SELECT status FROM cost_records").fetchone()[0] == "recorded"


@pytest.mark.parametrize(
    ("field", "value"), [("model", "different-model"), ("service_tier", "flex")]
)
async def test_no_silent_model_or_pricing_mode_substitution(
    field,
    value,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    response = completion("Wrong configuration")
    response[field] = value
    script = sdk_script([response])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "unknown_usage" and not outcome.cost_known
    assert len(script.requests) == 1


async def test_session_expiring_during_request_preserves_actual_accounting(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    def expire(_):
        with database.connect(write=True) as conn:
            conn.execute("UPDATE sessions SET expires_at=0")
        return completion("This answer must not be delivered")

    script = sdk_script([expire])
    outcome = await execute(database, store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert outcome.status == "access_denied" and len(script.requests) == 1
    with database.connect() as conn:
        row = conn.execute("SELECT * FROM cost_records").fetchone()
        assert row["status"] == "recorded" and row["input_tokens"] == 100


async def test_trace_failure_prevents_provider_request(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    blocked = tmp_path / "blocked"
    blocked.write_text("Not a directory")
    script = sdk_script([])
    async with connect(database.path, store, tokens["demo-a"], enable_demo_auth=True) as client:
        result = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            trace_directory=blocked,
        ).start("List products")
    assert result.status == "internal_error" and len(script.requests) == 0
