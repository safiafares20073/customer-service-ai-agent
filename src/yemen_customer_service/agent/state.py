"""Principal/session-scoped agent state using existing Phase 2 tables unchanged."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from yemen_customer_service.agent.pricing import Pricing, Usage
from yemen_customer_service.storage.store import Store, digest
from yemen_customer_service.tool_server.models import SafeError, TicketDraft


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    turns: int = Field(default=8, ge=1, le=8)
    budget_usd: Decimal = Field(default=Decimal("0.05"), gt=0, le=Decimal("0.05"))
    active_seconds: float = Field(default=60, gt=0, le=60)
    tool_seconds: float = Field(default=10, gt=0, le=10)
    max_output_tokens: int = Field(default=512, ge=1, le=512)


class TaskState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    session_hash: str
    model: str
    provider: Literal["openai", "fixture"]
    pricing_version: str
    limits: Limits
    status: str = "ready"
    turns: int = 0
    active_seconds: float = 0
    held_usd: Decimal = Decimal("0")
    unknown_cost: bool = False
    running: bool = False
    messages: list[dict] = Field(default_factory=list)
    queue: list[dict] = Field(default_factory=list)
    answer: str = ""
    request: str = ""
    last_result: dict | None = None


class Journal:
    def __init__(self, store: Store, token: str):
        self.store, self.token = store, token

    @staticmethod
    def key(task_id: str) -> str:
        return "agent_task:" + task_id

    def create(
        self,
        model: str,
        provider: str,
        pricing: Pricing | None,
        limits: Limits,
        messages: list[dict],
    ) -> TaskState:
        with self.store.db.connect(write=True) as conn:
            identity = self.store.session(conn, self.token)
            key = self.key(identity["task_id"])
            if conn.execute("SELECT 1 FROM metadata WHERE key=?", (key,)).fetchone():
                raise SafeError("INVALID_INPUT")  # one customer request per bound session
            state = TaskState(
                task_id=identity["task_id"],
                session_hash=identity["token_hash"],
                model=model,
                provider=provider,
                pricing_version=pricing.version if pricing else "unknown",
                limits=limits,
                messages=messages,
                request=messages[-1]["content"],
            )
            conn.execute("INSERT INTO metadata VALUES (?, ?)", (key, state.model_dump_json()))
            conn.execute(
                "UPDATE tasks SET budget_usd=? WHERE task_id=?",
                (str(limits.budget_usd), state.task_id),
            )
        return state

    def load(self, task_id: str) -> TaskState:
        with self.store.db.connect() as conn:
            identity = self.store.session(conn, self.token)
            task = conn.execute(
                "SELECT 1 FROM tasks WHERE task_id=? AND customer_id=?",
                (task_id, identity["customer_id"]),
            ).fetchone()
            row = conn.execute(
                "SELECT value FROM metadata WHERE key=?", (self.key(task_id),)
            ).fetchone()
            if task is None or row is None:
                raise SafeError("ACCESS_DENIED")
            state = TaskState.model_validate_json(row[0])
            if state.session_hash != identity["token_hash"]:
                raise SafeError("ACCESS_DENIED")
        return state

    def acquire(self, state: TaskState) -> None:
        with self.store.db.connect(write=True) as conn:
            identity = self.store.session(conn, self.token)
            row = conn.execute(
                "SELECT value FROM metadata WHERE key=?", (self.key(state.task_id),)
            ).fetchone()
            current = TaskState.model_validate_json(row[0])
            if (
                current.running
                or current.session_hash != identity["token_hash"]
                or current.status not in {"ready", "awaiting_confirmation"}
            ):
                raise SafeError("ACCESS_DENIED")
            state.running = True
            self._save(conn, state)

    def _save(self, conn, state: TaskState) -> None:
        # Accounting/cleanup of an already-authorized request must remain durable
        # even if its session expires while waiting for a provider response.
        # This grants no private read or permission to issue another request.
        if state.session_hash != digest(self.token):
            raise SafeError("ACCESS_DENIED")
        conn.execute(
            "UPDATE metadata SET value=? WHERE key=?",
            (state.model_dump_json(), self.key(state.task_id)),
        )
        conn.execute("UPDATE tasks SET status=? WHERE task_id=?", (state.status, state.task_id))

    def save(self, state: TaskState) -> None:
        with self.store.db.connect(write=True) as conn:
            self._save(conn, state)

    def edit_ticket(self, task_id: str, draft: TicketDraft) -> None:
        """Trusted UI edit: atomically revoke pending consent and replace its payload.

        Preserve task counters, pricing, session and idempotency key. This is not
        an MCP/model tool. A running/finished task cannot be edited.
        """
        with self.store.db.connect(write=True) as conn:
            identity = self.store.session(conn, self.token)
            row = conn.execute(
                "SELECT value FROM metadata WHERE key=?", (self.key(task_id),)
            ).fetchone()
            if row is None:
                raise SafeError("ACCESS_DENIED")
            state = TaskState.model_validate_json(row[0])
            if (
                state.session_hash != identity["token_hash"]
                or state.running
                or state.status != "awaiting_confirmation"
                or not state.queue
                or state.queue[0]["name"] != "create_support_ticket"
            ):
                raise SafeError("ACCESS_DENIED")
            original = state.queue[0]
            if draft.idempotency_key != original["arguments"]["idempotency_key"]:
                raise SafeError("INVALID_INPUT")
            new_arguments = draft.model_dump()
            found = False
            for message in reversed(state.messages):
                if message["role"] != "assistant":
                    continue
                for call in message.get("tool_calls", []):
                    if (
                        call["id"] == original["call_id"]
                        and call["function"]["name"] == original["name"]
                    ):
                        call["function"]["arguments"] = json.dumps(new_arguments)
                        found = True
                        break
                if found:
                    break
            if not found:
                raise SafeError("INVALID_INPUT")
            original["arguments"] = new_arguments
            conn.execute(
                "DELETE FROM confirmations WHERE session_hash=? AND consumed=0",
                (identity["token_hash"],),
            )
            self._save(conn, state)

    def cancel_ticket(self, task_id: str) -> None:
        """Trusted UI cancellation needs no provider, new request, or new task."""
        with self.store.db.connect(write=True) as conn:
            identity = self.store.session(conn, self.token)
            row = conn.execute(
                "SELECT value FROM metadata WHERE key=?", (self.key(task_id),)
            ).fetchone()
            if row is None:
                raise SafeError("ACCESS_DENIED")
            state = TaskState.model_validate_json(row[0])
            if (
                state.session_hash != identity["token_hash"]
                or state.running
                or state.status != "awaiting_confirmation"
            ):
                raise SafeError("ACCESS_DENIED")
            conn.execute(
                "DELETE FROM confirmations WHERE session_hash=? AND consumed=0",
                (identity["token_hash"],),
            )
            state.status = "confirmation_declined"
            state.answer = "Ticket request cancelled."
            self._save(conn, state)
        self.audit(state, "deny", "CONFIRMATION_DECLINED")

    def reserve(self, state: TaskState, pricing: Pricing, amount: Decimal) -> int:
        if state.turns >= state.limits.turns or state.held_usd + amount > state.limits.budget_usd:
            raise ValueError("Request limit reached")
        with self.store.db.connect(write=True) as conn:
            self.store.session(conn, self.token)
            state.turns += 1
            state.held_usd += amount
            row = conn.execute(
                "INSERT INTO cost_records(task_id, provider, model, pricing_version, "
                "cost_usd, status, created_at) VALUES (?, ?, ?, ?, ?, 'reserved', ?)",
                (
                    state.task_id,
                    state.provider,
                    state.model,
                    pricing.version,
                    str(amount),
                    self.store.clock(),
                ),
            )
            conn.execute(
                "INSERT INTO metadata VALUES (?, ?)",
                (
                    f"agent_cost:{row.lastrowid}",
                    json.dumps(
                        {
                            "provider": state.provider,
                            "pricing_version": pricing.version,
                            "input_usd_per_million": str(pricing.input_rate),
                            "output_usd_per_million": str(pricing.output_rate),
                            "cached_input_usd_per_million": str(pricing.cached_rate),
                            "reservation_usd": str(amount),
                            "cached_input_tokens": None,
                        }
                    ),
                ),
            )
            self._save(conn, state)
            return row.lastrowid

    def reconcile(
        self,
        state: TaskState,
        record_id: int,
        reserved: Decimal,
        pricing: Pricing,
        usage: Usage | None,
    ) -> None:
        known = usage is not None and usage.valid()
        with self.store.db.connect(write=True) as conn:
            if known:
                cost = pricing.cost(usage)
                state.held_usd += cost - reserved
                conn.execute(
                    "UPDATE cost_records SET status='recorded', input_tokens=?, "
                    "output_tokens=?, cost_usd=? WHERE id=? AND task_id=?",
                    (usage.input_tokens, usage.output_tokens, str(cost), record_id, state.task_id),
                )
            else:
                state.unknown_cost = True
                conn.execute(
                    "UPDATE cost_records SET status='unknown', cost_usd=NULL "
                    "WHERE id=? AND task_id=?",
                    (record_id, state.task_id),
                )
            detail_row = conn.execute(
                "SELECT value FROM metadata WHERE key=?", (f"agent_cost:{record_id}",)
            ).fetchone()
            details = json.loads(detail_row[0])
            details["cached_input_tokens"] = usage.cached_input_tokens if known else None
            details["usage_source"] = state.provider if known else "unknown"
            conn.execute(
                "UPDATE metadata SET value=? WHERE key=?",
                (json.dumps(details), f"agent_cost:{record_id}"),
            )
            self._save(conn, state)

    def audit(self, state: TaskState, outcome: str, code: str) -> None:
        self.store.audit(self.token, "agent", outcome, code)

    def memory(self) -> list[str]:
        return self.store.recall(self.token)

    def ensure_authenticated(self) -> None:
        with self.store.db.connect() as conn:
            self.store.session(conn, self.token)

    def remember(self, text: str) -> None:
        self.store.remember(self.token, text[:2000])
