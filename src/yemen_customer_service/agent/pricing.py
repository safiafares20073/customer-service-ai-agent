"""Decimal accounting for a dated, model-specific Standard pricing snapshot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo


class PricingError(ValueError):
    pass


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int | None = None

    def valid(self) -> bool:
        values = (self.input_tokens, self.output_tokens)
        return all(type(v) is int and v >= 0 for v in values) and (
            self.cached_input_tokens is None
            or (
                type(self.cached_input_tokens) is int
                and 0 <= self.cached_input_tokens <= self.input_tokens
            )
        )


@dataclass(frozen=True)
class Pricing:
    model: str
    input_rate: Decimal
    output_rate: Decimal
    cached_rate: Decimal
    version: str

    @classmethod
    def load(cls, path: str | Path, model: str, *, today: date | None = None) -> Pricing:
        try:
            raw = Path(path).read_bytes()
            data = json.loads(raw)
            rates = [
                Decimal(data[key])
                for key in (
                    "input_usd_per_million",
                    "output_usd_per_million",
                    "cached_input_usd_per_million",
                )
            ]
            current_date = (
                today or datetime.now(ZoneInfo(data.get("verification_timezone", "UTC"))).date()
            )
            age = (current_date - date.fromisoformat(data["verified_on"])).days
            if (
                data["model"] != model
                or data["tier"] != "standard"
                or not 0 <= age <= 30
                or not all(rate.is_finite() and rate > 0 for rate in rates)
                or rates[2] > rates[0]
                or data["source_url"] != "https://developers.openai.com/api/docs/pricing"
                or data["verification_method"] != "user_supplied_official_excerpt"
            ):
                raise PricingError
            version = f"{data['verified_on']}:standard:{hashlib.sha256(raw).hexdigest()[:16]}"
            return cls(model, *rates, version)
        except (OSError, ValueError, KeyError, TypeError, ArithmeticError):
            raise PricingError("Missing, stale, invalid, or mismatched model pricing.") from None

    def cost(self, usage: Usage) -> Decimal:
        if not usage.valid():
            raise PricingError("Invalid usage.")
        cached = usage.cached_input_tokens or 0
        return (
            (usage.input_tokens - cached) * self.input_rate
            + cached * self.cached_rate
            + usage.output_tokens * self.output_rate
        ) / Decimal(1_000_000)

    def reserve(
        self, messages: list[dict], tools: list[dict], max_output: int
    ) -> tuple[int, Decimal]:
        # UTF-8 byte count exceeds byte-BPE text tokens; double it plus 4096 for
        # message/tool framing. This is a conservative engineering bound, not a
        # provider billing guarantee. Oversized prompts fail closed.
        size = len(json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False).encode())
        if size > 64_000 or not 1 <= max_output <= 512:
            raise PricingError("Request exceeds the configured input/output allowance.")
        input_bound = 2 * size + 4096
        return input_bound, self.cost(Usage(input_bound, max_output))
