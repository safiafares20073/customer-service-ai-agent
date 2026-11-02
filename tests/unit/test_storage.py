import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from yemen_customer_service.storage.database import MIGRATIONS, SCHEMA_VERSION, Database
from yemen_customer_service.tool_server.models import SafeError, TicketDraft


def test_migrations_seed_repeatable_and_constraints(database):
    database.initialize(seed_demo=True)
    with database.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert conn.execute("SELECT count(*) FROM products").fetchone()[0] == 3
        assert conn.execute("SELECT count(*) FROM customers").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM policies").fetchone()[0] == 4
        assert conn.execute("SELECT count(*) FROM orders").fetchone()[0] == 2
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"memory", "audits", "tasks", "cost_records", "tickets"} <= tables
    assert database.path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(sqlite3.IntegrityError), database.connect(write=True) as conn:
        conn.execute("INSERT INTO orders VALUES ('invalid', 'unknown', 'shipped', NULL)")


def test_upgrade_v1_preserves_data_and_rejects_future_schema(tmp_path):
    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as conn:
        for statement in MIGRATIONS[1]:
            conn.execute(statement)
        conn.execute("INSERT INTO customers VALUES ('demo-a', 'Synthetic existing fixture')")
        conn.execute("PRAGMA user_version=1")
    database = Database(path)
    database.initialize()
    with database.connect(write=True) as conn:
        assert conn.execute("SELECT display_name FROM customers").fetchone()[0].endswith("fixture")
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        conn.execute("PRAGMA user_version=999")
    with pytest.raises(ValueError, match="newer"):
        database.initialize()
    with database.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 999


@pytest.mark.parametrize(("enabled", "environment"), [(False, "development"), (True, "production")])
def test_demo_auth_requires_explicit_development_opt_in(store, enabled, environment):
    with pytest.raises(SafeError):
        store.provision_demo_session("demo-a", enable_demo_auth=enabled, app_env=environment)


def test_unknown_demo_identity_and_false_confirmation_denied(store, tokens):
    with pytest.raises(SafeError):
        store.provision_demo_session("unknown", enable_demo_auth=True, app_env="development")
    with pytest.raises(SafeError):
        store.register_confirmation(
            tokens["demo-a"],
            TicketDraft(
                subject="Synthetic",
                message="Synthetic",
                idempotency_key="test",
            ),
            confirmed=False,
        )


def test_memory_survives_separate_processes_and_is_scoped(database, store, tokens):
    store.remember(tokens["demo-a"], "Synthetic preference: wired headphones")
    # A new OS process loads the storage API and the same on-disk database.
    # Capability travels via stdin, never a command-line argument or printed output.
    code = """import sys
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
s = Store(Database(sys.argv[1]))
token = sys.stdin.read()
assert s.recall(token) == ['Synthetic preference: wired headphones']
s.remember(token, 'Synthetic preference: USB keyboard')
"""
    subprocess.run(
        [sys.executable, "-c", code, str(database.path)],
        input=tokens["demo-a"],
        text=True,
        check=True,
        timeout=10,
    )
    assert store.recall(tokens["demo-a"]) == [
        "Synthetic preference: wired headphones",
        "Synthetic preference: USB keyboard",
    ]
    assert store.recall(tokens["demo-b"]) == []
    with pytest.raises(SafeError):
        store.recall("forged")


def test_official_sdk_import_is_not_shadowed():
    from importlib.metadata import distribution

    import mcp

    installed = Path(distribution("mcp").locate_file("mcp")).resolve()
    assert Path(mcp.__file__).resolve().is_relative_to(installed)
    assert not Path("src/mcp").exists() and not Path("mcp.py").exists()


def test_server_rejects_demo_token_in_production(database):
    env = {
        **os.environ,
        "DATABASE_PATH": str(database.path),
        "CS_SESSION_TOKEN": "synthetic",
        "ENABLE_DEMO_AUTH": "true",
        "APP_ENV": "production",
    }
    process = subprocess.run(
        [sys.executable, "-m", "yemen_customer_service.tool_server.server"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode != 0
    assert "development demo opt-in" in process.stderr
    assert "synthetic" not in process.stderr
