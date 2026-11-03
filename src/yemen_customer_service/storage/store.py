"""Synthetic catalog and capability-based private operations.

The local operator and process launcher are trusted. MCP arguments are not.
No raw capabilities are persisted: the database contains only SHA-256 hashes.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sqlite3
import time
import uuid
from collections.abc import Callable
from typing import Any

from yemen_customer_service.storage.database import Database
from yemen_customer_service.tool_server.models import SafeError, TicketDraft


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def payload_hash(draft: TicketDraft) -> str:
    return digest(json.dumps(draft.model_dump(), sort_keys=True, separators=(",", ":")))


class Store:
    def __init__(self, database: Database, clock: Callable[[], float] = time.time):
        self.db = database
        self.clock = clock

    def provision_demo_session(
        self, customer_id: str, *, enable_demo_auth: bool, app_env: str
    ) -> str:
        """Trusted launcher API, never an MCP tool or model-accessible API.

        Synthetic fixture identity is permitted only by explicit development opt-in.
        This is not production login. Any process with DB write access is trusted.
        """
        if not enable_demo_auth or app_env != "development":
            raise SafeError("ACCESS_DENIED")
        token = secrets.token_urlsafe(32)
        task_id = uuid.uuid4().hex
        with self.db.connect(write=True) as conn:
            marker = conn.execute("SELECT value FROM metadata WHERE key='dataset'").fetchone()
            customer = conn.execute(
                "SELECT 1 FROM customers WHERE customer_id=?", (customer_id,)
            ).fetchone()
            hosted = conn.execute(
                "SELECT 1 FROM metadata WHERE key='hosted_schema_version'"
            ).fetchone()
            if hosted or marker is None or marker[0] != "synthetic-only" or customer is None:
                raise SafeError("ACCESS_DENIED")
            conn.execute(
                "INSERT INTO tasks(task_id, customer_id, created_at) VALUES (?, ?, ?)",
                (task_id, customer_id, self.clock()),
            )
            conn.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?)",
                (digest(token), customer_id, task_id, self.clock() + 3600),
            )
        return token

    def session(self, conn: sqlite3.Connection, token: str | None) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM sessions WHERE token_hash=? AND expires_at>?",
            (digest(token or ""), self.clock()),
        ).fetchone()
        if row is None:
            raise SafeError("ACCESS_DENIED")
        return row

    def _check_write(self, conn: sqlite3.Connection, identity: sqlite3.Row) -> None:
        """Extension hook within the write transaction; hosted mode adds its kill gate."""

    def register_confirmation(
        self, session_token: str, draft: TicketDraft, *, confirmed: bool
    ) -> str:
        """Register real consent captured by trusted code, never by model arguments.

        Caller must display the draft and capture explicit consent first. A new
        draft invalidates outstanding confirmations in this session. No MCP tool
        exposes this API. The console demo uses interactive human input.
        """
        if confirmed is not True:
            self.revoke_confirmations(session_token)
            raise SafeError("CONFIRMATION_REQUIRED")
        token = secrets.token_urlsafe(32)
        with self.db.connect(write=True) as conn:
            identity = self.session(conn, session_token)
            self._check_write(conn, identity)
            if draft.order_id:
                self._owner(conn, identity, draft.order_id)
            conn.execute(
                "DELETE FROM confirmations WHERE session_hash=? AND consumed=0",
                (identity["token_hash"],),
            )
            conn.execute(
                "INSERT INTO confirmations(token_hash, session_hash, payload_hash, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (digest(token), identity["token_hash"], payload_hash(draft), self.clock() + 300),
            )
        return token

    def revoke_confirmations(self, session_token: str) -> None:
        """Trusted draft-edit/cancel hook; invalidate pending consent server-side."""
        with self.db.connect(write=True) as conn:
            identity = self.session(conn, session_token)
            conn.execute(
                "DELETE FROM confirmations WHERE session_hash=? AND consumed=0",
                (identity["token_hash"],),
            )

    @staticmethod
    def _owner(conn: sqlite3.Connection, identity: sqlite3.Row, order_id: str) -> sqlite3.Row:
        order = conn.execute(
            "SELECT order_id, status, estimated_delivery FROM orders "
            "WHERE order_id=? AND customer_id=?",
            (order_id, identity["customer_id"]),
        ).fetchone()
        if order is None:
            raise SafeError("ACCESS_DENIED")
        return order

    def _access(
        self, conn: sqlite3.Connection, identity: sqlite3.Row, order_id: str, reference: str
    ) -> sqlite3.Row:
        order = self._owner(conn, identity, order_id)
        access = conn.execute(
            "SELECT 1 FROM order_access WHERE token_hash=? AND session_hash=? "
            "AND order_id=? AND expires_at>?",
            (digest(reference), identity["token_hash"], order_id, self.clock()),
        ).fetchone()
        if access is None:
            raise SafeError("ACCESS_DENIED")
        return order

    @staticmethod
    def _product(row: sqlite3.Row, *, details: bool = False) -> dict[str, Any]:
        result = {
            "product_id": row["product_id"],
            "name": row["name"],
            "description": row["description"] if details else row["description"][:200],
            "price": f"{row['price_cents'] // 100}.{row['price_cents'] % 100:02d}",
            "currency": row["currency"],
        }
        if details:
            result["availability"] = row["availability"]
        return result

    def list_products(self, limit: int = 10, cursor: str | None = None) -> dict[str, Any]:
        after = ""
        if cursor is not None:
            try:
                after = base64.b64decode(cursor, altchars=b"-_", validate=True).decode()
                if (
                    not after
                    or len(after) > 64
                    or not all(
                        c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
                        for c in after
                    )
                ):
                    raise ValueError
            except (ValueError, UnicodeError):
                raise SafeError("INVALID_INPUT") from None
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE product_id>? ORDER BY product_id LIMIT ?",
                (after, limit + 1),
            ).fetchall()
        next_cursor = None
        if len(rows) > limit:
            next_cursor = base64.urlsafe_b64encode(rows[limit - 1]["product_id"].encode()).decode()
        return {
            "products": [self._product(row) for row in rows[:limit]],
            "next_cursor": next_cursor,
        }

    def search_products(self, query: str, limit: int = 10) -> dict[str, Any]:
        # instr treats SQL syntax and LIKE wildcards as literal customer text.
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE instr(lower(name || ' ' || description), "
                "lower(?))>0 ORDER BY product_id LIMIT ?",
                (query, limit),
            ).fetchall()
        return {"products": [self._product(row) for row in rows], "next_cursor": None}

    def get_product_details(self, product_id: str) -> dict[str, Any]:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE product_id=?", (product_id,)
            ).fetchone()
        if row is None:
            raise SafeError("NOT_FOUND")
        return self._product(row, details=True)

    def get_store_policies(self, topic: str) -> dict[str, Any]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM policies WHERE (?='all' OR topic=?) ORDER BY topic", (topic, topic)
            ).fetchall()
        return {"policies": [dict(row) for row in rows]}

    def verify_order_access(self, session_token: str | None, order_id: str) -> dict[str, Any]:
        reference = secrets.token_urlsafe(32)
        with self.db.connect(write=True) as conn:
            identity = self.session(conn, session_token)
            self._owner(conn, identity, order_id)
            conn.execute(
                "INSERT INTO order_access VALUES (?, ?, ?, ?)",
                (digest(reference), identity["token_hash"], order_id, self.clock() + 300),
            )
        return {"authorized": True, "access_reference": reference}

    def get_order_status(
        self, session_token: str | None, order_id: str, access_reference: str
    ) -> dict[str, Any]:
        with self.db.connect() as conn:
            identity = self.session(conn, session_token)
            return dict(self._access(conn, identity, order_id, access_reference))

    def create_support_ticket(
        self,
        session_token: str | None,
        *,
        subject: str,
        message: str,
        confirmation_reference: str,
        idempotency_key: str,
        order_id: str | None = None,
        access_reference: str | None = None,
    ) -> dict[str, Any]:
        if (order_id is None) != (access_reference is None):
            raise SafeError("INVALID_INPUT")
        draft = TicketDraft(
            subject=subject, message=message, idempotency_key=idempotency_key, order_id=order_id
        )
        hashed_payload = payload_hash(draft)
        with self.db.connect(write=True) as conn:
            identity = self.session(conn, session_token)
            self._check_write(conn, identity)
            if order_id is not None and access_reference is not None:
                self._access(conn, identity, order_id, access_reference)
            existing = conn.execute(
                "SELECT ticket_id, payload_hash FROM tickets "
                "WHERE customer_id=? AND idempotency_key=?",
                (identity["customer_id"], idempotency_key),
            ).fetchone()
            if existing:
                if existing["payload_hash"] != hashed_payload:
                    raise SafeError("IDEMPOTENCY_CONFLICT")
                return {"ticket_id": existing["ticket_id"], "status": "created"}
            consent = conn.execute(
                "SELECT 1 FROM confirmations WHERE token_hash=? AND session_hash=? "
                "AND payload_hash=? AND expires_at>? AND consumed=0",
                (
                    digest(confirmation_reference),
                    identity["token_hash"],
                    hashed_payload,
                    self.clock(),
                ),
            ).fetchone()
            if consent is None:
                raise SafeError("CONFIRMATION_REQUIRED")
            ticket_id = "T-" + uuid.uuid4().hex
            conn.execute(
                "INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ticket_id,
                    identity["customer_id"],
                    subject,
                    message,
                    order_id,
                    idempotency_key,
                    hashed_payload,
                    self.clock(),
                ),
            )
            conn.execute(
                "UPDATE confirmations SET consumed=1 WHERE token_hash=?",
                (digest(confirmation_reference),),
            )
        return {"ticket_id": ticket_id, "status": "created"}

    def remember(self, session_token: str, content: str) -> None:
        """Trusted storage foundation only; no agent memory policy is implemented."""
        if not isinstance(content, str) or not 1 <= len(content) <= 2000:
            raise SafeError("INVALID_INPUT")
        with self.db.connect(write=True) as conn:
            identity = self.session(conn, session_token)
            conn.execute(
                "INSERT INTO memory(customer_id, content, created_at) VALUES (?, ?, ?)",
                (identity["customer_id"], content, self.clock()),
            )

    def recall(self, session_token: str) -> list[str]:
        with self.db.connect() as conn:
            identity = self.session(conn, session_token)
            rows = conn.execute(
                "SELECT content FROM (SELECT id, content FROM memory WHERE customer_id=? "
                "ORDER BY id DESC LIMIT 20) ORDER BY id",
                (identity["customer_id"],),
            ).fetchall()
        return [row["content"] for row in rows]

    def audit(self, token: str | None, tool: str, outcome: str, code: str) -> None:
        # Never record arguments, raw references, returned data, or exception text.
        with self.db.connect(write=True) as conn:
            try:
                identity = self.session(conn, token)
                principal = digest(identity["customer_id"])[:16]
                task_id = identity["task_id"]
            except SafeError:
                principal, task_id = "anonymous", "anonymous"
            conn.execute(
                "INSERT INTO audits(task_id, request_id, timestamp, principal_ref, tool, "
                "outcome, result_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, uuid.uuid4().hex, self.clock(), principal, tool, outcome, code),
            )
