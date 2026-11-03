import json
from decimal import Decimal

import pytest

from tests.agent_support import completion
from yemen_customer_service.agent import smoke
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError


async def test_smoke_preflight_never_creates_client_or_live_artifacts(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.setattr(smoke, "DIRECTORY", tmp_path / "unclaimed")
    marker = "fixture-placeholder-do-not-print"
    monkeypatch.setenv("LLM_API_KEY", marker)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    def forbidden(**kwargs):
        pytest.fail("Preflight must not construct a paid provider")

    monkeypatch.setattr(OpenAIProvider, "from_environment", forbidden)
    assert await smoke.run(allow_paid=False, enable_demo_auth=False) is None
    output = capsys.readouterr().out
    assert marker not in output and "no API request made" in output
    assert not smoke.DIRECTORY.exists()


def test_one_attempt_interlock_is_persistent_and_private(tmp_path):
    smoke.claim_attempt(tmp_path)
    assert (tmp_path / "attempt.lock").stat().st_mode & 0o777 == 0o600
    with pytest.raises(ProviderError, match="already claimed"):
        smoke.claim_attempt(tmp_path)


def test_existing_database_is_not_overwritten(tmp_path):
    (tmp_path / "synthetic.sqlite3").write_text("existing artifact")
    with pytest.raises(ProviderError, match="Existing smoke database"):
        smoke.claim_attempt(tmp_path)
    assert not (tmp_path / "attempt.lock").exists()


@pytest.mark.parametrize(
    ("answer", "grounded"),
    [
        (
            "Example Headphones cost USD 25. Returns are allowed within 14 days "
            "with the original receipt.",
            True,
        ),
        ("Example Headphones cost USD 35. Returns take 60 days.", False),
    ],
)
async def test_smoke_verifier_rehearsal_real_mcp_and_fixture_provider(
    answer,
    grounded,
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script(
        [
            completion(calls=[("search_products", {"query": "headphones"})]),
            completion(calls=[("get_store_policies", {"topic": "returns"})]),
            completion(answer),
        ]
    )
    report = await smoke.execute(store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert report["question"] == smoke.QUESTION
    assert report["provider"] == "fixture" and report["evidence"] == "provider_fixture"
    assert report["automated_checks_passed"] is grounded, report["checks"]
    assert report["human_grounding_review_required"] is True
    assert report["billing_invoice_verified"] is False
    assert report["mcp_tools_called"] == ["search_products", "get_store_policies"]
    assert report["checks"]["actual_mcp_calls_match_transcript"]
    assert report["checks"]["usage_and_usd_reconciled"]
    assert report["llm_request_attempts"] == len(script.requests) == 3
    assert Decimal(report["computed_usd"]) == Decimal("0.000060")
    assert all(payload["messages"][1]["content"] == smoke.QUESTION for payload in script.requests)
    assert all(secret not in json.dumps(report) for secret in tokens.values())


async def test_smoke_missing_usage_is_unknown_not_fake_zero(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([completion("Unusable fixture answer", usage=False)])
    report = await smoke.execute(store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert report["status"] == "unknown_usage"
    assert report["computed_usd"] is None and not report["automated_checks_passed"]
    assert len(script.requests) == 1


async def test_smoke_does_not_confirm_an_unexpected_ticket_proposal(
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
                            "subject": "Unexpected synthetic ticket",
                            "message": "Not the catalog question",
                            "idempotency_key": "smoke-no-write",
                        },
                    )
                ]
            )
        ]
    )
    report = await smoke.execute(store, tokens["demo-a"], script.provider, pricing, tmp_path)
    assert report["status"] == "awaiting_confirmation" and not report["automated_checks_passed"]
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
