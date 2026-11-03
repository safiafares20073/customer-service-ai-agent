"""Prepare or explicitly run ONE synthetic live smoke task; never auto-retry it."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
from decimal import Decimal
from pathlib import Path

from yemen_customer_service.agent.loop import Agent, Outcome
from yemen_customer_service.agent.pricing import Pricing, PricingError, Usage
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError
from yemen_customer_service.agent.state import Journal, Limits
from yemen_customer_service.agent.tracing import safe_text
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError

MODEL = "gpt-6-luna"
QUESTION = "Find headphones under $30 and explain the return policy."
DIRECTORY = Path("artifacts/live_smoke")


def price_anchor(price: str, answer: str) -> bool:
    whole, cents = price.split(".")
    amount = re.escape(whole) + (r"(?:\.00)?" if cents == "00" else r"\." + cents)
    return bool(
        re.search(
            rf"(?:\$\s*|\bUSD\s*){amount}(?!\d|\.\d)"
            rf"|(?<![\d.]){amount}\s*USD\b",
            answer,
            re.I,
        )
    )


def configured_pricing() -> Pricing:
    if os.getenv("OPENAI_MODEL", MODEL) != MODEL:
        raise ProviderError(
            "This prepared smoke test requires gpt-6-luna; no substitution allowed."
        )
    pricing = Pricing.load(os.getenv("MODEL_PRICING_FILE", "config/model_pricing.json"), MODEL)
    if (pricing.input_rate, pricing.output_rate, pricing.cached_rate) != (
        Decimal("0.10"),
        Decimal("0.50"),
        Decimal("0.01"),
    ):
        raise PricingError("Re-review the prepared smoke test if verified Standard rates change.")
    return pricing


def claim_attempt(directory: Path) -> None:
    """Persistent one-shot interlock. Never remove it automatically after failure."""
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (directory / "synthetic.sqlite3").exists():
        raise ProviderError("Existing smoke database found; stop for review instead of repeating.")
    try:
        fd = os.open(
            directory / "attempt.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
    except FileExistsError:
        raise ProviderError(
            "A smoke attempt was already claimed. No repeat call is allowed."
        ) from None
    with os.fdopen(fd, "w") as marker:
        marker.write(
            "One attempt claimed. Retain this interlock and review before any further run.\n"
        )


def verify(store: Store, journal: Journal, outcome: Outcome, pricing: Pricing) -> dict:
    """Offline verification only: no model judge and no extra API/MCP requests."""
    state = journal.load(outcome.task_id)
    pending, received = {}, []
    for message in state.messages:
        if message["role"] == "assistant":
            pending = {c["id"]: c["function"]["name"] for c in message.get("tool_calls", [])}
        elif message["role"] == "tool":
            name = pending.pop(message["tool_call_id"], None)
            value = json.loads(message["content"])
            if name and value.get("ok"):
                received.append((name, value["data"]))
    with store.db.connect() as conn:
        audits = conn.execute(
            "SELECT tool, outcome, result_code FROM audits WHERE task_id=? ORDER BY id",
            (outcome.task_id,),
        ).fetchall()
        records = conn.execute(
            "SELECT * FROM cost_records WHERE task_id=? ORDER BY id", (outcome.task_id,)
        ).fetchall()
        snapshots = {
            row["id"]: json.loads(
                conn.execute(
                    "SELECT value FROM metadata WHERE key=?", (f"agent_cost:{row['id']}",)
                ).fetchone()[0]
            )
            for row in records
        }
        tickets = conn.execute("SELECT count(*) FROM tickets").fetchone()[0]
    actual_calls = [
        row["tool"] for row in audits if row["tool"] != "agent" and row["outcome"] == "allow"
    ]
    products, policies = [], []
    for name, data in received:
        if name in {"list_products", "search_products"}:
            products.extend(data["products"])
        elif name == "get_product_details":
            products.append(data)
        elif name == "get_store_policies":
            policies.extend(p for p in data["policies"] if p["topic"] == "returns")
    candidates = [
        p
        for p in products
        if "headphone" in p["name"].casefold()
        and p["currency"] == "USD"
        and Decimal(p["price"]) < 30
    ]
    answer = safe_text(outcome.answer)
    folded = answer.casefold()
    product_anchor = any(
        p["name"].casefold() in folded and price_anchor(p["price"], answer) for p in candidates
    )
    policy_anchor = bool(
        policies
        and re.search(r"\b(?:14|fourteen)\s+days?\b", folded)
        and "original receipt" in folded
    )
    ledger, total, known = [], Decimal("0"), bool(records)
    for row in records:
        detail = snapshots[row["id"]]
        valid = (
            row["status"] == "recorded"
            and row["provider"] == state.provider
            and row["model"] == MODEL
            and row["pricing_version"] == pricing.version
            and row["input_tokens"] is not None
            and row["output_tokens"] is not None
            and row["cost_usd"] is not None
        )
        if valid:
            usage = Usage(row["input_tokens"], row["output_tokens"], detail["cached_input_tokens"])
            valid = usage.valid() and pricing.cost(usage) == Decimal(row["cost_usd"])
            valid = valid and (
                detail["input_usd_per_million"],
                detail["output_usd_per_million"],
                detail["cached_input_usd_per_million"],
            ) == ("0.10", "0.50", "0.01")
        known = known and valid
        if valid:
            total += Decimal(row["cost_usd"])
        ledger.append(
            {
                "status": row["status"],
                "input_tokens": row["input_tokens"],
                "output_tokens": row["output_tokens"],
                "cached_input_tokens": detail["cached_input_tokens"],
                "computed_usd": row["cost_usd"],
            }
        )
    checks = {
        "completed": outcome.status == "completed",
        "actual_mcp_calls_match_transcript": bool(actual_calls)
        and actual_calls == [n for n, _ in received],
        "product_facts_received": bool(candidates),
        "returns_policy_received": bool(policies),
        "product_name_and_price_anchor": bool(product_anchor),
        "policy_anchor": policy_anchor,
        "read_only_task": tickets == 0
        and all(
            n in {"list_products", "search_products", "get_product_details", "get_store_policies"}
            for n in actual_calls
        ),
        "usage_and_usd_reconciled": known
        and outcome.cost_known
        and len(records) == outcome.turns
        and total == Decimal(outcome.estimated_or_recorded_usd),
        "within_limits": 0 < outcome.turns <= 8
        and outcome.active_seconds <= 60
        and Decimal(outcome.estimated_or_recorded_usd) <= Decimal("0.05"),
    }
    return {
        "question": QUESTION,
        "model": MODEL,
        "provider": state.provider,
        "evidence": "provider_fixture" if state.provider == "fixture" else "live_openai_attempt",
        "requested_service_tier": "default",
        "reasoning_effort": "none",
        "pricing_version": pricing.version,
        "task_id": outcome.task_id,
        "status": outcome.status,
        "answer": answer,
        "mcp_tools_called": actual_calls,
        "verified_product_facts": candidates,
        "verified_return_policies": policies,
        "usage_records": ledger,
        "computed_usd": str(total) if known else None,
        "llm_request_attempts": outcome.turns,
        "active_seconds": outcome.active_seconds,
        "checks": checks,
        "automated_checks_passed": all(checks.values()),
        "human_grounding_review_required": True,
        "billing_invoice_verified": False,
    }


async def execute(
    store: Store, token: str, provider: OpenAIProvider, pricing: Pricing, directory: Path
) -> dict:
    journal = Journal(store, token)
    async with connect(store.db.path, store, token, enable_demo_auth=True) as client:
        outcome = await Agent(
            client,
            journal,
            provider,
            pricing,
            limits=Limits(),
            trace_directory=directory / "events",
        ).start(QUESTION)
    return verify(store, journal, outcome, pricing)


async def run(*, allow_paid: bool, enable_demo_auth: bool) -> dict | None:
    pricing = configured_pricing()
    if not allow_paid:
        print("PREPARED ONLY — no API request made.")
        print("Question:", QUESTION)
        print("Model: gpt-6-luna; Standard; reasoning_effort=none; max output=512.")
        print("Limits: 8 requests; USD 0.05 estimated; 60s active; 10s/tool.")
        print(
            "Credentials:",
            "present"
            if (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"))
            else "not configured",
        )
        print(
            "One-shot interlock:",
            "already claimed" if (DIRECTORY / "attempt.lock").exists() else "not claimed",
        )
        return None
    if not enable_demo_auth or os.getenv("APP_ENV", "development") != "development":
        raise SafeError("ACCESS_DENIED")
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")):
        raise ProviderError("Credentials are not configured. No request made.")
    claim_attempt(DIRECTORY)
    provider = OpenAIProvider.from_environment(paid_approved=True)
    # The SDK owns the credential until close; no child process needs these variables.
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("LLM_API_KEY", None)
    try:
        database = Database(DIRECTORY / "synthetic.sqlite3")
        database.initialize(seed_demo=True)
        store = Store(database)
        token = store.provision_demo_session("demo-a", enable_demo_auth=True, app_env="development")
        report = await execute(store, token, provider, pricing, DIRECTORY)
        fd = os.open(
            DIRECTORY / "report.openai.json",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
        with os.fdopen(fd, "w") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return report
    finally:
        await provider.client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--enable-demo-auth", action="store_true")
    args = parser.parse_args()
    if args.preflight and args.allow_paid:
        parser.error("Preflight and paid execution cannot be combined.")
    logging.disable(logging.CRITICAL)  # No SDK HTTP debug/body/header logging in this process.
    try:
        report = asyncio.run(
            run(allow_paid=args.allow_paid, enable_demo_auth=args.enable_demo_auth)
        )
        if report is not None and not report["automated_checks_passed"]:
            parser.exit(
                1, "Smoke checks failed or are incomplete. Review; do not repeat the call.\n"
            )
    except (ProviderError, PricingError, SafeError) as exc:
        parser.exit(2, str(exc) + "\n")
    except Exception:
        parser.exit(2, "Smoke attempt failed. Retain evidence and interlock; stop for review.\n")


if __name__ == "__main__":
    main()
