# Minimum safe hosted-demo design

Proposal only, 2026-11-03 (Asia/Aden). No authentication or hosting implemented.
Preserve one agent, seven existing MCP tools, SQLite, trusted consent and limits.

## Decision and alternatives

| Approach | Security/maintenance implications | Decision |
| --- | --- | --- |
| Publish development UI, shared demo login, or shared password | Reuses synthetic identity authority, merges memory/consent, lacks per-user accountability; network binding is not authentication | Reject |
| Invite-only native Streamlit OIDC plus server-side allowlist | Provider handles login; application maps verified issuer/subject to isolated opaque principals and enforces access; modest integration scope | Recommended minimum |
| Authenticating gateway in front of Streamlit | Can be safe only with verified signed identity, origin bypass prevention and WebSocket coverage; a login page alone is inadequate | Alternative if already available; otherwise adds infrastructure |
| Full production identity/customer lifecycle | OIDC plus enrollment, recovery, administrative roles, real commerce account linking, multi-device task recovery and potentially broader storage changes | Defer; not required for capstone |

Invite-only and full production OIDC are not different authentication protocols.
The minimum uses genuine OIDC, but omits the unnecessary customer lifecycle.
Do not invent a smaller custom password/token system. Confirm Streamlit 1.66.1
native auth support, required optional dependencies, claim availability and cookie
behavior through official documentation and offline tests before coding. If the
chosen provider cannot supply an adequately validated identity, stop and revise.

## Boundaries and intended scope

Browser -> HTTPS Streamlit service -> server-side principal/capability -> existing
single agent -> trusted adapter -> private stdio FastMCP -> persistent SQLite.
Only the provider client makes outbound model requests. OIDC endpoints are used
for login, never offered as tools. MCP and SQLite have no public service endpoint.

- Public URL provides a landing/login screen and synthetic-store disclosure.
  Unauthenticated or unapproved visitors get no agent, record lookup or paid call.
- Invitees authenticate with the identity provider; an explicit server allowlist
  uses stable issuer/subject claims. Email alone, unsigned headers and browser
  customer selectors never establish ownership. OIDC profile claims stay out of
  model context, logs and submission traces; store the minimum opaque mapping.
- Each approved principal gets a separate internal account with no inherited
  demo orders, tickets or memory. The development seed never runs in production.
  Public catalog/policies are the only initial business data. No development
  database, raw evidence bundle or customer records are uploaded to the host.
- Initial hosted scope: catalog/policy chat, isolated conversation memory, and
  explicit confirmed tickets containing synthetic content. No real customer
  data is solicited; explain that text goes to the configured model provider.
  Tickets/memory remain private to the authenticated principal.
- Existing order tools remain registered and enforce ownership, but there are
  no preloaded development orders to expose. A missing order returns generic
  denial. Full own-order success remains evidenced in existing private tests.
  Adding reviewer-specific synthetic orders is a separate approved scope decision,
  never an excuse to expose DEMO-100/DEMO-200 or assign demo-a/demo-b.
- An assessor needing full private-order interaction must receive separately
  approved isolated records/access. Document this hosted limitation instead of
  claiming every seven-tool success scenario is available in the public demo.
- Preserve exact-draft confirmation, edit revocation, cancellation, task counters,
  idempotency and server-side checks. No identity or consent comes from the LLM.
- Logout/expiry revokes local capabilities and pending consent. Do not implement
  automatic cross-device task adoption. Incomplete tasks remain accounted for;
  restart cannot grant a new budget to an old task.

## Host and operational minimum

Prefer Render with one service, one instance, TLS, Streamlit WebSocket support
and an attached persistent disk. Railway is acceptable if current capabilities
and account costs fit better. Platform features, costs and sleep/disk behavior
are prerequisites to verify, not facts validated in Step 1. No deployment account
or billable plan has been selected.

Use a separate production launcher and APP_ENV=production. ENABLE_DEMO_AUTH must
be false; missing/contradictory security configuration fails closed. Use the
platform port and only expose the Streamlit listener. Preserve XSRF/CORS, safe
errors, secret-free logs and private capability transport. Do not modify the
development launcher into a public demo-auth launcher.

Keep the database and durable spending ledger on disk. Bound concurrent active
tasks (initial proposal: one), use transactional reservations, and test busy/error
handling. No horizontal replicas sharing SQLite. Backup/restore must preserve
task and spending history; do not roll back billed usage into fresh allowance.

Place OpenAI key, OIDC client secret and cookie secret in host secret settings.
Do not put them in render.yaml, Git, browser controls or public instructions.
Set gpt-6-luna, Standard/default tier and reasoning_effort none; load dated verified
pricing and fail closed for stale/unknown configuration. Retain all per-task
limits. Require separately approved per-principal/global allowance, expiry time,
rate limits and an operator kill switch. No paid startup/health check or automatic
smoke test. Provider alerts do not replace an application-wide reservation gate.

Proposed retention for review: automatically expire capabilities/consent at their
existing TTL, and delete demo conversation/ticket content after seven days or
the review window, whichever comes first. Keep minimal audit/cost accounting
through reconciliation without retaining raw messages or identifiers. Final
policy needs approval and tests; deleting content must not reset spending limits.

## Required tests and release gates

See the exact file/test inventory in PHASE_5_STEP_1.md. Before deploying, offline
tests must cover denied login, origin/configuration failures, no-demo initialization,
principal isolation, logout/expiry, ticket edit/confirm/cancel/replay, persistent
limits and shared spending races through actual MCP sessions and provider fixtures.
New authentication fixtures must be clearly labeled; no fake live login claims.

After separate approval, real hosted acceptance requires a logged-out browser,
approved and unapproved OIDC users, two isolated approved principals, restart
persistence, HTTPS/WebSocket checks, safe operational failures and a privately
recorded deployed commit. Login tests themselves must not trigger model calls.
Live chat needs separate paid authorization. A reachable health endpoint alone
does not prove login, application correctness, privacy or persistence.

Check English/Arabic mixed text and IDs, RTL, mobile width, draft controls,
loading/errors and keyboard access on identified browsers. Distinguish AppTest,
emulation and real-device results. Document unavailable checks.

The chapter requires a public URL but does not state anonymous access. An
authenticated public URL with private assessor invitations is the proposed safe
interpretation. Confirm assessor access expectations before final submission.
If anonymous chat is later required, redesign public-read-only capabilities and
abuse/spending protections; do not weaken this boundary by enabling demo auth.
