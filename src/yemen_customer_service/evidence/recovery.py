"""Reviewed harness-only recovery policy. No production auto-retry."""

from yemen_customer_service.tool_server.client import TrustedClient


class ReadRecoveryClient(TrustedClient):
    """Harness-only policy: at most one retry of list_products for this task.

    Agent._tool's existing timeout surrounds both calls. No write, authorization
    error, nonretryable result or transport exception is retried. No LLM request
    or task/session/counter reset occurs here. Production adapter is unchanged.
    """

    def __init__(self, session, store, token, journal, trace):
        super().__init__(session, store, token)
        self.journal, self.trace = journal, trace
        self.retried = False

    async def invoke(self, name, arguments):
        response = await super().invoke(name, arguments)
        if response.get("ok"):
            return response
        error = response.get("error", {})
        self.trace.emit("tool", tool=name, status="error", reason=error["code"])
        if (
            name != "list_products"
            or self.retried
            or error.get("code") != "INTERNAL_ERROR"
            or error.get("retryable") is not True
        ):
            return response
        state = self.journal.load(self.trace.task_id)
        if state.unknown_cost or state.held_usd >= state.limits.budget_usd:
            return response
        self.retried = True
        self.trace.emit("tool", tool=name, status="retrying", reason="INTERNAL_ERROR")
        return await super().invoke(name, arguments)
