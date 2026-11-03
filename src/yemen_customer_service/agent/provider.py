"""Official OpenAI SDK boundary. Fixture transport must be explicitly labeled."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from openai import APIError, AsyncOpenAI

from yemen_customer_service.agent.pricing import Usage


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class Reply:
    content: str | None
    calls: list[ToolCall]
    usage: Usage | None
    finish_reason: str


class ProviderError(Exception):
    """Never include SDK exception text, request bodies, or credential headers."""


class OpenAIProvider:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        *,
        mode: Literal["openai", "fixture"],
        paid_approved: bool = False,
    ):
        if mode not in {"openai", "fixture"} or (mode == "openai" and not paid_approved):
            raise ProviderError("Paid OpenAI execution requires explicit approval.")
        if client.max_retries != 0:
            raise ProviderError("SDK automatic retries must be disabled.")
        self.client, self.model, self.mode = client, model, mode

    @classmethod
    def from_environment(cls, *, paid_approved: bool = False) -> OpenAIProvider:
        if not paid_approved:
            raise ProviderError("Paid OpenAI execution requires explicit approval.")
        key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-6-luna")
        if not key:
            raise ProviderError("OpenAI credentials are not configured.")
        # Do not inherit an arbitrary alternate endpoint or organization setting.
        client = AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1", max_retries=0)
        return cls(client, model, mode="openai", paid_approved=True)

    async def complete(self, messages: list[dict], tools: list[dict], max_output: int) -> Reply:
        if self.mode == "fixture" and self.client.base_url.host != "fixture.invalid":
            raise ProviderError("Fixture execution requires a non-live transport endpoint.")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                reasoning_effort="none",  # gpt-6-luna Chat Completions tools require this.
                parallel_tool_calls=False,
                max_completion_tokens=max_output,
                n=1,
                store=False,
                service_tier="default",
            )
            if response.model != self.model or response.service_tier not in {None, "default"}:
                return Reply(None, [], None, "invalid")
            usage = None
            if response.usage is not None:
                details = response.usage.prompt_tokens_details
                cached = details.cached_tokens if details else None
                usage = Usage(
                    response.usage.prompt_tokens, response.usage.completion_tokens, cached
                )
            if not response.choices:
                return Reply(None, [], usage, "invalid")
            choice = response.choices[0]
            wire_calls = choice.message.tool_calls or []
            if any(c.type != "function" for c in wire_calls):
                return Reply(None, [], usage, "invalid")
            calls = [ToolCall(c.id, c.function.name, c.function.arguments) for c in wire_calls]
            return Reply(choice.message.content, calls, usage, choice.finish_reason)
        except (APIError, IndexError, AttributeError, TypeError, ValueError):
            raise ProviderError("The provider request failed; usage may be unknown.") from None
