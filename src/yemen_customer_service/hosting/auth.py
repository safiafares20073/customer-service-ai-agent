"""Authorize only native Streamlit/Authlib-validated server-side OIDC claims."""

import hashlib
import hmac
import json
import math
from dataclasses import dataclass

from yemen_customer_service.hosting.settings import Settings
from yemen_customer_service.tool_server.models import SafeError


@dataclass(frozen=True, repr=False)
class Login:
    principal: str
    fingerprint: str
    expires: float


def authorize_native_user(claims: dict, settings: Settings, now: float) -> Login:
    # This function consumes st.user, never request headers, widgets or model text.
    # Cryptographic signature/state/nonce validation belongs to native OIDC/Authlib.
    if claims.get("is_logged_in") is not True or claims.get("iss") != settings.issuer:
        raise SafeError("ACCESS_DENIED")
    subject, nonce = claims.get("sub"), claims.get("nonce")
    if not isinstance(subject, str) or not isinstance(nonce, str) or not 1 <= len(nonce) <= 512:
        raise SafeError("ACCESS_DENIED")
    if (settings.issuer, subject) not in settings.invites:
        raise SafeError("ACCESS_DENIED")
    audience = claims.get("aud")
    if claims.get("azp", settings.client_id) != settings.client_id:
        raise SafeError("ACCESS_DENIED")
    if not (
        audience == settings.client_id
        or (
            isinstance(audience, list)
            and settings.client_id in audience
            and claims.get("azp") == settings.client_id
        )
    ):
        raise SafeError("ACCESS_DENIED")
    iat, expiry = claims.get("iat"), claims.get("exp")
    for value in (iat, expiry):
        if type(value) not in {int, float} or not math.isfinite(value):
            raise SafeError("ACCESS_DENIED")
    end = min(expiry, iat + settings.session_seconds)
    if not iat <= now < end or expiry <= iat:
        raise SafeError("ACCESS_DENIED")
    raw = json.dumps(
        [settings.issuer, subject, audience, iat, expiry, nonce],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    fingerprint = hmac.new(settings.principal_secret.encode(), raw, hashlib.sha256).hexdigest()
    return Login(settings.principal(settings.issuer, subject), fingerprint, end)
