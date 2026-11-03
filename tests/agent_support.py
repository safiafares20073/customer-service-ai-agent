"""Explicit provider fixtures over the official OpenAI SDK HTTP boundary.

These responses are synthetic and are NOT evidence of live OpenAI availability,
reasoning quality, actual tokenization, or billed costs. MCP is never mocked.
"""

import json

import httpx
from openai import AsyncOpenAI

from yemen_customer_service.agent.provider import OpenAIProvider

MODEL = "gpt-6-luna"


def completion(content=None, *, calls=None, usage=True, **usage_changes):
    message = {"role": "assistant", "content": content}
    if calls:
        message["tool_calls"] = [
            {
                "id": f"call_{i}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments),
                },
            }
            for i, (name, arguments) in enumerate(calls)
        ]
    result = {
        "id": "fixture-completion",
        "object": "chat.completion",
        "created": 0,
        "model": MODEL,
        "service_tier": "default",
        "choices": [
            {"index": 0, "message": message, "finish_reason": "tool_calls" if calls else "stop"}
        ],
    }
    if usage:
        result["usage"] = {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "prompt_tokens_details": {"cached_tokens": 0},
            **usage_changes,
        }
    return result


class SDKScript:
    def __init__(self, actions):
        self.actions = list(actions)
        self.requests = []

        async def handler(request):
            payload = json.loads(request.content)
            self.requests.append(payload)
            assert request.url.host == "fixture.invalid"
            assert request.url.path == "/v1/chat/completions"
            assert payload["model"] == MODEL
            assert payload["service_tier"] == "default"
            assert payload["store"] is False
            assert payload["parallel_tool_calls"] is False
            assert payload["reasoning_effort"] == "none"
            assert 1 <= payload["max_completion_tokens"] <= 512
            if not self.actions:
                raise AssertionError("Unexpected extra model request")
            action = self.actions.pop(0)
            if callable(action):
                action = action(payload)
                if hasattr(action, "__await__"):
                    action = await action
            if isinstance(action, Exception):
                raise action
            if isinstance(action, httpx.Response):
                return action
            return httpx.Response(200, json=action)

        self.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        self.sdk = AsyncOpenAI(
            api_key="fixture-not-a-real-key",
            max_retries=0,
            base_url="https://fixture.invalid/v1",
            http_client=self.http,
        )
        self.provider = OpenAIProvider(self.sdk, MODEL, mode="fixture")

    async def close(self):
        await self.sdk.close()
