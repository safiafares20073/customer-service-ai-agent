"""Test-only real FastMCP server with a disclosed catalog storage fault.

No production entry point imports this module. A real SQLite query fails before
the normal public catalog handler; only that injected error is marked retryable.
"""

import os
import sqlite3

from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.models import SafeError
from yemen_customer_service.tool_server.server import build_server, result


def main():
    if os.environ.get("APP_ENV") != "development":
        raise SystemExit("Fault harness requires development mode")
    database = Database(os.environ["DATABASE_PATH"])
    mode = os.environ["SCENARIO_FAULT"]
    if mode not in {"once", "always", "nonretryable", "denied"}:
        raise SystemExit("Unknown fault scenario")
    server = build_server(Store(database), os.environ["CS_SESSION_TOKEN"])
    normal_execute = server.execute
    attempts = 0

    def execute(name, **kwargs):
        nonlocal attempts
        if name == "list_products" and (attempts == 0 or mode == "always"):
            attempts += 1
            if mode == "denied":
                code = "ACCESS_DENIED"
            else:
                # Genuine storage failure, not a fabricated successful result.
                try:
                    with database.connect() as conn:
                        conn.execute("SELECT * FROM controlled_missing_catalog_table")
                except sqlite3.OperationalError:
                    code = "INTERNAL_ERROR"
                else:
                    raise RuntimeError("Fault injection did not occur")
            return result(
                {
                    "ok": False,
                    "error": {
                        "code": code,
                        "message": SafeError.MESSAGES[code],
                        "retryable": mode in {"once", "always"},
                    },
                },
                error=True,
            )
        return normal_execute(name, **kwargs)

    server.execute = execute
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
