"""Server-side per-browser controller. No credentials or task references are widgets."""

from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing
from yemen_customer_service.agent.provider import OpenAIProvider, ProviderError
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.agent.tracing import safe_text
from yemen_customer_service.storage.database import Database
from yemen_customer_service.storage.store import Store
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError, TicketDraft
from yemen_customer_service.ui.presentation import COPY, customer_text, outcome_message


def make_provider() -> OpenAIProvider:
    mode = os.getenv("UI_PROVIDER", "fixture")
    if mode == "fixture":
        from yemen_customer_service.ui.fixture_provider import demonstration_provider

        return demonstration_provider()
    if mode == "openai" and os.getenv("UI_PAID_APPROVED") == "true":
        return OpenAIProvider.from_environment(paid_approved=True)
    raise ProviderError("Provider unavailable")


@dataclass(frozen=True)
class Pending:
    token: str
    task_id: str
    draft: TicketDraft


class Controller:
    def __init__(
        self,
        database_path: str | Path,
        customer_id: str,
        *,
        demo_enabled: bool,
        provider_factory: Callable[[], OpenAIProvider] | None = None,
    ):
        if (
            not demo_enabled
            or os.getenv("APP_ENV", "development") != "development"
            or customer_id not in {"demo-a", "demo-b"}
        ):
            raise SafeError("ACCESS_DENIED")
        self.store = Store(Database(database_path))
        self.store.db.initialize(seed_demo=True)
        self._initialize(self.store, customer_id, provider_factory)

    def _initialize(self, store, customer_id, provider_factory):
        self.store = store
        self._customer = customer_id  # Trusted server only; never a browser selector.
        self._provider_factory = provider_factory or make_provider
        self._pending: Pending | None = None
        self._lock = threading.Lock()
        self._seen: set[str] = set()
        self.messages: list[tuple[str, str]] = []
        self.status = "ready"
        self.revision = 0
        self.error = ""

    def _new_token(self):
        return self.store.provision_demo_session(
            self._customer, enable_demo_auth=True, app_env="development"
        )

    @property
    def busy(self) -> bool:
        return self._lock.locked()

    @property
    def draft(self) -> dict[str, str] | None:
        if self._pending is None:
            return None
        draft = self._pending.draft
        # No idempotency key, task ID, token, or security reference in widget data.
        return {
            "subject": draft.subject,
            "message": draft.message,
            "order_id": draft.order_id or "",
        }

    async def _operate(
        self,
        token: str,
        *,
        request: str | None = None,
        task_id: str | None = None,
        confirmed: bool = False,
    ):
        provider = self._provider_factory()
        try:
            pricing = Pricing.load(
                os.getenv("MODEL_PRICING_FILE", "config/model_pricing.json"), provider.model
            )
            async with connect(
                self.store.db.path, self.store, token, enable_demo_auth=True
            ) as client:
                agent = Agent(
                    client,
                    Journal(self.store, token),
                    provider,
                    pricing,
                    trace_directory="artifacts/phase4-ui",
                )
                if request is not None:
                    return await agent.start(request)
                return await agent.resume(task_id, confirmed=confirmed)
        finally:
            await provider.client.close()

    def _accept(self, token: str, result, locale: str) -> None:
        self.status = result.status
        if result.status == "awaiting_confirmation":
            visible = (result.draft.subject, result.draft.message, result.draft.order_id or "")
            if any(customer_text(value, locale) != value for value in visible):
                Journal(self.store, token).cancel_ticket(result.task_id)
                self._pending = None
                self.status = "error"
                self.messages.append(("assistant", COPY[locale]["error"]))
                self.revision += 1
                return
            self._pending = Pending(token, result.task_id, result.draft)
        else:
            self._pending = None
        self.revision += 1
        self.messages.append(("assistant", outcome_message(result.status, result.answer, locale)))

    def submit(self, request: str, submission_id: str, locale: str) -> None:
        if not self._lock.acquire(blocking=False):
            return
        try:
            if submission_id in self._seen or self._pending is not None:
                return
            self._seen.add(submission_id)
            if not isinstance(request, str) or not 1 <= len(request.strip()) <= 2000:
                self.error = COPY[locale]["invalid"]
                return
            request = customer_text(request.strip(), locale, hide_internal=False)
            self.messages.append(("user", request))
            self.error = ""
            self.status = "working"
            token = self._new_token()
            result = asyncio.run(self._operate(token, request=request))
            self._accept(token, result, locale)
        except Exception:
            self.status = "error"
            self.messages.append(("assistant", COPY[locale]["error"]))
        finally:
            self._lock.release()

    def edit(self, subject: str, message: str, order_id: str, locale: str) -> bool:
        if not self._lock.acquire(blocking=False):
            return False
        try:
            if self._pending is None:
                return False
            draft = TicketDraft(
                subject=safe_text(subject),
                message=safe_text(message),
                order_id=order_id.strip() or None,
                idempotency_key=self._pending.draft.idempotency_key,
            )
            journal = Journal(self.store, self._pending.token)
            journal.edit_ticket(self._pending.task_id, draft)
            self._pending = Pending(self._pending.token, self._pending.task_id, draft)
            self.revision += 1
            self.error = ""
            return True
        except Exception as exc:
            # Even invalid edits cancel outstanding consent; do not approve a stale draft.
            if self._pending:
                try:
                    self.store.revoke_confirmations(self._pending.token)
                except Exception:
                    pass
            self.error = COPY[locale][
                "invalid" if isinstance(exc, (ValidationError, ValueError, SafeError)) else "error"
            ]
            self.revision += 1
            return False
        finally:
            self._lock.release()

    def decide(self, *, confirm: bool, revision: int, locale: str) -> None:
        if not self._lock.acquire(blocking=False):
            return
        try:
            if self._pending is None or revision != self.revision or (confirm and self.error):
                return
            pending = self._pending
            self.error = ""
            self.status = "working"
            if not confirm:
                Journal(self.store, pending.token).cancel_ticket(pending.task_id)
                self._pending = None
                self.status = "confirmation_declined"
                self.revision += 1
                self.messages.append(("assistant", COPY[locale]["cancelled"]))
                return
            result = asyncio.run(
                self._operate(pending.token, task_id=pending.task_id, confirmed=confirm)
            )
            self._accept(pending.token, result, locale)
        except Exception:
            self.status = "error"
            self._pending = None  # No automatic replay after an ambiguous write.
            self.messages.append(("assistant", COPY[locale]["error"]))
        finally:
            self._lock.release()
