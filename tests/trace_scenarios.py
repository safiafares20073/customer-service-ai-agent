"""Offline-only trace rehearsals. SDK fixtures + genuine MCP, never live calls.

Run: python -m tests.trace_scenarios
Every attempt receives a unique ignored evidence directory, including failures.
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from mcp import StdioServerParameters

from tests.agent_support import MODEL, SDKScript, completion
from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing
from yemen_customer_service.agent.state import Journal, Limits
from yemen_customer_service.agent.tracing import Trace
from yemen_customer_service.evidence.recovery import ReadRecoveryClient
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import TrustedClient, protocol_session

SUCCESS_HASH = "5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb"


async def run_scenario(root: Path, scenario: str, *, fault="once", tool_seconds=10):
    if scenario not in {"near_failure_recovery", "explicit_failure"}:
        raise ValueError("Unknown scenario")
    # Refuse fixture output in any official submission directory, even if renamed.
    if "traces" in root.resolve().parts:
        raise ValueError("Fixture evidence cannot be submission evidence")
    directory = root / f"{scenario}-{uuid.uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {
        "scenario": scenario,
        "provider": "fixture",
        "evidence": "provider_fixture",
        "transport": "official_mcp_stdio",
        "fixture_usage_not_billed": True,
        "result": "FAIL",
        "checks": {},
    }
    script = None
    try:
        db = Database(directory / "synthetic.sqlite3")
        db.initialize(seed_demo=True)
        store = Store(db)
        token = store.provision_demo_session("demo-a", enable_demo_auth=True, app_env="development")
        journal = Journal(store, token)
        with db.connect() as conn:
            task_id = store.session(conn, token)["task_id"]
        report["task_id"] = task_id
        trace = Trace(directory / "events", task_id, "fixture")
        pricing = Pricing.load("config/model_pricing.json", MODEL, today=date(2026, 11, 3))
        final = "Example Headphones cost USD 25.00."
        script = SDKScript(
            [completion(calls=[("list_products", {})]), completion(final)]
            if scenario == "near_failure_recovery"
            else [completion(calls=[("list_products", {})])]
        )
        limits = Limits(
            turns=8 if scenario == "near_failure_recovery" else 1, tool_seconds=tool_seconds
        )
        env = {
            "DATABASE_PATH": str(db.path.resolve()),
            "CS_SESSION_TOKEN": token,
            "APP_ENV": "development",
            "ENABLE_DEMO_AUTH": "true",
            "SCENARIO_FAULT": fault,
        }
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "tests.fault_mcp_server"]
            if scenario == "near_failure_recovery"
            else ["-m", "yemen_customer_service.tool_server.server"],
            env=env,
        )
        async with protocol_session(parameters) as session:
            report["discovered_tools"] = [t.name for t in (await session.list_tools()).tools]
            client = (
                ReadRecoveryClient(session, store, token, journal, trace)
                if scenario == "near_failure_recovery"
                else TrustedClient(session, store, token)
            )
            outcome = await Agent(
                client,
                journal,
                script.provider,
                pricing,
                limits=limits,
                trace_directory=directory / "events",
            ).start("List products and give the price of Example Headphones.")
        state = journal.load(task_id)
        events = [json.loads(line) for line in trace.path.read_text().splitlines()]
        with db.connect() as conn:
            audits = [
                dict(row)
                for row in conn.execute(
                    "SELECT tool,outcome,result_code FROM audits WHERE task_id=? ORDER BY id",
                    (task_id,),
                )
            ]
            costs = [
                dict(row)
                for row in conn.execute(
                    "SELECT id,provider,model,input_tokens,output_tokens,cost_usd,status "
                    "FROM cost_records WHERE task_id=? ORDER BY id",
                    (task_id,),
                )
            ]
            task = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            tickets = conn.execute("SELECT count(*) FROM tickets").fetchone()[0]
            confirmations = conn.execute("SELECT count(*) FROM confirmations").fetchone()[0]
            snapshots = [
                json.loads(
                    conn.execute(
                        "SELECT value FROM metadata WHERE key=?",
                        (f"agent_cost:{c['id']}",),
                    ).fetchone()[0]
                )
                for c in costs
            ]
        recovered = scenario == "near_failure_recovery"
        expected_status, turns = ("completed", 2) if recovered else ("turn_limit", 1)
        expected_events = (
            [
                "started",
                "reserved",
                "usage",
                "tool",
                "tool",
                "tool",
                "reserved",
                "usage",
                "finished",
            ]
            if recovered
            else ["started", "reserved", "usage", "tool", "finished"]
        )
        expected_audits = (
            [
                ("list_products", "deny", "INTERNAL_ERROR"),
                ("list_products", "allow", "OK"),
                ("agent", "allow", "COMPLETED"),
            ]
            if recovered
            else [("list_products", "allow", "OK"), ("agent", "deny", "TURN_LIMIT")]
        )
        usage = [e for e in events if e["event"] == "usage"]
        total = sum((Decimal(c["cost_usd"]) for c in costs), Decimal(0))
        checks = {
            "same_task": all(e["task_id"] == task_id for e in events)
            and state.task_id == outcome.task_id == task["task_id"],
            "fixture_labels": all(
                e["provider"] == "fixture" and e["evidence"] == "provider_fixture" for e in events
            ),
            "event_sequence": [e["event"] for e in events] == expected_events,
            "timestamp_order": [datetime.fromisoformat(e["timestamp"]) for e in events]
            == sorted(datetime.fromisoformat(e["timestamp"]) for e in events),
            "terminal_outcome": outcome.status
            == state.status
            == task["status"]
            == events[-1]["status"]
            == expected_status,
            "request_count": len(script.requests)
            == outcome.turns
            == state.turns
            == len(costs)
            == len(usage)
            == turns,
            "audit_sequence": [(a["tool"], a["outcome"], a["result_code"]) for a in audits]
            == expected_audits,
            "limits_retained": state.limits == limits
            and state.active_seconds > 0
            and state.active_seconds == events[-1]["active_seconds"] <= 60
            and state.held_usd == total <= limits.budget_usd,
            "usage_cost_reconciliation": total
            == Decimal(events[-1]["cost_usd"])
            == Decimal(outcome.estimated_or_recorded_usd)
            and all(
                c["provider"] == "fixture"
                and c["status"] == "recorded"
                and c["model"] == MODEL
                and c["input_tokens"] == u["input_tokens"]
                and c["output_tokens"] == u["output_tokens"]
                and Decimal(c["cost_usd"])
                == pricing.cost(
                    # Usage counts here are scripted, not provider measurements.
                    script_usage(u)
                )
                for c, u in zip(costs, usage, strict=True)
            )
            and all(s["usage_source"] == "fixture" for s in snapshots),
            "no_writes_or_consent": tickets == confirmations == 0,
            "discovery": len(report["discovered_tools"]) == 7,
            "answer": outcome.answer == final
            if recovered
            else "TURN_LIMIT" in outcome.answer and "incomplete" in outcome.answer,
            "success_trace_unchanged": hashlib.sha256(
                Path("traces/success_1.jsonl").read_bytes()
            ).hexdigest()
            == SUCCESS_HASH,
        }
        if recovered:
            checks["real_fault_then_retry"] = [
                e["status"] for e in events if e["event"] == "tool"
            ] == ["error", "retrying", "success"]
            checks["grounded"] = bool(state.last_result) and any(
                p["name"] == "Example Headphones" and p["price"] == "25.00"
                for p in state.last_result["data"]["products"]
            )
        report.update(
            checks=checks,
            status=outcome.status,
            turns=outcome.turns,
            active_seconds=outcome.active_seconds,
            fixture_computed_usd=str(total),
            input_tokens=sum(c["input_tokens"] for c in costs),
            output_tokens=sum(c["output_tokens"] for c in costs),
            audit_records=audits,
            trace_sha256=hashlib.sha256(trace.path.read_bytes()).hexdigest(),
        )
        report["result"] = "PASS" if all(checks.values()) else "FAIL"
    except BaseException:
        report["error"] = "HARNESS_EXCEPTION"  # Never persist raw exception text/secrets.
        raise
    finally:
        with (directory / "report.json").open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
        if script is not None:
            await script.close()
    return directory, report


def script_usage(event):
    from yemen_customer_service.agent.pricing import Usage

    return Usage(event["input_tokens"], event["output_tokens"], event["cached_input_tokens"])


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/phase5-trace-fixtures"))
    args = parser.parse_args()
    failed = False
    for scenario in ("near_failure_recovery", "explicit_failure"):
        directory, report = await run_scenario(args.output, scenario)
        print(f"{scenario}: {report['result']} ({directory}) — provider_fixture, not live")
        failed |= report["result"] != "PASS"
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    # The harness has no paid mode or environment-key/provider factory.
    if os.getenv("APP_ENV", "development") != "development":
        raise SystemExit("Fixture harness requires development mode")
    asyncio.run(main())
