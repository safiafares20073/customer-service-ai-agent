"""Additive email-invitation extension; no raw email/subject, secrets or resets."""

from yemen_customer_service.hosting.settings import GOOGLE_ISSUER, normalize_email
from yemen_customer_service.tool_server.models import SafeError

VERSION = "1"


def initialize(conn):
    marker = conn.execute(
        "SELECT value FROM metadata WHERE key='hosted_email_invitation_version'"
    ).fetchone()
    if marker is None:
        conn.execute(
            "CREATE TABLE hosted_email_invites (email_hash TEXT PRIMARY KEY,"
            "principal TEXT,enabled INTEGER NOT NULL,bound_at REAL)"
        )
        conn.execute(
            "INSERT INTO metadata VALUES ('hosted_email_invitation_version',?)", (VERSION,)
        )
    elif marker[0] != VERSION:
        raise ValueError("Unknown email invitation version")


def configure(conn, settings):
    conn.execute("UPDATE hosted_email_invites SET enabled=0")
    for email in settings.email_invites:
        conn.execute(
            "INSERT INTO hosted_email_invites VALUES (?,NULL,1,NULL) "
            "ON CONFLICT(email_hash) DO UPDATE SET enabled=1",
            (settings.email_hash(email),),
        )
    conn.execute(
        "UPDATE hosted_principals SET enabled=1 WHERE principal IN "
        "(SELECT principal FROM hosted_email_invites WHERE enabled=1 AND principal IS NOT NULL)"
    )


def authorize(store, login, settings, claims):
    """Caller has already validated native OIDC claims. No public enrollment API."""
    if (
        settings.issuer != GOOGLE_ISSUER
        or not settings.email_invites
        or not store.db.path.is_file()
    ):
        raise SafeError("ACCESS_DENIED")
    if "email_verified" in claims and claims["email_verified"] is not True:
        raise SafeError("ACCESS_DENIED")
    with store.db.connect(write=True) as conn:
        if login.expires <= store.clock():
            raise SafeError("ACCESS_DENIED")
        old_login = conn.execute(
            "SELECT revoked,expires FROM hosted_logins WHERE fingerprint=?", (login.fingerprint,)
        ).fetchone()
        if old_login and (old_login["revoked"] or old_login["expires"] <= store.clock()):
            raise SafeError("ACCESS_DENIED")
        active = {settings.email_hash(email) for email in settings.email_invites}
        # Stable issuer/subject principal is the authority after enrollment;
        # renamed or absent email claims cannot substitute another subject.
        bound = conn.execute(
            "SELECT email_hash FROM hosted_email_invites WHERE principal=? AND enabled=1",
            (login.principal,),
        ).fetchall()
        if any(row[0] in active for row in bound):
            return
        if claims.get("email_verified") is not True:
            raise SafeError("ACCESS_DENIED")
        try:
            email = normalize_email(claims.get("email"))
        except ValueError:
            raise SafeError("ACCESS_DENIED") from None
        hashed = settings.email_hash(email)
        if hashed not in active:
            raise SafeError("ACCESS_DENIED")
        invitation = conn.execute(
            "SELECT principal FROM hosted_email_invites WHERE email_hash=? AND enabled=1", (hashed,)
        ).fetchone()
        if invitation is None or invitation[0] not in {None, login.principal}:
            raise SafeError("ACCESS_DENIED")
        # BEGIN IMMEDIATE serializes competing first logins. Binding is never
        # overwritten by configure, removal/re-addition, purge or another subject.
        conn.execute(
            "UPDATE hosted_email_invites SET principal=?,bound_at=? "
            "WHERE email_hash=? AND principal IS NULL",
            (login.principal, store.clock(), hashed),
        )
        conn.execute(
            "INSERT INTO hosted_principals VALUES (?,1) "
            "ON CONFLICT(principal) DO UPDATE SET enabled=1",
            (login.principal,),
        )
