import json
from datetime import UTC, date, datetime
from decimal import Decimal
from importlib.metadata import distribution
from pathlib import Path
from types import SimpleNamespace

import pytest
from openai import AsyncOpenAI

from tests.agent_support import MODEL, completion
from yemen_customer_service.agent import pricing as pricing_module
from yemen_customer_service.agent.cli import session_binding
from yemen_customer_service.agent.pricing import Pricing, PricingError, Usage
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError
from yemen_customer_service.agent.state import Limits
from yemen_customer_service.agent.tracing import Trace, safe_text


def test_corrected_user_supplied_standard_prices_and_cache_discount(pricing):
    assert pricing.model == MODEL
    assert pricing.input_rate == Decimal("0.10")
    assert pricing.output_rate == Decimal("0.50")
    assert pricing.cached_rate == Decimal("0.01")
    assert pricing.cost(Usage(1000, 100, 300)) == Decimal("0.000123")


@pytest.mark.parametrize(
    "change",
    [
        {"model": "another-model"},
        {"tier": "flex"},
        {"verified_on": "2026-12-31"},
        {"verified_on": "2020-01-01"},
        {"input_usd_per_million": "NaN"},
        {"output_usd_per_million": "-1"},
        {"cached_input_usd_per_million": "1"},
        {"source_url": "https://untrusted.invalid/prices"},
    ],
)
def test_pricing_snapshot_fails_closed(change, tmp_path):
    data = json.loads(Path("config/model_pricing.json").read_text())
    data.update(change)
    path = tmp_path / "pricing.json"
    path.write_text(json.dumps(data))
    with pytest.raises(PricingError):
        Pricing.load(path, MODEL, today=date(2026, 11, 3))


def test_reservation_is_conservative_and_ignores_cache(pricing):
    bound, reservation = pricing.reserve([{"role": "user", "content": "مرحبا"}], [], 512)
    assert bound >= len("مرحبا".encode())
    assert reservation == pricing.cost(Usage(bound, 512))
    with pytest.raises(PricingError):
        pricing.reserve([{"role": "user", "content": "x" * 64_001}], [], 512)


def test_reservation_uses_standard_rates_and_entire_completion_cap(pricing):
    bound, reserved = pricing.reserve([{"role": "user", "content": "Synthetic"}], [], 512)
    expected = (Decimal(bound) * Decimal("0.10") + Decimal(512) * Decimal("0.50")) / 1_000_000
    assert reserved == expected
    old_flex_estimate = (
        Decimal(bound) * Decimal("0.05") + Decimal(512) * Decimal("0.25")
    ) / 1_000_000
    assert reserved == old_flex_estimate * 2
    assert reserved > pricing.cost(Usage(bound, 512, bound))  # no speculative cache discount


def test_snapshot_date_uses_recorded_verification_timezone(monkeypatch, tmp_path):
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 2, 22, tzinfo=UTC).astimezone(tz)

    monkeypatch.setattr(pricing_module, "datetime", FrozenDateTime)
    assert Pricing.load("config/model_pricing.json", MODEL).input_rate == Decimal("0.10")
    snapshot = json.loads(Path("config/model_pricing.json").read_text())
    snapshot["verification_timezone"] = "UTC"
    path = tmp_path / "misdated.json"
    path.write_text(json.dumps(snapshot))
    with pytest.raises(PricingError):
        Pricing.load(path, MODEL)  # Still reject an actually future date in the declared zone.


@pytest.mark.parametrize(
    "overrides",
    [
        {"turns": 9},
        {"budget_usd": "0.051"},
        {"active_seconds": 61},
        {"tool_seconds": 11},
        {"max_output_tokens": 513},
    ],
)
def test_config_cannot_raise_approved_limits(overrides):
    with pytest.raises(ValueError):
        Limits(**overrides)


def test_openai_import_is_official():
    import openai

    root = Path(distribution("openai").locate_file("openai")).resolve()
    assert Path(openai.__file__).resolve().is_relative_to(root)
    assert not Path("src/openai").exists() and not Path("openai.py").exists()


def test_no_paid_execution_without_explicit_approval(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="approval"):
        OpenAIProvider.from_environment()
    with pytest.raises(ProviderError, match="credentials"):
        OpenAIProvider.from_environment(paid_approved=True)


async def test_sdk_hidden_retries_are_rejected():
    client = AsyncOpenAI(api_key="fixture-not-a-real-key", max_retries=2)
    try:
        with pytest.raises(ProviderError, match="retries"):
            OpenAIProvider(client, MODEL, mode="fixture")
    finally:
        await client.close()


async def test_completion_usage_includes_reasoning_without_double_counting(pricing, sdk_script):
    # Synthetic SDK response: 20 total completion tokens, 15 of them reasoning.
    # This validates accounting semantics, not live gpt-6-luna reasoning support.
    script = sdk_script(
        [
            completion(
                "Fixture answer",
                completion_tokens_details={
                    "reasoning_tokens": 15,
                },
            )
        ]
    )
    reply = await script.provider.complete(
        [{"role": "user", "content": "Synthetic request"}], [], 512
    )
    assert reply.usage.output_tokens == 20
    assert pricing.cost(reply.usage) == Decimal("0.000020")
    assert script.requests[0]["max_completion_tokens"] == 512


def test_trace_allowlist_and_redaction(tmp_path):
    trace = Trace(tmp_path, "a" * 32, "fixture")
    trace.emit("finished", status="completed", turns=1, cost_usd="0.00001")
    event = json.loads(trace.path.read_text())
    assert event["evidence"] == "provider_fixture"
    assert trace.path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError):
        trace.emit("tool", arguments={"private": "value"})
    with pytest.raises(ValueError):
        trace.emit("usage", cost_usd="not-a-price")
    with pytest.raises(ValueError):
        Trace(tmp_path / "traces", "b" * 32, "fixture")
    assert "someone@example.invalid" not in safe_text("Contact someone@example.invalid")
    assert "x" * 43 not in safe_text("token=" + "x" * 43)


def test_cli_retains_original_trusted_session_for_start_and_resume(store, tokens, monkeypatch):
    monkeypatch.setenv("CS_SESSION_TOKEN", tokens["demo-a"])
    for task in (None, "known-task-id"):
        assert (
            session_binding(store, SimpleNamespace(customer=None, resume_task=task))
            == tokens["demo-a"]
        )
    with store.db.connect() as conn:
        assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2


def test_cli_cannot_switch_identity_when_a_session_is_already_bound(store, tokens, monkeypatch):
    monkeypatch.setenv("CS_SESSION_TOKEN", tokens["demo-a"])
    with pytest.raises(ProviderError):
        session_binding(store, SimpleNamespace(customer="demo-b", resume_task=None))
