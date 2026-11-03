"""Guarded synthetic agent console. Live execution requires explicit paid approval."""

import argparse
import asyncio
import os

from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing, PricingError
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError


def session_binding(store: Store, args) -> str:
    """Use a launcher's original binding without minting a replacement on resume."""
    existing = os.getenv("CS_SESSION_TOKEN")
    if existing:
        if args.customer is not None:
            raise ProviderError("Do not select a customer when a trusted session is already bound.")
        with store.db.connect() as conn:
            store.session(conn, existing)
        return existing
    if args.resume_task:
        raise ProviderError("Resumption requires the original trusted session binding.")
    return store.provision_demo_session(
        args.customer or "demo-a", enable_demo_auth=True, app_env="development"
    )


async def run(args) -> None:
    model = os.getenv("OPENAI_MODEL", "gpt-6-luna")
    path = os.getenv("MODEL_PRICING_FILE", "config/model_pricing.json")
    pricing = Pricing.load(path, model)
    if args.preflight:
        print("Configured model:", model, "| pricing version:", pricing.version)
        print("Pricing: user-supplied official Standard excerpt; live compatibility unverified.")
        print(
            "Credentials:",
            "present"
            if (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"))
            else "not configured",
        )
        print("No provider requests made. Paid execution requires explicit approval.")
        return
    if not args.allow_paid:
        raise ProviderError("No requests made. Explicit paid-run approval is required.")
    if not args.enable_demo_auth or os.getenv("APP_ENV", "development") != "development":
        raise SafeError("ACCESS_DENIED")
    if args.resume_task and not os.getenv("CS_SESSION_TOKEN"):
        raise ProviderError("Resumption requires the original trusted session binding.")
    database = Database(os.getenv("DATABASE_PATH", "data/customer_service.sqlite3"))
    database.initialize(seed_demo=True)
    store = Store(database)
    token = session_binding(store, args)
    provider = OpenAIProvider.from_environment(paid_approved=True)
    try:
        async with connect(database.path, store, token, enable_demo_auth=True) as client:
            agent = Agent(client, Journal(store, token), provider, pricing)
            if args.resume_task:
                state = agent.journal.load(args.resume_task)
                if state.status != "awaiting_confirmation":
                    raise SafeError("ACCESS_DENIED")
                draft = state.queue[0]["arguments"]
                print("Pending draft:", draft["subject"], "—", draft["message"])
                if draft.get("order_id"):
                    print("Order:", draft["order_id"])
                confirmed = input("Type CONFIRM for this exact draft: ").strip() == "CONFIRM"
                outcome = await agent.resume(state.task_id, confirmed=confirmed)
            else:
                if not args.request:
                    raise ProviderError("Supply a synthetic customer request.")
                outcome = await agent.start(args.request)
            while outcome.status == "awaiting_confirmation":
                print("Draft:", outcome.draft.subject, "—", outcome.draft.message)
                if outcome.draft.order_id:
                    print("Order:", outcome.draft.order_id)
                print("Task:", outcome.task_id)
                confirmed = input("Type CONFIRM for this exact draft: ").strip() == "CONFIRM"
                outcome = await agent.resume(outcome.task_id, confirmed=confirmed)
            print(outcome.answer)
            print(
                "Status:",
                outcome.status,
                "| requests:",
                outcome.turns,
                "| USD:",
                outcome.estimated_or_recorded_usd if outcome.cost_known else "unknown",
            )
    finally:
        await provider.client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="?")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument(
        "--allow-paid",
        action="store_true",
        help="Use only after explicit operator approval of paid execution",
    )
    parser.add_argument("--enable-demo-auth", action="store_true")
    parser.add_argument("--customer", choices=["demo-a", "demo-b"])
    parser.add_argument("--resume-task")
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except (PricingError, ProviderError, SafeError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
