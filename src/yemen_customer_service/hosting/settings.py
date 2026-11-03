"""Validated operator configuration; never log settings or secret values."""

import hashlib
import hmac
import json
import math
import os
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit


def https_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("HTTPS configuration required")
    if parsed.query or parsed.fragment:
        raise ValueError("Unsafe URL configuration")
    return value


@dataclass(frozen=True, repr=False)
class Settings:
    data_dir: Path
    origin: str
    issuer: str
    metadata_url: str
    client_id: str
    client_secret: str = field(repr=False)
    cookie_secret: str = field(repr=False)
    principal_secret: str = field(repr=False)
    invites: tuple[tuple[str, str], ...]
    paid_enabled: bool = False
    approval_until: float = 0
    global_budget: Decimal = Decimal(0)
    principal_budget: Decimal = Decimal(0)
    session_seconds: int = 900
    tasks_per_hour: int = 5

    @classmethod
    def load(cls):
        if (
            os.getenv("APP_ENV") != "production"
            or os.getenv("ENABLE_DEMO_AUTH", "false") != "false"
        ):
            raise ValueError("Hosted mode requires production without development auth")
        if os.getenv("UI_PROVIDER", "openai") != "openai":
            raise ValueError("Hosted UI cannot select fixture providers")
        origin = https_url(os.environ["HOSTED_ORIGIN"]).rstrip("/")
        if urlsplit(origin).path:
            raise ValueError("Origin must not contain a path")
        issuer = https_url(os.environ["OIDC_ISSUER"])
        metadata = https_url(os.environ["OIDC_METADATA_URL"])
        if urlsplit(issuer).netloc != urlsplit(metadata).netloc:
            raise ValueError("Issuer/discovery origin mismatch")
        secret = os.environ["OIDC_CLIENT_SECRET"]
        cookie = os.environ["HOSTED_COOKIE_SECRET"]
        principal = os.environ["HOSTED_PRINCIPAL_SECRET"]
        if (
            len(secret) < 16
            or len(cookie) < 48
            or len(principal) < 48
            or len({secret, cookie, principal}) != 3
        ):
            raise ValueError("Strong distinct secrets required")
        if not 1 <= len(os.environ["OIDC_CLIENT_ID"]) <= 256:
            raise ValueError("OIDC client ID required")
        if os.getenv("OPENAI_MODEL", "gpt-6-luna") != "gpt-6-luna":
            raise ValueError("Hosted model requires a compatibility review")
        raw = json.loads(os.getenv("HOSTED_REVIEWERS_JSON", "[]"))
        if not isinstance(raw, list) or len(raw) > 50:
            raise ValueError("Invalid reviewer allowlist")
        invites = []
        for item in raw:
            if set(item) != {"iss", "sub"} or item["iss"] != issuer:
                raise ValueError("Reviewer issuer mismatch")
            if not isinstance(item["sub"], str) or not 1 <= len(item["sub"]) <= 256:
                raise ValueError("Invalid reviewer subject")
            invites.append((issuer, item["sub"]))
        global_budget = Decimal(os.getenv("HOSTED_GLOBAL_BUDGET_USD", "0"))
        principal_budget = Decimal(os.getenv("HOSTED_PRINCIPAL_BUDGET_USD", "0"))
        if not all(v.is_finite() and v >= 0 for v in (global_budget, principal_budget)):
            raise ValueError("Invalid allowance")
        if principal_budget > global_budget or global_budget > 10:
            raise ValueError("Allowance out of range")
        approval = float(os.getenv("HOSTED_APPROVAL_UNTIL", "0"))
        if not math.isfinite(approval) or approval < 0:
            raise ValueError("Invalid approval expiry")
        paid = os.getenv("HOSTED_PAID_ENABLED", "false")
        if paid not in {"false", "true"} or (paid == "true" and principal_budget <= 0):
            raise ValueError("Explicit allowance required")
        seconds = int(os.getenv("HOSTED_SESSION_SECONDS", "900"))
        rate = int(os.getenv("HOSTED_TASKS_PER_HOUR", "5"))
        if not 60 <= seconds <= 900 or not 1 <= rate <= 20:
            raise ValueError("Session/rate setting out of range")
        return cls(
            Path(os.environ["HOSTED_DATA_DIR"]).absolute(),
            origin,
            issuer,
            metadata,
            os.environ["OIDC_CLIENT_ID"],
            secret,
            cookie,
            principal,
            tuple(invites),
            paid == "true",
            approval,
            global_budget,
            principal_budget,
            seconds,
            rate,
        )

    def principal(self, issuer, subject):
        raw = json.dumps([issuer, subject], separators=(",", ":")).encode()
        return "R-" + hmac.new(self.principal_secret.encode(), raw, hashlib.sha256).hexdigest()[:48]

    @property
    def allowed_principals(self):
        return {self.principal(issuer, sub) for issuer, sub in self.invites}
