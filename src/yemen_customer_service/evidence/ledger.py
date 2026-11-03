"""Private, durable two-scenario request and reservation ledger. No network code."""

import fcntl
import os
import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from yemen_customer_service.agent.provider import ProviderError

SCENARIOS = {"near_failure_recovery": 8, "explicit_failure": 1}


@contextmanager
def exclusive_plan(root: Path):
    # Refuse symlink components and official submission output locations.
    if "traces" in root.absolute().parts or any(p.is_symlink() for p in [root, *root.parents]):
        raise ProviderError("Unsafe evidence directory.")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if root.stat().st_mode & 0o077:
        raise ProviderError("Evidence directory must be owner-only.")
    fd = os.open(root / "plan.active.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ProviderError("Another scenario is already active.") from None
        yield
    finally:
        os.close(fd)


class Ledger:
    def __init__(self, root: Path, pricing_version: str, mode: str):
        if mode not in {"openai", "fixture"}:
            raise ProviderError("Unknown evidence mode.")
        self.path = root / "plan.sqlite3"
        if self.path.is_symlink():
            raise ProviderError("Unsafe ledger path.")
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        with self.connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY,value TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS runs (scenario TEXT PRIMARY KEY,status TEXT)")
            c.execute("""CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY,scenario TEXT,status TEXT,reserved TEXT,
                cost TEXT,input_tokens INTEGER,output_tokens INTEGER,cached_tokens INTEGER)""")
            for key, value in {"version": "1", "pricing": pricing_version, "mode": mode}.items():
                c.execute("INSERT OR IGNORE INTO metadata VALUES (?,?)", (key, value))
                if (
                    c.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()[0]
                    != value
                ):
                    raise ProviderError("Plan pricing or evidence mode changed; review required.")

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            c.execute("PRAGMA synchronous=FULL")
            c.execute("BEGIN IMMEDIATE")
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def claim(self, scenario):
        if scenario not in SCENARIOS:
            raise ProviderError("Unknown scenario.")
        with self.connect() as c:
            if c.execute("SELECT 1 FROM runs WHERE status!='passed'").fetchone():
                raise ProviderError("An earlier attempt is unfinished or failed; stop for review.")
            if c.execute("SELECT count(*) FROM runs").fetchone()[0] >= 2:
                raise ProviderError("Two-task allowance exhausted.")
            if c.execute("SELECT 1 FROM runs WHERE scenario=?", (scenario,)).fetchone():
                raise ProviderError("Scenario already attempted.")
            c.execute("INSERT INTO runs VALUES (?,'running')", (scenario,))

    def reserve(self, scenario, amount):
        if not amount.is_finite() or amount <= 0:
            raise ProviderError("Invalid reservation.")
        with self.connect() as c:
            run = c.execute("SELECT status FROM runs WHERE scenario=?", (scenario,)).fetchone()
            rows = c.execute("SELECT * FROM calls").fetchall()
            own = [r for r in rows if r["scenario"] == scenario]

            def held(rs):
                return sum(
                    (
                        Decimal(r["cost"] if r["status"] == "recorded" else r["reserved"])
                        for r in rs
                    ),
                    Decimal(0),
                )

            if (
                run is None
                or run[0] != "running"
                or c.execute(
                    "SELECT 1 FROM runs WHERE scenario!=? AND status!='passed'", (scenario,)
                ).fetchone()
                or any(r["status"] != "recorded" for r in rows)
                or len(rows) >= 9
                or len(own) >= SCENARIOS[scenario]
                or held(rows) + amount > Decimal("0.10")
                or held(own) + amount > Decimal("0.05")
            ):
                raise ProviderError("Plan request or estimated spending limit reached.")
            return c.execute(
                "INSERT INTO calls(scenario,status,reserved) VALUES (?,'reserved',?)",
                (scenario, str(amount)),
            ).lastrowid

    def reconcile(self, call_id, pricing, usage, *, bound, max_output):
        with self.connect() as c:
            row = c.execute("SELECT * FROM calls WHERE id=?", (call_id,)).fetchone()
            if row is None or row["status"] != "reserved":
                raise ProviderError("Reservation reconciliation failed.")
            known = usage is not None and usage.valid()
            if known:
                cost = pricing.cost(usage)
                c.execute(
                    "UPDATE calls SET status='recorded',cost=?,input_tokens=?,"
                    "output_tokens=?,cached_tokens=? WHERE id=?",
                    (
                        str(cost),
                        usage.input_tokens,
                        usage.output_tokens,
                        usage.cached_input_tokens,
                        call_id,
                    ),
                )
                unsafe = (
                    usage.input_tokens > bound
                    or usage.output_tokens > max_output
                    or cost > Decimal(row["reserved"])
                )
            else:
                c.execute("UPDATE calls SET status='unknown' WHERE id=?", (call_id,))
                unsafe = True
            if unsafe:
                c.execute("UPDATE runs SET status='blocked' WHERE scenario=?", (row["scenario"],))

    def finish(self, scenario, passed):
        with self.connect() as c:
            row = c.execute("SELECT status FROM runs WHERE scenario=?", (scenario,)).fetchone()
            ok = passed and row is not None and row[0] == "running"
            c.execute(
                "UPDATE runs SET status=? WHERE scenario=?",
                ("passed" if ok else "blocked", scenario),
            )
            return ok

    def rows(self, scenario):
        with self.connect() as c:
            return [
                dict(r)
                for r in c.execute("SELECT * FROM calls WHERE scenario=? ORDER BY id", (scenario,))
            ]
