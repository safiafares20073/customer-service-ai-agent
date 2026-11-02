from yemen_customer_service.tool_server.models import TicketDraft


async def test_real_server_restart_preserves_ticket_and_catalog(wire, store, tokens, database):
    draft = TicketDraft(
        subject="Restart persistence",
        message="Synthetic ticket before restart",
        idempotency_key="restart-key",
        order_id="DEMO-100",
    )
    confirmation = store.register_confirmation(tokens["demo-a"], draft, confirmed=True)
    async with wire(tokens["demo-a"]) as first_process:
        verified = await first_process.call_tool("verify_order_access", {"order_id": "DEMO-100"})
        reference = verified.structuredContent["data"]["access_reference"]
        args = {
            **draft.model_dump(),
            "confirmation_reference": confirmation,
            "access_reference": reference,
        }
        first = await first_process.call_tool("create_support_ticket", args)
        assert not first.isError
    # Context exit closes the client and terminates the first server process.
    database.initialize(seed_demo=True)
    async with wire(tokens["demo-a"]) as restarted_process:
        repeated = await restarted_process.call_tool("create_support_ticket", args)
        assert not repeated.isError
        assert repeated.structuredContent == first.structuredContent
        catalog = await restarted_process.call_tool("list_products", {})
        assert len(catalog.structuredContent["data"]["products"]) == 3
        order = await restarted_process.call_tool(
            "get_order_status",
            {
                "order_id": "DEMO-100",
                "access_reference": reference,
            },
        )
        assert not order.isError and order.structuredContent["data"]["status"] == "shipped"
    with database.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
