# Invite-only hosted demo: implementation and verification

Prepared November 4, 2026 (Asia/Aden), from merged main
`39744ce44f3a53851b9bfbc08848fd0fe37ddd5e`. Deployment and paid calls have not
been performed. See [deployment instructions](DEPLOYMENT.md) for approval gates.

## Smallest suitable architecture

One Render Docker web service, one instance, one attached persistent disk. Render
terminates public HTTPS. Caddy receives the platform port and proxies to
Streamlit on loopback; both run under UID 10001 after the launcher assigns the
volume and permanently drops root. FastMCP remains a private stdio subprocess.
No database, MCP port, administrative HTTP route, or development launcher is public.
Railway could host the same container and mounted disk, but preparing two platform
configurations adds no capstone benefit. Render account features and current
service/disk prices must be checked before deployment.

Native Streamlit OIDC/Authlib validates authorization codes, signatures, state and
nonce. PKCE S256 and scope openid are required. The application accepts only
private, explicitly invited issuer/subject pairs and checks audience, authorized
party, nonce, issue/expiry time and a maximum 15-minute login age. Email, browser
fields, model arguments and unsigned proxy headers never establish identity.
Only a keyed opaque principal and keyed login fingerprint enter SQLite; profile
claims are not sent to the model. Each login has a separately scoped capability.
Removing an invitation, expiry or logout invalidates access. Logout also revokes
capabilities and consent; replaying an old signed identity cookie cannot revive a
revoked fingerprint. Task adoption by a different login is denied.

Streamlit 1.66.1's signed identity cookie has a 30-day lifetime and its native
Starlette setter omits Secure. The application enforces its shorter lifetime on
every action. Caddy appends Secure to all Set-Cookie responses, preserving
HttpOnly and SameSite=Lax, adds HSTS/nosniff/frame denial/referrer protection, and
has no access logging. Streamlit retains CORS and XSRF protection. Runtime Python
SDK/auth logging is disabled and errors are generic. Secret TOML is generated
only inside the mode-0700 mounted directory, mode 0600. Native OIDC code exchange
and cookie signing are not reimplemented. Real provider interoperability and
public HTTPS cookie/WebSocket behavior remain deployment acceptance checks.

## Data, permission and consent boundaries

The base schema remains version 2; the separate hosted extension is version 1.
Startup refuses development/customer-populated databases, unknown hosted schema
and fixture evidence mode. Only public synthetic catalog/policies are seeded.
An account is created only after validated invitation login. There are no
preloaded orders or demo identities. Existing order tools remain registered and
deny unowned/missing orders; public own-order success is deliberately unavailable.
Do not upload the development database, raw evidence bundles, attempt locks, or
original private reviewer databases.

Exactly seven tools and the original agent remain. Hosted capability validation
is added at the real MCP boundary and store. The existing draft/edit/confirm/
cancel workflow is reused, including idempotence and the same task's counters.
Write gates are checked inside the confirmation/ticket transaction. Kill, expiry
and unconfirmed or replayed consent cannot authorize writes. The shared UI renderer
keeps API tokens, costs and operational limits out of customer views. Synthetic
content disclosure is bilingual; do not enter personal information into chat.

Memory, private task transcripts and tickets remain principal-scoped. On startup
and private operator purge, content older than seven days is deleted and old task
capabilities expire. Purge retains task identity, audits, all costs and revoked
login fingerprints. This is purge-on-startup/manual, not a strict scheduled
seven-day deletion guarantee. During a running review, schedule the private purge
or run it at the end of the approved review window. Private event files contain
structured metadata, not raw prompts/answers; they are never public exports.

## Spending and availability

Paid mode is off, allowances zero and the durable kill switch ON initially.
No provider is constructed on an anonymous, uninvited or disabled-paid UI path.
Enabling requires separately approved secret configuration, positive lifetime
allowances and future approval expiry, followed by a private explicit enable
command. There is no public administration interface. A fresh verified pricing
snapshot is required: only gpt-6-luna Standard rates 0.10/0.50/0.01 USD per million
input/output/cached tokens are currently approved. Chat Completions uses
reasoning_effort none and Standard/default processing; no automatic model fallback.

A nonblocking OS lock permits one active task operation across processes.
Transactional durable reservations precede every SDK call. Global and principal
allowances are lifetime totals, not reset on login, restart, purge or cancellation.
Configuration cannot set a global allowance above USD 10; this ceiling does not
constitute spending approval. Per-task limits remain 8 requests, USD 0.05 estimated,
60 cumulative active seconds and 10 seconds per tool. Principal task starts are
rate-limited (default 5/hour, maximum configurable 20/hour).

Known usage is reconciled at recorded rates, even if a login expires in flight.
Missing usage, an interrupted reserved call, or usage above its conservative
reservation sets a sticky blocked/kill state. Restart cannot clear it; the normal
enable command refuses it. Do not reset the ledger to recover availability.
Review uncertain usage privately against the provider before designing any manual
reconciliation. A kill switch prevents subsequent calls/writes; it cannot cancel
an already sent request or undo billed tokens. Application estimates are not
provider hard billing caps. Use provider project controls and alerts as well.

SQLite and a single process gate are intentionally unsuitable for horizontal
replicas or high availability. HTTP denial-of-service can still affect the public
login page; provider-side login protection is required. Backup access is privileged:
restoring an older spending ledger could create allowance again. Disable calls
before backup/restore and retain the complete most recent accounting state;
ambiguous or stale restoration must remain paid-disabled until reconciliation.

## Verification scope and retained defects

Automated tests use clearly labeled provider fixtures and genuine MCP subprocesses.
OIDC tests exercise the installed native Authlib class with an offline mock issuer,
real generated signing keys, code exchange, PKCE, state/nonce/signature failures and
cookie tampering. AppTest's user objects are fixtures, never proof of live login.
They cover public landing, rejected users, English/Arabic and RTL widgets,
chat, exact draft edits/confirmation/cancel/replay, login/session isolation and
safe errors. Spending and memory tests cross real process boundaries.
A real Caddy binary tests response cookies and health proxying.

Initial checks found and corrected an extracted renderer's missing RTL variable,
a proxy-test HTTP/HTTPS address mismatch, container files unreadable after dropping
root, and a changed legacy production-demo rejection message. Existing tests were
preserved; the message fix retains both the denial and its prior safe wording.
Failed XML/logs remain ignored under artifacts/hosted-preparation. They are not
submission traces. Final executed counts and container results are recorded below.

Authlib 1.9.3 emits one httpx-integration deprecation warning through the installed
Streamlit stack. The exercised code exchange passes; this remains an upstream
maintenance item, not a suppressed warning or a live-provider compatibility claim.

No real IdP login, public TLS endpoint, assessor account, paid API exchange, mobile
pixel review, infrastructure invoice or independent penetration/vulnerability audit
is claimed. AppTest verifies bilingual text/RTL styling, not visual accessibility
on all devices. All three original submission trace files and cost_analysis.md
remain unchanged. No new execution is labeled live evidence.

## Final executed offline results

- `.venv/bin/pytest -q --tb=short --junitxml=artifacts/hosted-preparation/full-regression.xml`:
  **251 passed, 0 failed, 0 skipped**, 86.69 seconds, one upstream Authlib warning.
  This includes all 187 original tests unchanged and 64 new hosted tests.
- Affected hosted/legacy-denial rerun: **65 passed, 0 failed, 0 skipped**, 8.51 seconds.
- Ruff lint and format: passed (91 Python files formatted). Installed dependency
  compatibility: 63 packages checked, no conflicts. Frozen offline lock check:
  66 packages resolved. Offline source distribution and wheel build: passed.
- Actual Caddy 2.10.2 configuration and response-header/cookie/health checks passed.
- Docker image built successfully. Local loopback-only container test: health and
  HTML responses, private database/config content non-disclosure, zero initial
  customers/orders/model calls, UID 10001 operation, and a SQLite sentinel plus
  disabled-paid/kill state surviving a real container restart all passed.
  Container Python is 3.12.16; workspace regression Python is 3.12.14. The test
  used dummy OIDC configuration, no invited accounts and no API key; it did not
  perform login or prove live browser authentication. Its container is stopped;
  private test volume and JSON/log evidence remain local and ignored.
- Reviewed 38 intended text files; credential-pattern/manual review, private
  artifact exclusion, relative documentation links and git diff --check passed.
  This is not a third-party dependency vulnerability audit or penetration test.
- Original trace SHA-256 values remain success
  5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb,
  recovery 55e903d6b3726a5d13d68091a77ac6cee92de0bc99a7a8c57f947de359e6a841,
  failure a8bd7b17b4c7d2adb2810d28ba60622109b0b2be02a639e750713ea2abe0fbe6.
  Each trace and cost_analysis.md also matches its merged-main bytes directly.

Reproducible commands and Caddy extraction are in DEPLOYMENT.md. Managed cloud
checks used a writable /tmp/hosting-uv-cache and execution permissions allowing
real MCP/HTTP/container subprocesses; no protocol mock replaced MCP. Initial
container failures included both source file modes and Streamlit's default
root-home secret lookup after dropping privileges. The fixed launcher explicitly
uses only its private runtime secret file. Those original local failures and the
initial 250-pass/1-fail regression are retained beside the final evidence.
