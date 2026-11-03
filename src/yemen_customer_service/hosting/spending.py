"""Lifetime hosted allowances, durable pre-request reservations and single-worker gate."""

import fcntl
import json
import os
from contextlib import contextmanager
from decimal import Decimal

from yemen_customer_service.agent.provider import ProviderError


@contextmanager
def single_operation(path):
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ProviderError("Service busy") from None
        yield
    finally:
        os.close(fd)


def held(rows):
    return sum(
        (Decimal(r["cost"] if r["status"] == "recorded" else r["reserved"]) for r in rows),
        Decimal(0),
    )


class Spending:
    def __init__(self, store, token):
        self.store, self.token = store, token

    def reserve(self, amount, pricing, mode):
        with self.store.db.connect(write=True) as c:
            identity = self.store.session(c, self.token)
            if not self.store.operations_allowed(c):
                raise ProviderError("Paid operations unavailable")
            expected = c.execute(
                "SELECT value FROM metadata WHERE key='hosted_evidence_mode'"
            ).fetchone()[0]
            if expected != mode:
                raise ProviderError("Evidence mode mismatch")
            control = c.execute("SELECT * FROM hosted_control WHERE id=1").fetchone()
            rows = c.execute("SELECT * FROM hosted_calls").fetchall()
            own = [r for r in rows if r["principal"] == identity["customer_id"]]
            task = [r for r in own if r["task_id"] == identity["task_id"]]
            if (
                not amount.is_finite()
                or amount <= 0
                or any(r["status"] != "recorded" for r in rows)
                or held(rows) + amount > Decimal(control["global_budget"])
                or held(own) + amount > Decimal(control["principal_budget"])
                or held(task) + amount > Decimal("0.05")
                or len(task) >= 8
            ):
                raise ProviderError("Request allowance unavailable")
            ident = c.execute(
                "INSERT INTO hosted_calls(task_id,principal,provider,pricing_version,"
                "reserved,status) VALUES (?,?,?,?,?,'reserved')",
                (identity["task_id"], identity["customer_id"], mode, pricing.version, str(amount)),
            )
            c.execute(
                "INSERT INTO metadata VALUES (?,?)",
                (
                    f"hosted_cost:{ident.lastrowid}",
                    json.dumps(
                        {
                            "input_rate": str(pricing.input_rate),
                            "output_rate": str(pricing.output_rate),
                            "cached_rate": str(pricing.cached_rate),
                            "provider": mode,
                        }
                    ),
                ),
            )
            return ident.lastrowid

    def reconcile(self, ident, pricing, usage, *, bound, output_limit):
        # Reconcile even after login expiry/revocation; never grant another request.
        with self.store.db.connect(write=True) as c:
            row = c.execute("SELECT * FROM hosted_calls WHERE id=?", (ident,)).fetchone()
            if row is None or row["status"] != "reserved":
                raise ProviderError("Accounting reconciliation failed")
            known = usage is not None and usage.valid()
            if known:
                cost = pricing.cost(usage)
                c.execute(
                    "UPDATE hosted_calls SET status='recorded',cost=?,input_tokens=?,"
                    "output_tokens=?,cached_tokens=? WHERE id=?",
                    (
                        str(cost),
                        usage.input_tokens,
                        usage.output_tokens,
                        usage.cached_input_tokens,
                        ident,
                    ),
                )
                stop = (
                    usage.input_tokens > bound
                    or usage.output_tokens > output_limit
                    or cost > Decimal(row["reserved"])
                )
            else:
                c.execute("UPDATE hosted_calls SET status='unknown' WHERE id=?", (ident,))
                stop = True
            if stop:
                c.execute("UPDATE hosted_control SET kill=1,blocked=1 WHERE id=1")

    @staticmethod
    def available(store, login):
        with store.db.connect() as c:
            store.check_login(c, login)
            if not store.operations_allowed(c):
                return False
            control = c.execute("SELECT * FROM hosted_control WHERE id=1").fetchone()
            rows = c.execute("SELECT * FROM hosted_calls").fetchall()
            return (
                all(r["status"] == "recorded" for r in rows)
                and held(rows) < Decimal(control["global_budget"])
                and held([r for r in rows if r["principal"] == login.principal])
                < Decimal(control["principal_budget"])
            )


class HostedProvider:
    def __init__(self, provider, spending, pricing):
        self.provider, self.spending, self.pricing = provider, spending, pricing
        self.mode, self.model = provider.mode, provider.model

    async def complete(self, messages, tools, max_output):
        bound, amount = self.pricing.reserve(messages, tools, max_output)
        ident = self.spending.reserve(amount, self.pricing, self.mode)
        try:
            reply = await self.provider.complete(messages, tools, max_output)
        except BaseException:
            self.spending.reconcile(ident, self.pricing, None, bound=bound, output_limit=max_output)
            raise
        self.spending.reconcile(
            ident, self.pricing, reply.usage, bound=bound, output_limit=max_output
        )
        return reply
