import sys
from contextlib import asynccontextmanager

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "synthetic.sqlite3")
    db.initialize(seed_demo=True)
    return db


@pytest.fixture
def store(database):
    return Store(database)


@pytest.fixture
def tokens(store):
    return {
        customer: store.provision_demo_session(
            customer, enable_demo_auth=True, app_env="development"
        )
        for customer in ("demo-a", "demo-b")
    }


@pytest.fixture
def wire(database, tmp_path):
    """Each invocation launches a real, fresh official SDK server subprocess."""

    @asynccontextmanager
    async def launch(token=None):
        env = {
            "DATABASE_PATH": str(database.path),
            "ENABLE_DEMO_AUTH": "true",
            "APP_ENV": "development",
        }
        if token:
            env["CS_SESSION_TOKEN"] = token
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "yemen_customer_service.tool_server.server"],
            env=env,
        )
        with (tmp_path / "server-stderr.log").open("a") as stderr, anyio.fail_after(20):
            async with stdio_client(parameters, errlog=stderr) as (read, write):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    assert initialized.serverInfo.name == "Synthetic Customer Service"
                    yield session

    return launch
