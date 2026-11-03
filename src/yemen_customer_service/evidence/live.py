"""Separately gated live trace runner. Default/preflight never creates a client.

No fixture imports, automatic reruns, official submission exports, or UI hooks.
"""

import argparse
import hashlib
import json
import logging
import os
import sqlite3
import subprocess
import sys
from contextlib import contextmanager
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

from mcp import StdioServerParameters

from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing, PricingError
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError
from yemen_customer_service.agent.smoke import price_anchor
from yemen_customer_service.agent.state import Journal, Limits
from yemen_customer_service.agent.tracing import FIELDS, Trace
from yemen_customer_service.evidence.ledger import SCENARIOS, Ledger, exclusive_plan
from yemen_customer_service.evidence.recovery import ReadRecoveryClient
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import TrustedClient, protocol_session
from yemen_customer_service.tool_server.models import OUTPUT_MODELS, SafeError

MODEL = "gpt-6-luna"
DIRECTORY = Path("artifacts/live_submission")
SUCCESS_HASH = "5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb"
QUESTION = "Use list_products to list products and give the USD price of Example Headphones."


@contextmanager
def quiet_provider():
    # Ancestor logger.disabled alone does not suppress descendant SDK loggers.
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


def configuration():
    if os.getenv("OPENAI_MODEL", MODEL) != MODEL:
        raise ProviderError("This runner requires gpt-6-luna; no fallback.")
    path = Path(os.getenv("MODEL_PRICING_FILE", "config/model_pricing.json"))
    raw = path.read_bytes()
    pricing = Pricing.load(path, MODEL)  # Real current-date freshness check; never fixed for live.
    data = json.loads(raw)
    if (
        pricing.version != f"{data['verified_on']}:standard:{hashlib.sha256(raw).hexdigest()[:16]}"
        or (pricing.input_rate, pricing.output_rate, pricing.cached_rate)
        != (Decimal("0.10"), Decimal("0.50"), Decimal("0.01"))
        or data.get("model_source_url")
        != "https://developers.openai.com/api/docs/models/gpt-6-luna"
        or data.get("compatibility")
        != "documented_chat_completions_tools_with_reasoning_none_live_account_unverified"
    ):
        raise PricingError("Re-review model compatibility and Standard pricing before execution.")
    if hashlib.sha256(Path("traces/success_1.jsonl").read_bytes()).hexdigest() != SUCCESS_HASH:
        raise ProviderError("Existing success evidence changed; stop for review.")
    return pricing, raw


def preflight(root=DIRECTORY):
    """Pure local read-only check. No credential values, SDK objects or new files."""
    pricing, _ = configuration()
    if "traces" in root.absolute().parts or any(p.is_symlink() for p in [root, *root.parents]):
        raise ProviderError("Unsafe evidence directory.")
    summary = {
        "mode": "PREPARED_ONLY_NO_REQUEST",
        "model": MODEL,
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "service_tier": "default",
        "reasoning_effort": "none",
        "pricing_version": pricing.version,
        "compatibility_source": "dated_user_verified_official_excerpt",
        "live_availability_and_billing": "NOT_CHECKED",
        "credential_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")),
        "max_tasks": 2,
        "max_model_attempts": 9,
        "estimated_plan_usd": "0.10",
        "scenario_locks_present": [s for s in SCENARIOS if (root / s).exists()],
    }
    ledger_path = root / "plan.sqlite3"
    if ledger_path.is_symlink():
        raise ProviderError("Unsafe ledger path.")
    if ledger_path.exists():
        with sqlite3.connect(ledger_path.resolve().as_uri() + "?mode=ro", uri=True) as c:
            c.execute("PRAGMA query_only=ON")
            summary["prior_attempts"] = c.execute("SELECT scenario,status FROM runs").fetchall()
    return summary


def source_revision():
    """Paid evidence must identify reviewed, committed source, not a dirty tree."""
    if subprocess.check_output(
        ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
    ).strip():
        raise ProviderError("Working tree must be clean before paid execution.")
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
    ).strip()


def create_attempt(root, scenario):
    # A directory left by an interrupted claim is also an interlock, not something to clear.
    directory = root / scenario
    try:
        directory.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError:
        raise ProviderError("Scenario already claimed; never reset its attempt lock.") from None
    fd = os.open(
        directory / "attempt.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(fd, "w") as f:
        f.write("One scenario attempt claimed. Preserve this lock even after failure.\n")
        f.flush()
        os.fsync(f.fileno())
    return directory


class BoundedProvider:
    """Second, durable gate immediately before each SDK request; no SDK retries."""

    def __init__(self, provider, ledger, scenario, pricing):
        self.provider, self.ledger, self.scenario, self.pricing = (
            provider,
            ledger,
            scenario,
            pricing,
        )
        self.model, self.mode = provider.model, provider.mode

    async def complete(self, messages, tools, max_output):
        bound, amount = self.pricing.reserve(messages, tools, max_output)
        call_id = self.ledger.reserve(self.scenario, amount)
        try:
            reply = await self.provider.complete(messages, tools, max_output)
        except BaseException:
            self.ledger.reconcile(call_id, self.pricing, None, bound=bound, max_output=max_output)
            raise
        self.ledger.reconcile(
            call_id, self.pricing, reply.usage, bound=bound, max_output=max_output
        )
        return reply


class CatalogOnlyClient(ReadRecoveryClient):
    """Both scenarios permit only the selected public read; never private reads/writes."""

    def __init__(self, *args, recover, **kwargs):
        super().__init__(*args, **kwargs)
        self.recover = recover

    async def invoke(self, name, arguments):
        if name != "list_products":
            raise SafeError("ACCESS_DENIED")
        if self.recover:
            return await super().invoke(name, arguments)
        return await TrustedClient.invoke(self, name, arguments)


async def execute_case(directory, scenario, provider, pricing, ledger):
    """Shared actual execution. Tests pass fixture-mode providers, labeled as such.

    CLI cannot select/inject fixtures. This function never promotes trace files.
    """
    database = Database(directory / "synthetic.sqlite3")
    database.initialize(seed_demo=True)
    store = Store(database)
    token = store.provision_demo_session("demo-a", enable_demo_auth=True, app_env="development")
    journal = Journal(store, token)
    with database.connect() as c:
        task_id = store.session(c, token)["task_id"]
    trace = Trace(directory / "events", task_id, provider.mode)
    recovery = scenario == "near_failure_recovery"
    limits = Limits(turns=SCENARIOS[scenario])
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "yemen_customer_service.evidence.fault_server"]
        if recovery
        else ["-m", "yemen_customer_service.tool_server.server"],
        env={
            "DATABASE_PATH": str(database.path.resolve()),
            "CS_SESSION_TOKEN": token,
            "APP_ENV": "development",
            "ENABLE_DEMO_AUTH": "true",
            "SCENARIO_FAULT": "once",
        },
    )
    async with protocol_session(parameters) as session:
        discovered = await session.list_tools()
        client = CatalogOnlyClient(session, store, token, journal, trace, recover=recovery)
        bounded = BoundedProvider(provider, ledger, scenario, pricing)
        outcome = await Agent(
            client, journal, bounded, pricing, limits=limits, trace_directory=directory / "events"
        ).start(QUESTION)
    state = journal.load(task_id)
    events = [json.loads(line) for line in trace.path.read_text().splitlines()]
    with database.connect() as c:
        audits = [
            dict(r)
            for r in c.execute(
                "SELECT tool,outcome,result_code FROM audits WHERE task_id=? ORDER BY id",
                (task_id,),
            )
        ]
        records = [
            dict(r)
            for r in c.execute("SELECT * FROM cost_records WHERE task_id=? ORDER BY id", (task_id,))
        ]
        snapshots = [
            json.loads(
                c.execute(
                    "SELECT value FROM metadata WHERE key=?", (f"agent_cost:{r['id']}",)
                ).fetchone()[0]
            )
            for r in records
        ]
        task = c.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        no_writes = c.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        no_consent = c.execute("SELECT count(*) FROM confirmations").fetchone()[0] == 0
        one_task = c.execute("SELECT count(*) FROM tasks").fetchone()[0] == 1
    plan_calls = ledger.rows(scenario)
    usage = [e for e in events if e["event"] == "usage"]
    reserved = [e for e in events if e["event"] == "reserved"]
    known = bool(records) and all(r["status"] == "recorded" for r in records)
    total = sum((Decimal(r["cost_usd"]) for r in records), Decimal(0)) if known else None
    # Grounding uses actual received tool data, never only the model's claim.
    grounded = False
    if state.last_result and state.last_result["tool"] == "list_products":
        for p in state.last_result["data"]["products"]:
            if p["name"] == "Example Headphones" and p["currency"] == "USD":
                grounded = p["name"] in state.answer and price_anchor(p["price"], state.answer)
    expected_audits = (
        [
            ("list_products", "deny", "INTERNAL_ERROR"),
            ("list_products", "allow", "OK"),
            ("agent", "allow", "COMPLETED"),
        ]
        if recovery
        else [("list_products", "allow", "OK"), ("agent", "deny", "TURN_LIMIT")]
    )
    expected_status = "completed" if recovery else "turn_limit"
    expected_evidence = "live_openai" if provider.mode == "openai" else "provider_fixture"
    fields = FIELDS | {"schema_version", "task_id", "provider", "timestamp", "evidence", "event"}
    checks = {
        "discovery": {t.name for t in discovered.tools} == set(OUTPUT_MODELS),
        "one_task_and_labels": one_task
        and all(
            e["task_id"] == task_id
            and e["provider"] == provider.mode
            and e["evidence"] == expected_evidence
            for e in events
        ),
        "terminal": state.status
        == outcome.status
        == task["status"]
        == events[-1]["status"]
        == expected_status
        and events[-1]["event"] == "finished",
        "ordered": [e["timestamp"] for e in events] == sorted(e["timestamp"] for e in events)
        and events[0]["event"] == "started",
        "audit_sequence": [(r["tool"], r["outcome"], r["result_code"]) for r in audits]
        == expected_audits,
        "no_writes": no_writes and no_consent,
        "limits": state.limits == limits
        and 0 < state.turns <= SCENARIOS[scenario]
        and state.active_seconds == outcome.active_seconds <= 60
        and state.held_usd <= Decimal("0.05")
        and not state.running,
        "request_count": len(records)
        == len(plan_calls)
        == len(usage)
        == len(reserved)
        == state.turns
        and [e["turns"] for e in usage] == list(range(1, state.turns + 1)),
        "accounting": known
        and not state.unknown_cost
        and total == state.held_usd == Decimal(events[-1]["cost_usd"])
        and all(
            r["status"] == p["status"] == "recorded"
            and r["provider"] == provider.mode
            and r["model"] == MODEL
            and r["pricing_version"] == pricing.version
            and r["input_tokens"] == p["input_tokens"] == u["input_tokens"]
            and r["output_tokens"] == p["output_tokens"] == u["output_tokens"]
            and s["cached_input_tokens"] == p["cached_tokens"] == u.get("cached_input_tokens")
            and Decimal(r["cost_usd"]) == Decimal(p["cost"]) == Decimal(u["cost_usd"])
            for r, p, u, s in zip(records, plan_calls, usage, snapshots, strict=True)
        ),
        "tool_sequence": [e["status"] for e in events if e["event"] == "tool"]
        == (["error", "retrying", "success"] if recovery else ["success"]),
        "answer": grounded
        if recovery
        else "TURN_LIMIT" in outcome.answer and "incomplete" in outcome.answer and state.turns == 1,
        "trace_safe": all(set(e) <= fields for e in events),
        "success_unchanged": hashlib.sha256(Path("traces/success_1.jsonl").read_bytes()).hexdigest()
        == SUCCESS_HASH,
    }
    return {
        "scenario": scenario,
        "task_id": task_id,
        "provider": provider.mode,
        "evidence": expected_evidence,
        "status": outcome.status,
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "model": MODEL,
        "endpoint": "chat_completions",
        "reasoning_effort": "none",
        "requested_service_tier": "default",
        "pricing_version": pricing.version,
        "model_requests": len(plan_calls),
        "computed_usd": str(total) if total is not None else None,
        "usage_records": [
            {
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cached_input_tokens": s["cached_input_tokens"],
                "computed_usd": r["cost_usd"],
                "status": r["status"],
            }
            for r, s in zip(records, snapshots, strict=True)
        ],
        "active_seconds": outcome.active_seconds,
        "audit_records": audits,
        "trace_sha256": hashlib.sha256(trace.path.read_bytes()).hexdigest(),
        "human_grounding_review_required": True,
        "billing_invoice_verified": False,
        "controlled_fault": "one_disclosed_SQLite_catalog_read_fault" if recovery else None,
        "recovery_policy": "harness_only_single_read_retry" if recovery else None,
        "constraint": "one_model_request" if not recovery else "standard_task_limits",
    }


async def run(
    scenario,
    *,
    allow_paid=False,
    approve_plan=False,
    enable_demo_auth=False,
    preflight_only=False,
    root=DIRECTORY,
):
    if scenario not in SCENARIOS:
        raise ProviderError("Unknown scenario.")
    if preflight_only or not allow_paid:
        return preflight(root)
    if (
        not approve_plan
        or not enable_demo_auth
        or os.getenv("APP_ENV", "development") != "development"
    ):
        raise ProviderError(
            "Live execution requires all three explicit flags and development mode."
        )
    pricing, raw = configuration()
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")):
        raise ProviderError("Credential not configured. No request made.")
    commit = source_revision()
    # Avoid SDK/body/header debug logging regardless of inherited operator settings.
    os.environ.pop("OPENAI_LOG", None)
    with exclusive_plan(root), quiet_provider():
        ledger = Ledger(root, pricing.version, "openai")
        directory = create_attempt(root, scenario)
        provider = None
        report = {
            "scenario": scenario,
            "requested_provider": "openai",
            "provider": "not_started",
            "evidence": "no_provider_execution",
            "result": "FAIL",
            "error": "ATTEMPT_INCOMPLETE",
            "billing_invoice_verified": False,
        }
        claimed = False
        try:
            ledger.claim(scenario)
            claimed = True
            with (directory / "model_pricing.json").open("xb") as f:
                f.write(raw)
            provider = OpenAIProvider.from_environment(paid_approved=True)
            if (
                provider.mode != "openai"
                or provider.model != MODEL
                or str(provider.client.base_url) != "https://api.openai.com/v1/"
            ):
                raise ProviderError("Live provider identity rejected.")
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("LLM_API_KEY", None)
            report.update(provider="openai", evidence="live_openai_attempt")
            report = await execute_case(directory, scenario, provider, pricing, ledger)
            report["source_commit"] = commit
            report["versions"] = {
                "python": sys.version.split()[0],
                "openai": version("openai"),
                "mcp": version("mcp"),
            }
        except BaseException:
            report["result"] = "FAIL"
            report["error"] = "RUNNER_STOPPED_REVIEW_REQUIRED"
        finally:
            if provider is not None:
                try:
                    await provider.client.close()
                except Exception:
                    report["result"] = "FAIL"
                    report["error"] = "PROVIDER_CLOSE_FAILED"
            if claimed:
                try:
                    passed = ledger.finish(scenario, report["result"] == "PASS")
                except Exception:
                    passed = False
                    report["error"] = "LEDGER_FINALIZE_FAILED"
                if not passed:
                    report["result"] = "FAIL"
            with (directory / "report.openai.json").open("x") as f:
                json.dump(report, f, indent=2, allow_nan=False)
                f.write("\n")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument(
        "--approve-plan",
        action="store_true",
        help="Approve at most two tasks, nine requests and USD 0.10 estimated",
    )
    parser.add_argument("--enable-demo-auth", action="store_true")
    args = parser.parse_args()
    try:
        import asyncio

        report = asyncio.run(
            run(
                args.scenario,
                allow_paid=args.allow_paid,
                approve_plan=args.approve_plan,
                enable_demo_auth=args.enable_demo_auth,
                preflight_only=args.preflight,
            )
        )
    except Exception:
        print("STOPPED: local configuration or evidence check failed. No automatic retry.")
        raise SystemExit(1) from None
    if report.get("mode") == "PREPARED_ONLY_NO_REQUEST":
        print(json.dumps(report, indent=2))
    else:
        print(
            json.dumps(
                {
                    k: report.get(k)
                    for k in ("scenario", "result", "status", "model_requests", "computed_usd")
                }
            )
        )
        if report["result"] != "PASS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
