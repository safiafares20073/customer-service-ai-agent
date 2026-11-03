# Render deployment preparation (not deployed)

This is an invitation-only synthetic capstone demo. The container and offline
checks are prepared; a public URL and real authentication acceptance are pending.
See [security design and limitations](SECURE_HOSTING.md).

## Approval gates and prerequisites

1. Review and merge the secure-hosting PR only after independent review.
2. Separately approve creating the Render service and persistent disk, after
   checking current account availability, region, TLS/WebSocket support, backup
   behavior and an actual price quote. No deployment has been performed here.
3. Privately configure an OIDC confidential web application and invited reviewer
   issuer/subject pairs. Never send secrets in chat, Git, URLs or screenshots.
4. Deploy with paid mode false and zero budgets. Validate real login, forbidden
   access, expiry/logout, HTTPS cookies and disk restart without model calls.
5. Separately approve any OpenAI spending, principal/global allowance and expiry.
   Only then enable the private paid gate. No paid request is authorized by these
   instructions or by merely approving hosting.

Render is selected for one Docker web service with one persistent disk. The
render.yaml selects starter and 1 GB as a configuration example, not an asserted
current product/price. Verify the service tier supports disks in the chosen region.
Do not use an ephemeral/free service without a durable disk, multiple replicas,
previews that copy private disks, or automatic deploys. Blueprint auto-deployment
is disabled. No Docker registry publication is needed; Render builds the reviewed
Git commit. The only external listener is Caddy on PORT; Streamlit stays private.

## Environment and private secret setup

Commands do not load .env automatically. Production requires Linux and the
container entrypoint; do not publish customer-service-ui --demo or run
ui/hosted_app.py directly as an internet server.

| Variable | Setup / default |
| --- | --- |
| APP_ENV / ENABLE_DEMO_AUTH / UI_PROVIDER | production / false / openai; contradictory values fail closed |
| HOSTED_DATA_DIR | /var/lib/customer-service, an actual mounted persistent volume, never a development database |
| PORT | Render-provided nonprivileged port, default 10000; 8501 forbidden |
| HOSTED_ORIGIN | Exact final HTTPS origin, no path/query; do not accept user-supplied origins |
| OIDC_ISSUER | Exact HTTPS issuer from the selected trusted provider |
| OIDC_METADATA_URL | HTTPS discovery URL on that issuer's origin; provider must support PKCE S256 and required ID-token claims |
| OIDC_CLIENT_ID / OIDC_CLIENT_SECRET | Confidential application credentials, private dashboard; secret at least 16 characters |
| HOSTED_COOKIE_SECRET | Independently generated random secret, at least 48 characters; private dashboard only |
| HOSTED_PRINCIPAL_SECRET | Different random secret, at least 48 characters; stable across restarts; rotation changes opaque principal mapping |
| HOSTED_REVIEWERS_JSON | Private list of objects with exactly iss and sub; default [] grants nobody access; use verified stable subjects, never email as authority |
| HOSTED_SESSION_SECONDS | 900 default/max; 60 minimum; authenticated actions stop after expiry |
| HOSTED_TASKS_PER_HOUR | 5 default, range 1–20 per opaque principal |
| HOSTED_PAID_ENABLED | false; do not change before explicit spending approval |
| HOSTED_GLOBAL_BUDGET_USD / HOSTED_PRINCIPAL_BUDGET_USD | 0 / 0; lifetime estimated USD caps, principal <= global <= 10; no automatic reset |
| HOSTED_APPROVAL_UNTIL | 0; later approved future Unix timestamp, not an indefinite authorization |
| OPENAI_API_KEY or LLM_API_KEY | No value needed for login/health validation; later use dedicated restricted project secret after separate approval |
| OPENAI_MODEL | gpt-6-luna; no model substitution |
| MODEL_PRICING_FILE | /app/config/model_pricing.json; verified Standard snapshot, maximum age 30 days |

Create long independent secrets using a password manager's generator, directly
into the host's secret settings. Do not include actual values in shell history,
this repository, invitation examples, or a public access guide. Keep provider
OAuth tokens unexposed; the generated runtime TOML requests openid only. Use
provider-side MFA/login protection and restrict access to the service dashboard.
Reviewer identities themselves stay private even though they are not passwords.

Register the exact callback HOSTED_ORIGIN/oauth2callback with the provider.
The provider must supply iss, sub, aud, iat, exp and nonce (and azp when required).
There is no email-only fallback, anonymous chat or shared review identity.
Configure the exact provider logout policy separately; application logout revokes
its own login fingerprint even if the provider retains its SSO session.

## Build and offline review

From the repository root, with Docker available:

```sh
uv sync --frozen
docker build -t customer-service-hosted:review .
# Extract the real proxy binary for the nonmocked HTTP/cookie integration test.
container_id=$(docker create customer-service-hosted:review)
docker cp "$container_id:/usr/local/bin/caddy" /tmp/hosting-caddy
docker rm "$container_id"
CADDY_TEST_BINARY=/tmp/hosting-caddy .venv/bin/pytest -q --tb=short
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
uv lock --check --offline
uv build --offline
git diff --check
```

The Caddy test fails if its real binary is unavailable; it is not silently skipped.
In a managed proxy environment only, the optional build flag
--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt supplies existing public
CA trust via BuildKit. Do not disable TLS verification or put private credentials
in build arguments. The allowlisted build context excludes data, artifacts,
submission traces, .env, tests and local auth configuration. Only public source,
model pricing, locked dependencies and Caddy configuration enter the image.

The launcher refuses a missing mount, symlinks, an unprivate data directory,
wrong owner, production fixture data, development accounts and invalid settings.
It starts as root solely to assign the dedicated volume and drops to UID 10001
before starting Streamlit/Caddy/MCP. Never override the entrypoint or expose 8501.
For a local container check, use a new named Docker volume and bind public port
10000 only to 127.0.0.1; a local dummy issuer can check health/startup only and
cannot demonstrate actual authentication. Do not publish the test port.

## Render steps after deployment approval

1. Use the reviewed commit/branch and render.yaml; attach the dedicated disk at
   the fixed path. Confirm one instance and auto-deploy off in the dashboard.
2. Obtain the assigned HTTPS origin, configure the registered exact callback and
   secret variables privately. Keep reviewer allowlist empty until specific
   invitations are approved. Never upload any existing SQLite/evidence files.
3. Start the service with paid false, budgets/approval zero and no API key. Inspect
   only safe startup status. GET /healthz must return 200/ok. A health response or
   the Streamlit HTML shell alone proves neither successful login nor chat.
4. In actual logged-out browsers, verify invitation-only landing in both languages,
   HTTPS redirects, Secure/HttpOnly/SameSite cookie flags, CORS/XSRF and WebSockets.
   Confirm direct database/config paths never serve file contents, and no model
   request occurs on login/health/rejected access.
5. Privately test approved/unapproved subjects and two distinct approved users,
   logout, expired login, cookie replay and disabled invitation. Verify no cross-user
   transcript, task, consent or order access. There are no seeded hosted orders;
   all own-order successes remain local synthetic test evidence.
6. Restart the real service and verify principal isolation and private disk data/
   spending survive. Record deployed commit, platform/date, exact observations
   and a public login URL without identities, access codes or secret query strings.
7. Check desktop and narrow mobile layouts in identified browsers: Arabic RTL,
   mixed IDs/prices, long messages, draft edit/confirm/cancel, keyboard focus and
   generic errors/loading. Offline AppTest is not a pixel/real-browser substitute.
8. Supply individual assessor invitations privately through the approved process.
   Publish only the login URL and clear invitation instructions. No public account
   registration, development token or synthetic shared login exists.

## Optional later approved paid operation

After separate approval, privately set the approved budgets, future approval
expiry, fresh verified pricing and restricted API secret; restart to synchronize
configuration without resetting the ledger. Paid env true alone leaves the initial
kill switch ON. From the private operator shell, as UID 10001 with the same secure
environment and without echoing it:

```sh
/app/.venv/bin/python -m yemen_customer_service.hosting.control enable --allow-paid
# Immediate stop for subsequent requests and ticket writes:
/app/.venv/bin/python -m yemen_customer_service.hosting.control disable
# Content retention operation, preserving all accounting:
/app/.venv/bin/python -m yemen_customer_service.hosting.control purge
```

Do not run enable during this preparation. Inspect backend counters privately;
UI customers see no API accounting. Unknown usage, interrupted reservations or
oversized results lock paid operations persistently; normal enable cannot clear
that state. Do not delete databases, reset counters, loosen task limits or silently
rerun a task to recover. Operator-led reconciliation requires a separate reviewed
procedure. Kill/expiry cannot undo a request already sent to OpenAI.

Back up the complete SQLite database with SQLite's online backup API, or stop the
service before copying database and associated WAL state. Encrypt/restrict backups
and retain the latest accounting record. Before restore, disable paid mode and
kill execution. Never restore an older ledger and re-enable spending without
reconciling all later attempts/costs against preserved records and provider usage.
This workflow is an operational prerequisite, not a claimed tested disaster-recovery
service. Restrict disk/dashboard/shell access to the operator.

## Infrastructure costs and outstanding validation

No infrastructure price has been independently fetched or quoted here. Consult
https://render.com/pricing and https://render.com/docs/disks at deployment time
and record the dated account/region-specific service, disk, backup and traffic
quote before approving charges. An OIDC provider may have separate charges or
quotas; verify those too. Estimated monthly total is the actual quoted fixed
service + disk/backup/traffic + identity-provider charges + usage-derived model
estimate from cost_analysis.md. Do not present the three-task model estimate as
a hosting price or a verified bill. No deployment or paid API charge was incurred
by these preparation tests. Live identity-provider compatibility, real hosted
restart, HTTPS/browser/mobile review and actual assessor access remain pending.
