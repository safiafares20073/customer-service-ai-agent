"""Allowlisted JSONL metadata only: never log prompts, answers, arguments or references."""

import json
import math
import os
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from yemen_customer_service.tool_server.models import OUTPUT_MODELS

EVENTS = {"started", "reserved", "usage", "tool", "awaiting_confirmation", "resumed", "finished"}
FIELDS = {
    "turns",
    "active_seconds",
    "cost_usd",
    "reserved_usd",
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "tool",
    "status",
    "reason",
}


def safe_text(text: str) -> str:
    text = re.sub(r"\b[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[redacted]", text)
    text = re.sub(
        r"\b[A-Za-z0-9_-]{32,}\b",
        lambda match: match[0] if re.fullmatch(r"T-[a-f0-9]{32}", match[0]) else "[redacted]",
        text,
    )
    text = re.sub(r"(?i)\b(?:api[_ -]?key|password|secret|token)\s*[:=]\s*\S+", "[redacted]", text)
    return text


class Trace:
    def __init__(self, directory: str | Path, task_id: str, mode: str):
        if not re.fullmatch(r"[a-f0-9]{32}", task_id) or mode not in {"fixture", "openai"}:
            raise ValueError("Invalid trace identity")
        root = Path(directory)
        if "traces" in root.parts and mode == "fixture":
            raise ValueError("Fixture evidence cannot be written to submission traces")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = root / f"{task_id}.{mode}.jsonl"
        self.task_id, self.mode = task_id, mode

    def emit(self, event: str, **fields) -> None:
        if event not in EVENTS or set(fields) - FIELDS:
            raise ValueError("Trace event is not allowlisted")
        if "tool" in fields and fields["tool"] not in OUTPUT_MODELS:
            fields["tool"] = "unknown"
        for key in ("status", "reason"):
            if key in fields and not re.fullmatch(r"[A-Za-z_]{1,64}", fields[key]):
                raise ValueError("Trace code is not safe")
        for key in ("turns", "input_tokens", "output_tokens", "cached_input_tokens"):
            if key in fields and (type(fields[key]) is not int or fields[key] < 0):
                raise ValueError("Trace counter is not safe")
        for key in ("cost_usd", "reserved_usd"):
            if fields.get(key) is not None:
                value = fields[key]
                if not isinstance(value, str) or not re.fullmatch(
                    r"\d+(?:\.\d+)?(?:E[+-]?\d+)?", value
                ):
                    raise ValueError("Trace cost is not safe")
                if not Decimal(value).is_finite():
                    raise ValueError("Trace cost is not finite")
        if "active_seconds" in fields and (
            not isinstance(fields["active_seconds"], (int, float))
            or not math.isfinite(fields["active_seconds"])
            or fields["active_seconds"] < 0
        ):
            raise ValueError("Trace elapsed time is not safe")
        record = {
            "schema_version": 1,
            "task_id": self.task_id,
            "provider": self.mode,
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence": "provider_fixture" if self.mode == "fixture" else "live_openai",
            "event": event,
            **fields,
        }
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
