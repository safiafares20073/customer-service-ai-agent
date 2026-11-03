"""Real FastMCP server with a delayed real catalog query for timeout testing."""

import os
import time

from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.server import build_server


class SlowCatalog(Store):
    def list_products(self, limit=10, cursor=None):
        time.sleep(0.3)
        return super().list_products(limit, cursor)


if __name__ == "__main__":
    database = Database(os.environ["DATABASE_PATH"])
    database.initialize()
    build_server(SlowCatalog(database), os.environ["CS_SESSION_TOKEN"]).run(transport="stdio")
