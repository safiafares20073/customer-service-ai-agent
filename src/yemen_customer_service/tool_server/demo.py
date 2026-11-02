"""Interactive synthetic-only MCP smoke client; no LLM and no submission traces."""

import argparse
import asyncio
import json
import os
import uuid

from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import TicketDraft


async def run(path: str, customer: str | None, enable_demo_auth: bool) -> None:
    database = Database(path)
    database.initialize(seed_demo=True)
    store = Store(database)
    token = None
    if customer:
        token = store.provision_demo_session(
            customer,
            enable_demo_auth=enable_demo_auth,
            app_env=os.getenv("APP_ENV", "development"),
        )
    async with connect(path, store, token, enable_demo_auth=enable_demo_auth) as client:
        print(
            "MCP initialized; tools:", ", ".join(t["name"] for t in await client.tools_for_model())
        )
        print(json.dumps(await client.invoke("list_products", {}), indent=2))
        if customer:
            order_id = "DEMO-100" if customer == "demo-a" else "DEMO-200"
            await client.invoke("verify_order_access", {"order_id": order_id})
            print(json.dumps(await client.invoke("get_order_status", {"order_id": order_id})))
            draft = TicketDraft(
                subject="Synthetic damaged headphones",
                message="This is a synthetic capstone support request.",
                idempotency_key=uuid.uuid4().hex,
                order_id=order_id,
            )
            print("Ticket draft:", draft.subject, "—", draft.message)
            if input("Create this synthetic ticket? Type CONFIRM: ").strip() == "CONFIRM":
                client.confirm_ticket(draft, confirmed=True)
                print(json.dumps(await client.invoke("create_support_ticket", draft.model_dump())))
            else:
                print("Ticket not created.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="data/customer_service.sqlite3")
    parser.add_argument("--customer", choices=["demo-a", "demo-b"])
    parser.add_argument("--enable-demo-auth", action="store_true")
    args = parser.parse_args()
    if args.customer and not args.enable_demo_auth:
        parser.error("--customer requires --enable-demo-auth for synthetic development only")
    asyncio.run(run(args.database, args.customer, args.enable_demo_auth))


if __name__ == "__main__":
    main()
