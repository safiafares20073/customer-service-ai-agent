"""SQLite migrations and synthetic fixtures. No real customer data belongs here."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 2

MIGRATIONS = {
    1: (
        "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
        "INSERT INTO metadata VALUES ('dataset', 'synthetic-only')",
        "CREATE TABLE customers (customer_id TEXT PRIMARY KEY, display_name TEXT NOT NULL)",
        """CREATE TABLE products (
            product_id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
            price_cents INTEGER NOT NULL CHECK(price_cents >= 0), currency TEXT NOT NULL,
            availability TEXT NOT NULL)""",
        """CREATE TABLE policies (
            topic TEXT PRIMARY KEY, text TEXT NOT NULL, version TEXT NOT NULL)""",
        """CREATE TABLE orders (
            order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers,
            status TEXT NOT NULL, estimated_delivery TEXT)""",
        """CREATE TABLE tickets (
            ticket_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers,
            subject TEXT NOT NULL, message TEXT NOT NULL, order_id TEXT REFERENCES orders,
            idempotency_key TEXT NOT NULL, payload_hash TEXT NOT NULL,
            created_at REAL NOT NULL, UNIQUE(customer_id, idempotency_key))""",
        """CREATE TABLE memory (
            id INTEGER PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers,
            content TEXT NOT NULL, created_at REAL NOT NULL)""",
        """CREATE TABLE audits (
            id INTEGER PRIMARY KEY, task_id TEXT NOT NULL, request_id TEXT NOT NULL,
            timestamp REAL NOT NULL, principal_ref TEXT NOT NULL, tool TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('allow','deny','error')),
            result_code TEXT NOT NULL)""",
        """CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers,
            created_at REAL NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            budget_usd TEXT NOT NULL DEFAULT '0.05')""",
        """CREATE TABLE cost_records (
            id INTEGER PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks,
            provider TEXT NOT NULL, model TEXT NOT NULL, pricing_version TEXT NOT NULL,
            input_tokens INTEGER CHECK(input_tokens >= 0),
            output_tokens INTEGER CHECK(output_tokens >= 0), cost_usd TEXT,
            status TEXT NOT NULL CHECK(status IN ('reserved','recorded','unknown')),
            created_at REAL NOT NULL)""",
    ),
    2: (
        """CREATE TABLE sessions (
            token_hash TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers,
            task_id TEXT NOT NULL REFERENCES tasks, expires_at REAL NOT NULL)""",
        """CREATE TABLE order_access (
            token_hash TEXT PRIMARY KEY, session_hash TEXT NOT NULL REFERENCES sessions,
            order_id TEXT NOT NULL REFERENCES orders, expires_at REAL NOT NULL)""",
        """CREATE TABLE confirmations (
            token_hash TEXT PRIMARY KEY, session_hash TEXT NOT NULL REFERENCES sessions,
            payload_hash TEXT NOT NULL, expires_at REAL NOT NULL,
            consumed INTEGER NOT NULL DEFAULT 0 CHECK(consumed IN (0,1)))""",
        "CREATE INDEX memory_customer ON memory(customer_id, id)",
        "CREATE INDEX audit_task ON audits(task_id, id)",
    ),
}


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()

    @contextmanager
    def connect(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self, *, seed_demo: bool = False) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        is_new = not self.path.exists()
        with self.connect(write=True) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise ValueError("Database schema is newer than this application")
            for target in range(version + 1, SCHEMA_VERSION + 1):
                for statement in MIGRATIONS[target]:
                    conn.execute(statement)
                conn.execute(f"PRAGMA user_version = {target}")  # internal integer only
            marker = conn.execute("SELECT value FROM metadata WHERE key='dataset'").fetchone()
            if marker is None or marker[0] != "synthetic-only":
                raise ValueError("Only the synthetic dataset is supported")
            if seed_demo:
                self._seed(conn)
        if is_new:
            self.path.chmod(0o600)

    @staticmethod
    def _seed(conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT OR IGNORE INTO customers VALUES (?, ?)",
            [("demo-a", "Synthetic Customer A"), ("demo-b", "Synthetic Customer B")],
        )
        conn.executemany(
            "INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    "P-100",
                    "Example Headphones",
                    "Synthetic wired headphones",
                    2500,
                    "USD",
                    "in_stock",
                ),
                ("P-200", "Example Keyboard", "Synthetic USB keyboard", 4000, "USD", "in_stock"),
                ("P-300", "Example Mouse", "Synthetic optical mouse", 1500, "USD", "out_of_stock"),
            ],
        )
        conn.executemany(
            "INSERT OR IGNORE INTO policies VALUES (?, ?, ?)",
            [
                ("shipping", "Synthetic store ships within 3 business days.", "demo-v1"),
                ("returns", "Returns within 14 days with the original receipt.", "demo-v1"),
                ("privacy", "Synthetic demo only. Never submit real personal data.", "demo-v1"),
                (
                    "support",
                    "Open a support ticket after reviewing and confirming its draft.",
                    "demo-v1",
                ),
            ],
        )
        conn.executemany(
            "INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?)",
            [("DEMO-100", "demo-a", "shipped", None), ("DEMO-200", "demo-b", "processing", None)],
        )
