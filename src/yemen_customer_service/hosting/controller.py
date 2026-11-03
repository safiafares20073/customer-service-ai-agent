"""Authenticated hosted controller; existing draft/confirmation behavior is reused."""

import os

from yemen_customer_service.agent.loop import Agent
from yemen_customer_service.agent.pricing import Pricing, PricingError
from yemen_customer_service.agent.provider import OpenAIProvider
from yemen_customer_service.agent.state import Journal
from yemen_customer_service.hosting.spending import HostedProvider, Spending, single_operation
from yemen_customer_service.tool_server.client import connect
from yemen_customer_service.tool_server.models import SafeError
from yemen_customer_service.ui.presentation import COPY
from yemen_customer_service.ui.service import Controller


class HostedController(Controller):
    def __init__(self, store, login, settings, *, provider_factory=None):
        if os.getenv("APP_ENV") != "production":
            raise ValueError("Hosted controller requires production")
        self.login, self.settings = login, settings
        store.register_login(login)
        self._initialize(store, login.principal, provider_factory or self._real_provider)

    @staticmethod
    def _real_provider():
        return OpenAIProvider.from_environment(paid_approved=True)

    def validate(self, token=None):
        with self.store.db.connect() as c:
            self.store.check_login(c, self.login)
            if token is not None:
                identity = self.store.session(c, token)
                bound = c.execute(
                    "SELECT login FROM hosted_tasks WHERE task_id=?", (identity["task_id"],)
                ).fetchone()
                if bound is None or bound[0] != self.login.fingerprint:
                    raise SafeError("ACCESS_DENIED")

    @property
    def available(self):
        try:
            return Spending.available(self.store, self.login)
        except Exception:
            return False

    def _new_token(self):
        self.validate()
        return self.store.provision(self.login, tasks_per_hour=self.settings.tasks_per_hour)

    async def _operate(self, token, *, request=None, task_id=None, confirmed=False):
        self.validate(token)
        if not self.available:
            raise ValueError("Service unavailable")
        provider = self._provider_factory()
        try:
            pricing = Pricing.load(
                os.getenv("MODEL_PRICING_FILE", "config/model_pricing.json"), provider.model
            )
            if provider.model != "gpt-6-luna" or tuple(
                str(v) for v in (pricing.input_rate, pricing.output_rate, pricing.cached_rate)
            ) != ("0.10", "0.50", "0.01"):
                raise PricingError("Hosted model/pricing must be re-reviewed")
            async with connect(
                self.store.db.path, self.store, token, enable_hosted_auth=True
            ) as client:
                agent = Agent(
                    client,
                    Journal(self.store, token),
                    HostedProvider(provider, Spending(self.store, token), pricing),
                    pricing,
                    trace_directory=self.settings.data_dir / "events",
                )
                if request is not None:
                    return await agent.start(request)
                return await agent.resume(task_id, confirmed=confirmed)
        finally:
            await provider.client.close()

    def submit(self, request, submission_id, locale):
        try:
            self.validate()
            if not self.available:
                raise ValueError("Unavailable")
            with single_operation(self.settings.data_dir / "agent.active.lock"):
                super().submit(request, submission_id, locale)
        except Exception:
            self.error = COPY[locale]["error"]

    def edit(self, subject, message, order_id, locale):
        try:
            self.validate(self._pending.token if self._pending else None)
            return super().edit(subject, message, order_id, locale)
        except Exception:
            self.error = COPY[locale]["error"]
            return False

    def decide(self, *, confirm, revision, locale):
        try:
            self.validate(self._pending.token if self._pending else None)
            if confirm:
                if not self.available:
                    raise ValueError("Unavailable")
                with single_operation(self.settings.data_dir / "agent.active.lock"):
                    super().decide(confirm=confirm, revision=revision, locale=locale)
            else:
                super().decide(confirm=False, revision=revision, locale=locale)
        except Exception:
            self.error = COPY[locale]["error"]

    def logout(self):
        self.store.revoke(self.login)
        self._pending = None
        self.messages.clear()
