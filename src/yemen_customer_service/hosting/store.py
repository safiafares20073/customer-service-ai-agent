"""Versioned hosted extension of the existing capability/ownership store."""

import secrets
import uuid

from yemen_customer_service.hosting.auth import Login
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store, digest
from yemen_customer_service.tool_server.models import SafeError

HOSTED_SCHEMA = 1
DDL = (
    "CREATE TABLE hosted_principals (principal TEXT PRIMARY KEY,enabled INTEGER NOT NULL)",
    "CREATE TABLE hosted_logins (fingerprint TEXT PRIMARY KEY,principal TEXT NOT NULL,"
    "expires REAL NOT NULL,revoked INTEGER NOT NULL DEFAULT 0)",
    "CREATE TABLE hosted_tasks (task_id TEXT PRIMARY KEY REFERENCES tasks,"
    "login TEXT NOT NULL REFERENCES hosted_logins)",
    "CREATE TABLE hosted_control (id INTEGER PRIMARY KEY CHECK(id=1),kill INTEGER NOT NULL,"
    "paid INTEGER NOT NULL,blocked INTEGER NOT NULL,approval_until REAL NOT NULL,"
    "global_budget TEXT NOT NULL,"
    "principal_budget TEXT NOT NULL)",
    "CREATE TABLE hosted_calls (id INTEGER PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks,"
    "principal TEXT NOT NULL,provider TEXT NOT NULL,pricing_version TEXT NOT NULL,"
    "reserved TEXT NOT NULL,status TEXT NOT NULL,cost TEXT,input_tokens INTEGER,"
    "output_tokens INTEGER,cached_tokens INTEGER)",
)


class HostedStore(Store):
    def initialize_hosted(self, *, evidence_mode="openai"):
        if evidence_mode not in {"openai", "fixture"}:
            raise ValueError("Invalid evidence mode")
        self.db.initialize()
        with self.db.connect(write=True) as c:
            marker = c.execute(
                "SELECT value FROM metadata WHERE key='hosted_schema_version'"
            ).fetchone()
            if marker is None:
                if any(
                    c.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
                    for table in ("customers", "orders", "tickets", "sessions", "memory", "tasks")
                ):
                    raise ValueError("Development or existing customer data cannot be hosted")
                for statement in DDL:
                    c.execute(statement)
                c.execute(
                    "INSERT INTO metadata VALUES ('hosted_schema_version',?)", (str(HOSTED_SCHEMA),)
                )
                c.execute(
                    "INSERT INTO metadata VALUES ('hosted_evidence_mode',?)", (evidence_mode,)
                )
                c.execute("INSERT INTO hosted_control VALUES (1,1,0,0,0,'0','0')")
            elif marker[0] != str(HOSTED_SCHEMA):
                raise ValueError("Unknown hosted schema")
            mode = c.execute(
                "SELECT value FROM metadata WHERE key='hosted_evidence_mode'"
            ).fetchone()
            if mode is None or mode[0] != evidence_mode:
                raise ValueError("Fixture data cannot be promoted to hosted live evidence")
            if c.execute(
                "SELECT 1 FROM customers WHERE customer_id IN ('demo-a','demo-b')"
            ).fetchone():
                raise ValueError("Development identities are forbidden")
            Database.seed_catalog(c)

    def configure(self, settings):
        with self.db.connect(write=True) as c:
            c.execute("UPDATE hosted_principals SET enabled=0")
            for principal in settings.allowed_principals:
                c.execute(
                    "INSERT INTO hosted_principals VALUES (?,1) ON CONFLICT(principal) "
                    "DO UPDATE SET enabled=1",
                    (principal,),
                )
            c.execute(
                "UPDATE hosted_control SET paid=?,approval_until=?,global_budget=?,"
                "principal_budget=? WHERE id=1",
                (
                    int(settings.paid_enabled),
                    settings.approval_until,
                    str(settings.global_budget),
                    str(settings.principal_budget),
                ),
            )

            c.execute(
                "UPDATE hosted_control SET kill=1,blocked=1 WHERE EXISTS "
                "(SELECT 1 FROM hosted_calls WHERE status!='recorded')"
            )

    def register_login(self, login: Login):
        with self.db.connect(write=True) as c:
            if login.expires <= self.clock():
                raise SafeError("ACCESS_DENIED")
            allowed = c.execute(
                "SELECT enabled FROM hosted_principals WHERE principal=?", (login.principal,)
            ).fetchone()
            if allowed is None or allowed[0] != 1:
                raise SafeError("ACCESS_DENIED")
            c.execute(
                "INSERT OR IGNORE INTO hosted_logins VALUES (?,?,?,0)",
                (login.fingerprint, login.principal, login.expires),
            )
            self.check_login(c, login)
            c.execute(
                "INSERT OR IGNORE INTO customers VALUES (?, 'Invited reviewer')", (login.principal,)
            )

    def check_login(self, c, login: Login):
        row = c.execute(
            "SELECT l.* FROM hosted_logins l JOIN hosted_principals p "
            "ON p.principal=l.principal WHERE l.fingerprint=? AND p.enabled=1 "
            "AND l.revoked=0 AND l.expires>? AND l.principal=?",
            (login.fingerprint, self.clock(), login.principal),
        ).fetchone()
        if row is None:
            raise SafeError("ACCESS_DENIED")
        return row

    def provision(self, login: Login, *, tasks_per_hour):
        token, task = secrets.token_urlsafe(32), uuid.uuid4().hex
        with self.db.connect(write=True) as c:
            row = self.check_login(c, login)
            count = c.execute(
                "SELECT count(*) FROM tasks WHERE customer_id=? AND created_at>?",
                (login.principal, self.clock() - 3600),
            ).fetchone()[0]
            if count >= tasks_per_hour:
                raise SafeError("ACCESS_DENIED")
            c.execute(
                "INSERT INTO tasks(task_id,customer_id,created_at) VALUES (?,?,?)",
                (task, login.principal, self.clock()),
            )
            c.execute(
                "INSERT INTO sessions VALUES (?,?,?,?)",
                (digest(token), login.principal, task, row["expires"]),
            )
            c.execute("INSERT INTO hosted_tasks VALUES (?,?)", (task, login.fingerprint))
        return token

    def session(self, conn, token):
        identity = super().session(conn, token)
        row = conn.execute(
            "SELECT l.principal,l.fingerprint,l.expires FROM hosted_logins l "
            "JOIN hosted_tasks t ON t.login=l.fingerprint WHERE t.task_id=?",
            (identity["task_id"],),
        ).fetchone()
        if row is None or row["principal"] != identity["customer_id"]:
            raise SafeError("ACCESS_DENIED")
        self.check_login(conn, Login(row["principal"], row["fingerprint"], row["expires"]))
        return identity

    def revoke(self, login: Login):
        with self.db.connect(write=True) as c:
            c.execute(
                "UPDATE hosted_logins SET revoked=1 WHERE fingerprint=?", (login.fingerprint,)
            )
            refs = [
                r[0]
                for r in c.execute(
                    "SELECT s.token_hash FROM sessions s JOIN hosted_tasks t "
                    "ON t.task_id=s.task_id WHERE t.login=?",
                    (login.fingerprint,),
                )
            ]
            for ref in refs:
                c.execute("DELETE FROM confirmations WHERE session_hash=?", (ref,))
                c.execute("DELETE FROM order_access WHERE session_hash=?", (ref,))
                c.execute("UPDATE sessions SET expires_at=0 WHERE token_hash=?", (ref,))

    def operations_allowed(self, conn):
        row = conn.execute("SELECT * FROM hosted_control WHERE id=1").fetchone()
        return bool(
            row
            and row["kill"] == 0
            and row["blocked"] == 0
            and row["paid"] == 1
            and row["approval_until"] > self.clock()
            and conn.execute(
                "SELECT 1 FROM hosted_calls WHERE status!='recorded' LIMIT 1"
            ).fetchone()
            is None
        )

    def _check_write(self, conn, identity):
        if not self.operations_allowed(conn):
            raise SafeError("ACCESS_DENIED")

    def set_kill(self, *, enabled):
        with self.db.connect(write=True) as c:
            row = c.execute("SELECT * FROM hosted_control WHERE id=1").fetchone()
            ambiguous = c.execute(
                "SELECT 1 FROM hosted_calls WHERE status!='recorded' LIMIT 1"
            ).fetchone()
            if enabled and not (
                row["paid"] == 1
                and row["approval_until"] > self.clock()
                and row["blocked"] == 0
                and ambiguous is None
            ):
                raise SafeError("ACCESS_DENIED")
            c.execute("UPDATE hosted_control SET kill=? WHERE id=1", (0 if enabled else 1,))

    def purge_content(self, *, before=None):
        cutoff = self.clock() - 7 * 86400 if before is None else before
        with self.db.connect(write=True) as c:
            c.execute("DELETE FROM memory WHERE created_at<?", (cutoff,))
            c.execute("DELETE FROM tickets WHERE created_at<?", (cutoff,))
            expired = [
                r[0] for r in c.execute("SELECT task_id FROM tasks WHERE created_at<?", (cutoff,))
            ]
            for task in expired:
                c.execute("DELETE FROM metadata WHERE key=?", ("agent_task:" + task,))
                c.execute("UPDATE sessions SET expires_at=0 WHERE task_id=?", (task,))
            # Preserve every task/call/cost/audit and revoked-login record.
