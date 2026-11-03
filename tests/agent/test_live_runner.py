"""Offline tests only: deterministic SDK fixtures; real MCP; never live OpenAI."""

import hashlib
import json
import logging
import os
import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from tests.agent_support import completion
from yemen_customer_service.agent.pricing import PricingError, Usage
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError
from yemen_customer_service.evidence import live
from yemen_customer_service.evidence.ledger import Ledger, exclusive_plan
from yemen_customer_service.tool_server.models import SafeError


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def case_root():
    base = Path(os.getenv("LIVE_RUNNER_TEST_EVIDENCE", "artifacts/phase5-live-runner-tests/cases"))
    root = base / uuid.uuid4().hex
    root.mkdir(mode=0o700, parents=True)
    return root


async def test_preflight_is_readonly_even_with_paid_flags(tmp_path, monkeypatch, capsys):
    marker = "fixture-sensitive-marker-not-a-real-key"
    monkeypatch.setenv("LLM_API_KEY", marker)
    monkeypatch.setattr(
        OpenAIProvider, "from_environment", lambda **kw: pytest.fail("Paid factory")
    )
    root = tmp_path / "not-created"
    report = await live.run(
        "near_failure_recovery",
        allow_paid=True,
        approve_plan=True,
        enable_demo_auth=True,
        preflight_only=True,
        root=root,
    )
    print(json.dumps(report))
    assert marker not in capsys.readouterr().out
    assert report["mode"] == "PREPARED_ONLY_NO_REQUEST"
    assert not root.exists()


@pytest.mark.parametrize(
    "flags",
    [
        {},
        {"approve_plan": True},
        {"enable_demo_auth": True},
        {"approve_plan": True, "enable_demo_auth": True},
        {"allow_paid": True},
        {"allow_paid": True, "approve_plan": True},
        {"allow_paid": True, "enable_demo_auth": True},
    ],
)
async def test_every_missing_gate_prevents_provider(tmp_path, monkeypatch, flags):
    monkeypatch.setattr(
        OpenAIProvider, "from_environment", lambda **kw: pytest.fail("Paid factory")
    )
    root = tmp_path / "unclaimed"
    if flags.get("allow_paid"):
        with pytest.raises(ProviderError):
            await live.run("explicit_failure", root=root, **flags)
    else:
        assert (await live.run("explicit_failure", root=root, **flags))["mode"].startswith(
            "PREPARED"
        )
    assert not root.exists()


@pytest.mark.parametrize("problem", ["missing_key", "production", "dirty_tree"])
async def test_execution_prerequisites_fail_before_claim(tmp_path, monkeypatch, problem):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setattr(
        OpenAIProvider, "from_environment", lambda **kw: pytest.fail("Paid factory")
    )
    if problem != "missing_key":
        monkeypatch.setenv("LLM_API_KEY", "fixture-not-a-real-key")
    if problem == "production":
        monkeypatch.setenv("APP_ENV", "production")
    if problem == "dirty_tree":

        def dirty():
            raise ProviderError("Dirty source")

        monkeypatch.setattr(live, "source_revision", dirty)
    with pytest.raises(ProviderError):
        await live.run(
            "explicit_failure",
            allow_paid=True,
            approve_plan=True,
            enable_demo_auth=True,
            root=tmp_path / "not-created",
        )
    assert not (tmp_path / "not-created").exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("verified_on", "2000-01-01"),
        ("verified_on", "2099-01-01"),
        ("tier", "flex"),
        ("model", "another-model"),
        ("input_usd_per_million", "0.05"),
        ("compatibility", "unknown"),
        ("model_source_url", "https://invalid.example"),
    ],
)
def test_stale_unknown_or_mismatched_configuration_rejected(tmp_path, monkeypatch, key, value):
    raw = json.loads(live.Path("config/model_pricing.json").read_text())
    raw[key] = value
    path = tmp_path / "pricing.json"
    path.write_text(json.dumps(raw))
    monkeypatch.setenv("MODEL_PRICING_FILE", str(path))
    with pytest.raises((PricingError, ProviderError)):
        live.configuration()


def test_provider_model_cannot_be_substituted(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "another-model")
    with pytest.raises(ProviderError):
        live.configuration()


def test_attempts_are_exclusive_and_original_files_never_overwritten(tmp_path):
    root = tmp_path / "plan"
    with exclusive_plan(root):
        with pytest.raises(ProviderError, match="active"):
            with exclusive_plan(root):
                pytest.fail("Concurrent plan acquired")
        directory = live.create_attempt(root, "explicit_failure")
        lock = directory / "attempt.lock"
        original = digest(lock)
        (directory / "report.openai.json").write_text("original evidence")
        with pytest.raises(ProviderError, match="already claimed"):
            live.create_attempt(root, "explicit_failure")
        assert digest(lock) == original
        assert lock.stat().st_mode & 0o777 == 0o600
        assert (directory / "report.openai.json").read_text() == "original evidence"


def test_plan_protects_symlinks_and_submission_paths(tmp_path):
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    for root in [link / "plan", tmp_path / "traces"]:
        with pytest.raises(ProviderError):
            with exclusive_plan(root):
                pytest.fail("Unsafe output allowed")


def record(ledger, scenario, pricing, *, usage=None, reservation=Decimal("0.001")):
    ident = ledger.reserve(scenario, reservation)
    usage = usage or Usage(100, 20, 0)
    ledger.reconcile(ident, pricing, usage, bound=1_000_000, max_output=512)


def test_durable_caps_two_tasks_nine_requests_and_no_retries(tmp_path, pricing):
    with exclusive_plan(tmp_path):
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        ledger.claim("near_failure_recovery")
        for _ in range(8):
            record(ledger, "near_failure_recovery", pricing)
        with pytest.raises(ProviderError):
            ledger.reserve("near_failure_recovery", Decimal("0.001"))
        assert ledger.finish("near_failure_recovery", True)
    with exclusive_plan(tmp_path):
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        ledger.claim("explicit_failure")
        record(ledger, "explicit_failure", pricing)
        with pytest.raises(ProviderError):
            ledger.reserve("explicit_failure", Decimal("0.001"))
        assert ledger.finish("explicit_failure", True)
        assert len(ledger.rows("near_failure_recovery")) + len(ledger.rows("explicit_failure")) == 9
        for scenario in ("near_failure_recovery", "explicit_failure"):
            with pytest.raises(ProviderError):
                ledger.claim(scenario)


def test_reservations_and_spending_caps_are_conservative(tmp_path, pricing):
    with exclusive_plan(tmp_path):
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        ledger.claim("near_failure_recovery")
        with pytest.raises(ProviderError):
            ledger.reserve("near_failure_recovery", Decimal("0.050001"))
        record(
            ledger,
            "near_failure_recovery",
            pricing,
            usage=Usage(500_000, 0, 0),
            reservation=Decimal("0.05"),
        )
        with pytest.raises(ProviderError):
            ledger.reserve("near_failure_recovery", Decimal("0.000001"))
        assert ledger.finish("near_failure_recovery", True)
        ledger.claim("explicit_failure")
        record(
            ledger,
            "explicit_failure",
            pricing,
            usage=Usage(500_000, 0, 0),
            reservation=Decimal("0.05"),
        )
        total = sum(
            Decimal(r["cost"])
            for s in ("near_failure_recovery", "explicit_failure")
            for r in ledger.rows(s)
        )
        assert total == Decimal("0.10")


@pytest.mark.parametrize("unknown", [True, False])
def test_unknown_usage_or_safety_failure_blocks_other_scenario(tmp_path, pricing, unknown):
    with exclusive_plan(tmp_path):
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        ledger.claim("near_failure_recovery")
        if unknown:
            ident = ledger.reserve("near_failure_recovery", Decimal("0.001"))
            ledger.reconcile(ident, pricing, None, bound=20000, max_output=512)
            assert ledger.rows("near_failure_recovery")[0]["cost"] is None
        else:
            record(ledger, "near_failure_recovery", pricing)
        assert not ledger.finish("near_failure_recovery", False)
    with exclusive_plan(tmp_path):
        reopened = Ledger(tmp_path, pricing.version, "fixture")
        with pytest.raises(ProviderError):
            reopened.claim("explicit_failure")


def test_inflight_or_fixture_plan_cannot_be_reused_as_live(tmp_path, pricing):
    with exclusive_plan(tmp_path):
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        ledger.claim("near_failure_recovery")
        ledger.reserve("near_failure_recovery", Decimal("0.001"))
    with exclusive_plan(tmp_path):
        with pytest.raises(ProviderError):
            Ledger(tmp_path, pricing.version, "openai")
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        with pytest.raises(ProviderError):
            ledger.claim("explicit_failure")
        with pytest.raises(ProviderError):
            ledger.reserve("near_failure_recovery", Decimal("0.001"))


@pytest.mark.parametrize("scenario", ["near_failure_recovery", "explicit_failure"])
async def test_same_runner_execution_with_sdk_fixture_and_genuine_mcp(
    case_root, pricing, sdk_script, scenario
):
    actions = [completion(calls=[("list_products", {})])]
    if scenario == "near_failure_recovery":
        actions.append(completion("Example Headphones cost USD 25.00."))
    script = sdk_script(actions)
    with exclusive_plan(case_root):
        ledger = Ledger(case_root, pricing.version, "fixture")
        ledger.claim(scenario)
        directory = live.create_attempt(case_root, scenario)
        report = await live.execute_case(directory, scenario, script.provider, pricing, ledger)
        (directory / "report.fixture.json").write_text(json.dumps(report, indent=2) + "\n")
        assert report["result"] == "PASS", report["checks"]
        assert report["evidence"] == "provider_fixture"
        assert ledger.finish(scenario, True)
        assert len(script.requests) == (2 if scenario == "near_failure_recovery" else 1)
        assert not list(directory.glob("*.openai.json"))
        assert not list((directory / "events").glob("*.openai.jsonl"))


@pytest.mark.parametrize(
    "action,expected",
    [
        (completion("No usage", usage=False), "unknown_usage"),
        (completion("Headphones cost USD 99"), "completed"),
        (
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Unexpected ticket",
                            "message": "Never confirm this",
                            "idempotency_key": "live-guard-no-write",
                        },
                    )
                ]
            ),
            "awaiting_confirmation",
        ),
    ],
)
async def test_unqualified_or_unknown_run_blocks_plan(
    case_root, pricing, sdk_script, action, expected
):
    script = sdk_script([action])
    with exclusive_plan(case_root):
        ledger = Ledger(case_root, pricing.version, "fixture")
        ledger.claim("near_failure_recovery")
        directory = live.create_attempt(case_root, "near_failure_recovery")
        report = await live.execute_case(
            directory, "near_failure_recovery", script.provider, pricing, ledger
        )
        (directory / "report.fixture.json").write_text(json.dumps(report, indent=2) + "\n")
        assert report["result"] == "FAIL"
        assert report["status"] == expected
        assert report["checks"]["no_writes"]
        assert len(script.requests) == 1
        assert not ledger.finish("near_failure_recovery", False)
        with pytest.raises(ProviderError):
            ledger.claim("explicit_failure")


async def test_live_gate_rejects_fixture_factory_and_retains_lock(
    tmp_path, monkeypatch, sdk_script
):
    script = sdk_script([])
    monkeypatch.setenv("LLM_API_KEY", "fixture-not-a-real-key")
    monkeypatch.setattr(live, "source_revision", lambda: "offline-test-source")
    monkeypatch.setattr(OpenAIProvider, "from_environment", lambda **kw: script.provider)
    root = tmp_path / "plan"
    report = await live.run(
        "near_failure_recovery",
        allow_paid=True,
        approve_plan=True,
        enable_demo_auth=True,
        root=root,
    )
    assert report["result"] == "FAIL" and not script.requests
    lock = root / "near_failure_recovery/attempt.lock"
    before = digest(lock)
    with pytest.raises(ProviderError):
        await live.run(
            "near_failure_recovery",
            allow_paid=True,
            approve_plan=True,
            enable_demo_auth=True,
            root=root,
        )
    assert digest(lock) == before
    assert (root / "near_failure_recovery/report.openai.json").is_file()
    assert report["evidence"] == "no_provider_execution"


@pytest.mark.parametrize(
    "answer,expected",
    [
        ("USD 25.00.", True),
        ("$25.00 USD", True),
        ("USD 25.", True),
        ("USD 250", False),
        ("USD 25.50", False),
        ("USD 99", False),
    ],
)
def test_grounding_price_boundary(answer, expected):
    assert live.price_anchor("25.00", answer) is expected


@pytest.mark.parametrize(
    "name", ["create_support_ticket", "verify_order_access", "get_order_status"]
)
async def test_scenario_client_never_dispatches_writes_or_private_reads(name, monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("Forbidden operation reached MCP")

    monkeypatch.setattr(live.TrustedClient, "invoke", forbidden)
    client = live.CatalogOnlyClient(None, None, None, None, None, recover=True)
    with pytest.raises(SafeError, match="Access denied"):
        await client.invoke(name, {})


@pytest.mark.parametrize(
    "action",
    [
        completion("done"),
        completion("unknown", usage=False),
        completion("oversized usage", prompt_tokens=900_000),
    ],
)
async def test_durable_provider_gate_blocks_extra_requests_before_sdk(
    tmp_path, pricing, sdk_script, action
):
    script = sdk_script([action])
    with exclusive_plan(tmp_path):
        ledger = Ledger(tmp_path, pricing.version, "fixture")
        ledger.claim("explicit_failure")
        provider = live.BoundedProvider(script.provider, ledger, "explicit_failure", pricing)
        await provider.complete([{"role": "user", "content": "fixture"}], [], 512)
        with pytest.raises(ProviderError):
            await provider.complete([{"role": "user", "content": "fixture"}], [], 512)
        assert len(script.requests) == 1
        row = ledger.rows("explicit_failure")[0]
        if "usage" not in action:
            assert row["cost"] is None and row["status"] == "unknown"
        elif action["usage"]["prompt_tokens"] > 100:
            assert row["status"] == "recorded" and Decimal(row["cost"]) > Decimal("0.05")
            assert not ledger.finish("explicit_failure", True)


async def test_sdk_descendant_logging_and_constructor_errors_are_redacted(
    tmp_path, monkeypatch, caplog, capsys
):
    marker = "fixture-private-marker-never-display"
    monkeypatch.setenv("LLM_API_KEY", marker)
    monkeypatch.setattr(live, "source_revision", lambda: "offline-test-source")
    before = logging.root.manager.disable

    def forbidden_factory(**kwargs):
        logging.getLogger("openai._base_client").error(marker)
        raise ProviderError(marker)

    monkeypatch.setattr(OpenAIProvider, "from_environment", forbidden_factory)
    report = await live.run(
        "explicit_failure",
        allow_paid=True,
        approve_plan=True,
        enable_demo_auth=True,
        root=tmp_path / "plan",
    )
    saved = (tmp_path / "plan/explicit_failure/report.openai.json").read_text()
    assert report["result"] == "FAIL"
    assert marker not in saved + caplog.text + capsys.readouterr().out
    assert logging.root.manager.disable == before
