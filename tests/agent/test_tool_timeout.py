import sys

from mcp import StdioServerParameters

from tests.agent_support import completion
from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.state import Journal, Limits
from yemen_customer_service.tool_server.client import TrustedClient, protocol_session


async def test_tool_timeout_uses_actual_delayed_mcp_server(
    database,
    store,
    tokens,
    pricing,
    sdk_script,
    tmp_path,
):
    script = sdk_script([completion(calls=[("list_products", {})])])
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tests.slow_mcp_server"],
        env={"DATABASE_PATH": str(database.path), "CS_SESSION_TOKEN": tokens["demo-a"]},
    )
    async with protocol_session(params) as session:
        client = TrustedClient(session, store, tokens["demo-a"])
        result = await Agent(
            client,
            Journal(store, tokens["demo-a"]),
            script.provider,
            pricing,
            limits=Limits(tool_seconds=0.05),
            trace_directory=tmp_path,
        ).start("List products")
        assert result.status == "tool_timeout" and len(script.requests) == 1
