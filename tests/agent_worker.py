"""Separate-process agent fixture runner, explicitly not a live-provider run."""

import argparse
import asyncio
import json
import sys
from datetime import date

from tests.agent_support import MODEL, SDKScript, completion
from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import connect


async def run(args, token):
    database = Database(args.database)
    database.initialize()
    store = Store(database)
    pricing = Pricing.load("config/model_pricing.json", MODEL, today=date(2026, 11, 3))
    if args.mode == "remember":
        actions = [completion("I will remember your synthetic preference for wired headphones.")]
        request = "My synthetic preference is wired headphones."
    elif args.mode == "recall":

        def recall(payload):
            memory = json.dumps(payload["messages"])
            return completion(
                "You prefer wired headphones."
                if "wired headphones" in memory
                else "No prior preference is available."
            )

        actions, request = [recall], "What is my previous synthetic preference?"
    elif args.mode == "ticket_start":
        actions = [
            completion(
                calls=[
                    (
                        "create_support_ticket",
                        {
                            "subject": "Synthetic damaged headphones",
                            "message": "Synthetic support request",
                            "order_id": "DEMO-100",
                            "idempotency_key": "process-restart-ticket",
                        },
                    )
                ]
            )
        ]
        request = "Prepare a synthetic ticket for my damaged headphones."
    else:
        actions, request = [completion("The synthetic ticket was created.")], None
    script = SDKScript(actions)
    try:
        async with connect(database.path, store, token, enable_demo_auth=True) as client:
            agent = Agent(
                client,
                Journal(store, token),
                script.provider,
                pricing,
                trace_directory=args.evidence,
            )
            if args.mode == "ticket_resume":
                outcome = await agent.resume(args.task_id, confirmed=True)
            else:
                outcome = await agent.start(request)
            print(
                json.dumps(
                    {
                        "provider": "fixture",
                        "task_id": outcome.task_id,
                        "status": outcome.status,
                        "answer": outcome.answer,
                        "turns": outcome.turns,
                        "active_seconds": outcome.active_seconds,
                        "cost_usd": outcome.estimated_or_recorded_usd,
                        "requests_this_process": len(script.requests),
                    }
                )
            )
    finally:
        await script.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["remember", "recall", "ticket_start", "ticket_resume"])
    parser.add_argument("database")
    parser.add_argument("evidence")
    parser.add_argument("--task-id")
    arguments = parser.parse_args()
    asyncio.run(run(arguments, sys.stdin.read()))
