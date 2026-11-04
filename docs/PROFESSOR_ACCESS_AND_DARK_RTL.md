# Original dark theme, assistant RTL and simple Google invitations

Review candidate prepared November 4, 2026, from merged main
`7898fcd388c5dfe0a88c01711e8e5780557ecb7f`. The owner reports successful Railway
OpenAI chat, Google login and ticket workflow. This change was not deployed or
verified against the hosted service. No live variables, identities, credentials,
SQLite volume, records, approved USD 3 allowance or expiration were changed.

## Exact visual reference and restoration

The pre-polish reference is `a9bae01d0d8f8ba57b97185d56bf0f5846073626`, immediately
before final-capstone-submission-polish commit f2d5a9a. Its shared renderer used
Streamlit's native appearance, 12 px chat corners and no custom palette. There
was no committed private/original color configuration to reconstruct.

Removed the later forced light background, navy/teal colors, colored user bubbles,
custom avatar backgrounds, typography/padding and light input overrides. Both
existing launchers now select Streamlit's built-in dark base. Caddy, entrypoint,
ports and all working controls remain. This restores the native dark appearance
rather than inventing another palette. A manually saved browser theme preference
may need Settings -> Theme -> app theme/Dark; no browser settings are changed by
this preparation.

Measured in local Chromium: background #0e1117, text #fafafa, original native
coral primary background #ff4b4b. Body contrast is 18.11:1. The only color
adjustment is the primary label using native dark #0e1117, increasing contrast
from 3.30:1 with white to 5.72:1. No alert, input or chat background is repainted.
These measurements cover selected targets, not an exhaustive accessibility audit.

## Bot response RTL, not just page CSS

Existing page/input/form/notification RTL remains. Assistant Markdown now uses
native containers with server-generated direction/index keys and scoped rules for
paragraphs, headings, lists, list items and blockquotes. Message direction uses a
small strong-script word heuristic (ignoring inline code and USD), with page
language as tie-breaker. It is presentation only; it never authorizes actions or
turns model text into CSS. Ambiguous very short mixed-language answers can still
need human review; the tested Arabic/English/mixed cases are recorded below.

Arabic lists have outside markers, padding-inline-start on the right and no left
padding. Pure English responses retain LTR/left alignment even when the page is
Arabic. Code identifiers stay LTR and unicode-bidi isolated; inline Latin product
names and numeric prices use the browser's normal bidi handling. Bold, safe
Markdown, redaction, escaped HTML and disabled external media are preserved.
No unsafe HTML was enabled. User text remains plain, and ticket controls unchanged.

## Private professor setup: email first, verified subject thereafter

These are operator steps for a separately approved deployment of this reviewed
commit. They were **not executed** during development. The professor only needs
the demo link and their own approved Google account.

1. In Google Auth Platform -> Audience/Test Users, if the existing consent app is
   External/Testing, add the professor's **primary Google account email** as a Test
   User. This permits Google's consent screen, not application access. Keep the
   current OAuth client, secret, issuer and callback configuration.
2. In the existing Railway service's **Variables**, add
   `HOSTED_REVIEWER_EMAILS_JSON` as a private JSON array of exact primary account
   addresses. Format illustration only: `["professor@example.invalid"]` (replace
   the invented .invalid address privately). Preserve existing array entries when
   adding people. Case is normalized; dots, plus aliases, forwarding addresses and
   domain variants are not merged. Use the email Google actually verifies for that
   primary account, never a guessed alternate address.
3. **Do not replace HOSTED_REVIEWERS_JSON.** Existing issuer/subject invitations
   remain independently valid. Do not change any keys, USD 3 global allowance,
   per-principal limits, approval expiry, kill state, volume or ledger. Do not
   reapply fresh-deployment zero-budget defaults or native IaC during evaluation.
4. After review and separate deployment approval, deploy the reviewed code through
   the normal controlled process using the **same volume**. Startup requests
   `openid email` only when email invitations are configured and performs the
   additive migration below. No secret/client/callback replacement is needed.
   Complete pending ticket drafts before any normal service restart.
5. The professor opens
   https://yemen-customer-service-review-production.up.railway.app, clicks
   **Sign in with Google**, and selects that approved Google account. A valid first
   login binds the invitation automatically. No OAuth Playground, manual subject,
   ID token, password, authorization code, API key or Railway access is needed.
   If an earlier signed-in cookie predates the email scope, use Sign out and sign
   in again. Other existing invited users are not forcibly logged out by migration.
6. Verify real login and isolation privately after deployment. Login itself never
   calls OpenAI. Any chat evaluation must stay within existing approved spending
   and expiry. Do not issue paid calls just to test enrollment here.

Only the expected Google issuer is supported for email invitations. Native
Streamlit/Authlib still cryptographically validates the OIDC exchange/signature,
state/nonce and claims. Application checks issuer, subject, client audience/azp,
nonce, iat/exp and maximum session age before any enrollment write. The first
binding additionally requires email_verified to be the boolean true and an exact
case-normalized private invitation match. Model messages, widgets, unsigned
headers and caller-supplied emails cannot enroll anyone.

After enrollment, authorization uses the immutable opaque principal derived from
HMAC(verified issuer, subject), not email alone. A renamed or absent email claim
cannot change that principal; an explicit unverified email claim is rejected on
the email-invitation route. Another subject claiming the old approved email is
denied. Pre-existing explicit issuer/subject invitations retain their original
independent authorization semantics and do not suddenly require an email claim.

To revoke email-only access, remove its address from the private array and apply
through the approved configuration/restart process. If the same identity is also
explicitly invited in HOSTED_REVIEWERS_JSON, that independent grant must be removed
too. Removal/re-addition never releases the old binding or resets spend. A changed
subject requires operator investigation and a separate reviewed recovery decision;
there is no public reset/rebind/admin endpoint. Do not delete a binding or database
to bypass an account-substitution denial.

## Additive storage and backward compatibility

The base SQLite schema remains 2 and hosted schema remains 1. A separate additive
`hosted_email_invitation_version=1` extension creates `hosted_email_invites` with
email HMAC, opaque bound principal, enabled flag and binding timestamp. Raw emails,
Google subjects, tokens and profiles are not stored in it, model memory or logs.
No existing table/record is dropped or replaced. Migration and metadata commit in
one SQLite write transaction; re-running is idempotent and unknown versions fail
closed. Existing startup/data-volume permission checks remain.

Existing principal IDs, signed login fingerprints, capabilities, customers, memory,
consent, tasks, usage, budgets and revocations are not rekeyed or reset. Configure
continues to honor the old subject list and active email bindings. Atomic first
binding serializes competing subjects; only one wins. Logout/expired/revoked
fingerprints cannot enroll or regain access through the new route. Active signed
cookies remain bearer credentials as before; this is not a claim of sender-bound
cookies or protection against every cookie-theft scenario.

Older binaries can ignore the additive table and retain legacy-list access, but
they do not understand email enrollment and may disable email-only principals
when they apply their old configuration. Rollback must be reviewed; never delete
migration metadata, restore an older spending ledger or replace the volume to make
an old image run. A normal deployment may reconnect Streamlit tabs; migration
preserves database sessions/data, not in-memory pending forms across process exits.

## Actual validation and remaining release gates

New tests use synthetic identities/keys and actual SQLite/Authlib, with offline
HTTP transports that reject unexpected requests. They cover verified case-only
matching, wrong/unverified/forged/expired claims, changed subject, concurrency,
logout replay, additive migration/restart, legacy sessions/memory/accounting,
private scope configuration and the real hosted UI path without a provider call.
No fixture is presented as a live Google or OpenAI exchange.

Local Chromium 154, desktop 1280x960 and mobile emulation 390x844: actual assistant
paragraph/list/item/heading direction RTL, right alignment, marker direction RTL,
right padding 24 px / left 0, bold rendered, code LTR/isolate, mixed Example
Headphones / 25 USD / P-100 readable. English replies on the Arabic page remain
LTR with left-side list gutter. Native dark colors restored, mobile has no
horizontal overflow, and real pointer cancellation is unobscured. Screenshots
were inspected; this is local fixture UI evidence, not hosted/mobile-device proof.

Exact final commands/counts are recorded below after completion. All original
security tests, seven MCP wire contracts and official trace/cost files remain.
Initial failures (offline metadata fixture cache setup and a test-only missing
import) are retained privately under artifacts/dark-rtl-access; no production
check was bypassed to make them pass.

**GO for independent review. Hosted GO remains conditional:** after separate
review/deployment approval, verify the professor's actual first Google login,
legacy users, existing allowance/expiry, real Arabic responses on narrow/desktop
browsers, ticket edit/Confirm/Cancel and same-volume persistence. The owner reports
these business flows already work on the prior deployed version; the new version
has not been deployed or independently validated on Railway here.

## Final executed results

- Full suite: **330 passed, 0 failed, 0 skipped**, 104.90 seconds; one existing
  Authlib httpx deprecation warning. All 283 baseline cases retained unchanged;
  40 email/enrollment/migration cases and seven presentation cases added.
- New invitation end-to-end cases use the actual hosted controller and genuine
  MCP for products/policies and ticket Confirm/Cancel, SQLite writes/audits,
  isolation, stable accounting and revoked-cookie denial. No paid model was used.
- Actual local Chromium desktop/mobile and screenshot inspection passed all
  response-direction, list gutter/marker, native dark palette, bold/code/isolation,
  no-overflow, contrast and pointer-cancellation checks described above.
- Ruff check and format passed (103 Python files); 63 installed Python packages
  have no conflicts; frozen uv lock check resolves 66 packages. Offline source
  distribution and wheel builds passed. No runtime dependency/lockfile changed.
- Four native Railway SDK configuration checks passed; the new private variable
  is preserve-only. Deployment-tool npm audit reports zero known vulnerabilities;
  this is not a Python CVE audit or external penetration test.
- Standard `docker build --check .` passed with no warnings. Dockerfile is unchanged;
  no fresh full-image success is claimed. The known cloud intercepting-proxy CA
  limitation and owner-reported existing Railway operation remain separately
  documented. No CA, insecure flag, secret or deployment workaround was added.
- Whitespace, relative links, credential/artifact inventory and baseline byte/hash
  comparisons passed. Original three JSONL traces and cost_analysis.md are unchanged.
  No generated database, attempt lock, bundle, private settings or screenshots
  are included in this review branch.

Commands: `.venv/bin/pytest -q --tb=short`, `.venv/bin/ruff check .`,
`.venv/bin/ruff format --check .`, `uv pip check --python .venv/bin/python`,
`uv lock --check --offline`, `uv build --offline`, `npm test --prefix .railway`,
`npm audit --prefix .railway`, `docker build --check .`, `git diff --check`.
Managed checks used a writable /tmp cache and execution permissions for real
subprocess/loopback communication. Initial failed reports are retained, not
reclassified as passing or live evidence. No existing regression was weakened.

## Exact intended files

- `.env.example`
- `.railway/railway.ts`
- `.railway/test-config.mjs`
- `README.md`
- `docs/FINAL_DEMO_GUIDE.md`
- `docs/FINAL_SUBMISSION_CHECKLIST.md`
- `docs/REQUIREMENTS_MATRIX.md`
- `docs/PROFESSOR_ACCESS_AND_DARK_RTL.md`
- `src/yemen_customer_service/hosting/auth.py`
- `src/yemen_customer_service/hosting/invitations.py`
- `src/yemen_customer_service/hosting/launch.py`
- `src/yemen_customer_service/hosting/settings.py`
- `src/yemen_customer_service/hosting/store.py`
- `src/yemen_customer_service/ui/chat.py`
- `src/yemen_customer_service/ui/hosted_app.py`
- `src/yemen_customer_service/ui/launch.py`
- `src/yemen_customer_service/ui/presentation.py`
- `tests/hosting/test_email_invitations.py`
- `tests/ui/test_dark_rtl.py`
