# Railway Free deployment preparation: invitation-only live OpenAI chat

Current owner update (November 4): the service is deployed with Google OIDC/live
chat. See [FINAL_DEMO_GUIDE.md](FINAL_DEMO_GUIDE.md) and
[FINAL_VALIDATION.md](FINAL_VALIDATION.md). The preparation steps below are retained
for reproducibility, not instructions to reset the existing USD 3 authorization,
allowlist or persistent volume. Final polish was not deployed automatically.

Prepared November 4, 2026 (Asia/Aden), from merged main
`cedc24cc800b83fb60c9a9a4f6ad89d3a0090e80`. **Verdict: CONDITIONAL** for a bounded
review window, subject to the resource results and account checks below.
Nothing has been deployed, upgraded or provisioned, and no paid model calls ran.
The real OpenAI chat implementation remains available for separately authorized
activation; provider fixtures are confined to tests.

## 1. Verified official sources and Free restrictions

The rendered Railway/OpenAI documentation sites are blocked by this environment's
proxy (CONNECT 403). Railway's publicly accessible **official documentation source**
was independently read at railwayapp/docs commit
`dcbeb29573190a245d9af7cc43fbbdde0dee7375` (October 30, 2026), on November 4.
These are source-document checks, not observations of your Railway account.
Sources and reproducible permalinks:

| Topic | Official page | Source at reviewed commit |
| --- | --- | --- |
| Plans and usage prices | https://docs.railway.com/pricing/plans | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/pricing/plans.md |
| Free vs trial / network verification | https://docs.railway.com/pricing/free-trial | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/pricing/free-trial.md |
| Persistent volumes / limitations | https://docs.railway.com/volumes/reference | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/volumes/reference.md |
| Mount timing and ownership | https://docs.railway.com/volumes | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/volumes.md |
| HTTPS, WebSockets and networking | https://docs.railway.com/networking/public-networking/specs-and-limits | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/networking/public-networking/specs-and-limits.md |
| Startup health checks | https://docs.railway.com/deployments/healthchecks | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/deployments/healthchecks.md |
| Native configuration | https://docs.railway.com/infrastructure-as-code | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/infrastructure-as-code.md |
| Limits / sleeping | https://docs.railway.com/pricing/cost-control | https://github.com/railwayapp/docs/blob/dcbeb29573190a245d9af7cc43fbbdde0dee7375/content/docs/pricing/cost-control.md |

The documented **Free**, rather than Trial, per-service maximums are one replica,
0.5 GB RAM, 1 vCPU, 1 GB ephemeral writable storage, 0.5 GB volume and 4 GB image.
Free permits one volume per project. The subscription is USD 0/month with USD 1
monthly credit, not unlimited free compute; unused credit does not roll over.
Trial is distinct: a one-time USD 5/30-day grant, different resources, and restricted
outbound access for Limited Trial accounts. Do not assume trial resources on Free.
GitHub verification is automated; if OIDC/OpenAI egress is unavailable, **stop**,
without upgrading. No Hobby plan, card entry, purchased credits or paid resource
is authorized by this preparation. Account-specific entitlements remain unverified.

Volumes exist only at runtime, not in builds or pre-deploy commands. Railway mounts
them as root. The existing launcher assigns only the dedicated directory and then
permanently drops to UID 10001. Replicas cannot share a volume. Volume redeployment
has downtime despite health checks; Free volume expansion is unavailable. Plan
expiry/credit exhaustion can take the demo offline and retention is not indefinite:
the source lists Free/Trial data deletion 30 days after expiry. Retain private
backups; do not rely on a Free volume as a permanent archive.

## 2. Small architecture and configuration

Keep the existing Dockerfile and Python implementation unchanged:

Browser HTTPS -> Railway edge -> Caddy on PORT -> Streamlit 127.0.0.1:8501 ->
validated invitation/principal -> existing agent -> genuine private MCP subprocess ->
private SQLite. Only the official OpenAI SDK sends model requests.

The native configuration is [.railway/railway.ts](../.railway/railway.ts), using the
pinned railway 3.12.0 authoring SDK. This is deployment tooling only, not a new
application dependency or a second agent. It declares one Docker service, one
500 MB private volume at /var/lib/customer-service, /healthz, 120-second startup
health timeout, no automatic crash restarts, optional serverless sleep, one CPU
and a conservative 500,000,000-byte RAM cap. It leaves Docker ENTRYPOINT intact,
sets PORT=8080 and never initializes data in a pre-deploy command. The configured
region us-west2 is an example from the official reference; confirm availability
and service/volume co-location before provisioning. Do not request a larger disk.

**Do not add railway.json or railway.toml:** current official source says new
services cannot opt into that deprecated configuration system; legacy reads end
December 1, 2026. Merely connecting the GitHub repository does not apply the new
IaC file. Use the dashboard procedure below, matching its values, or a separately
reviewed native CLI plan/apply after explicit deployment approval. No automatic
apply/deploy GitHub workflow is provided.

The IaC preserves private settings without writing values into Git. Its safe
public defaults always set paid false, budgets zero and approval expiry zero.
Reapplying it during a paid review window disables that authorization; it never
resets accounting. Do not inline secrets or use CLI flags that show/export values.
The definition cannot select or verify an account subscription. Check Free in the
dashboard before any create/apply, and reject any upgrade/payment prompt.

## 3. Private variables and OIDC configuration

Use Railway service variables (sealed secrets where supported), never Docker
build arguments, committed .env files, source, screenshots or public invitations.
The Docker allowlist excludes databases, evidence, tests, traces and local secrets.

| Variable | Required setting |
| --- | --- |
| APP_ENV / ENABLE_DEMO_AUTH / UI_PROVIDER | production / false / openai |
| HOSTED_DATA_DIR | /var/lib/customer-service, an actual dedicated mounted volume |
| PORT | 8080, matching public domain target and health checks; worker 8501 stays private |
| HOSTED_ORIGIN | Exact assigned HTTPS origin without path/query |
| OIDC_ISSUER / OIDC_METADATA_URL | Exact trusted HTTPS issuer and discovery URL on the same origin |
| OIDC_CLIENT_ID / OIDC_CLIENT_SECRET | Private confidential web-app settings; secret at least 16 characters |
| HOSTED_COOKIE_SECRET / HOSTED_PRINCIPAL_SECRET | Separate random values of at least 48 characters, distinct from client secret; generate directly in a password manager and place privately in host settings |
| HOSTED_REVIEWERS_JSON | Private list of exact iss/sub objects; unset defaults to []; no email-only authority or public identity selector |
| HOSTED_SESSION_SECONDS / HOSTED_TASKS_PER_HOUR | 900 / 5 defaults; maximum session 900 seconds, rate 1–20/hour |
| OPENAI_MODEL | gpt-6-luna only; no model/tier fallback |
| MODEL_PRICING_FILE | /app/config/model_pricing.json |
| OPENAI_API_KEY or LLM_API_KEY | Absent during no-cost deployment acceptance; after separate approval, restricted OpenAI project secret in private variables only |
| HOSTED_PAID_ENABLED | false during preparation and initial deployment |
| HOSTED_GLOBAL_BUDGET_USD / HOSTED_PRINCIPAL_BUDGET_USD | 0 / 0 until separately approved; principal <= global <= 10 USD; lifetime estimated caps |
| HOSTED_APPROVAL_UNTIL | 0 until separately approved future Unix timestamp |

Do not set developer variables UI_CUSTOMER_ID, UI_PAID_APPROVED, CS_SESSION_TOKEN,
HOSTED_MODE or enable demo auth on the public service. Do not change the principal
secret casually: it determines stable data/spending identity. Native OIDC scopes
are openid with PKCE S256; provider must return iss/sub/aud/iat/exp/nonce (and azp
when needed). Register the exact HOSTED_ORIGIN/oauth2callback. Use provider-side
MFA/login protection. Supply each assessor's invitation privately, never shared
accounts/access codes. No reviewer records or credentials have been created here.

Server-side invitation checks, audience/expiry validation, 15-minute maximum
application login age, durable logout/replay revocation, separate task capabilities
and principal memory remain intact. Caddy appends Secure to native HttpOnly/Lax
cookies, preserves XSRF/CORS and prevents direct Streamlit origin access. Real TLS,
OIDC redirects and WebSockets still require deployed browser verification.

## 4. Exact Free deployment procedure — later approval required

1. Review and merge this PR. Separately approve a bounded Railway Free deployment
   window; nothing in these steps authorizes a paid plan or any model request.
2. In Railway, verify the actual Free account, remaining credit, volume entitlement,
   region and outbound network eligibility. A new Trial is not proof of Free
   capability. If required features/credit are unavailable, stop. Do not enter a
   payment method or accept an upgrade to resolve it.
3. Create an empty project/service only after approval. Disable automatic GitHub
   deployments/PR environments. Do not attach a build source that auto-starts
   deployment until storage and private settings are prepared. Do not import the
   Render blueprint or a template that provisions another database/service.
4. Attach the single default Free 0.5 GB volume at /var/lib/customer-service.
   Start with fresh data, never upload development SQLite or evidence bundles.
   Match region to the service, one replica, CPU <=1, RAM <=0.5 GB. IaC requests
   500 MB, within the documented ceiling; if rejected, use the allowed default
   0.5 GB size after verifying it without upgrading or resizing.
5. Privately configure the variables above with paid false, zero budgets/expiry,
   no API key and initially no invited reviewers. Keep the standard Dockerfile
   and ENTRYPOINT, with **no start/build/pre-deploy override**. Configure /healthz,
   120-second timeout, restart Never and PORT=8080. Serverless is optional and is
   not an uptime/free-cost guarantee. No background automatic model job exists.
6. Generate a Railway-provided HTTPS domain from service Settings -> Networking
   -> Public Networking, target port 8080. Set its exact HOSTED_ORIGIN and register
   its callback with the private OIDC application. Configure provider settings
   and individually approved invitations privately. Do not publish their values.
7. Connect only safiafares20073/customer-service-ai-agent at the reviewed merged
   commit/main; use Docker detection. Check settings and available credit before
   manually approving the first deploy. If connecting triggers an early failed
   startup, keep paid off and correct configuration; never bypass mount/auth gates.
8. Wait for /healthz = 200/ok, including Railway health-check hostname
   healthcheck.railway.app. Health checks gate startup only, not continuous
   monitoring or authenticated correctness. The HTML shell alone proves no login.
9. With no model calls, verify actual HTTPS/redirects, Secure/HttpOnly/Lax cookies,
   CORS/XSRF, WebSocket connection, logged-out landing and rejected users. Check
   approved login, logout/expiry/replay and two invited users' isolated sessions.
   Probe private file routes without printing contents. Never expose port 8501,
   a database download endpoint, debug logs or a public administration route.
10. Verify outbound HTTPS reaches the selected issuer and api.openai.com from the
    service without a model request. An unauthenticated /v1/models 401 is only
    reachability evidence, not model/account compatibility. Limited Trial egress
    restrictions, provider availability or missing Free eligibility are blockers.
11. Restart the actual service during the approved window; confirm the same disk,
    task/accounting data, revocations and disabled-paid/kill state survive. Use
    private operational checks, not public DB viewers or an evidence export.
12. Record deployed commit, date, real login/restart results and resource/credit
    observations privately; publish only the verified login URL. Perform actual
    English/Arabic desktop/narrow-screen checks before claiming a working demo.

Native IaC is an optional matching configuration path: Node >=22.18, Railway CLI
>=5.42.1 and .railway's locked SDK are required. Privately link the correct Free
account/project after approval, then review railway config plan. Do not run
config apply, --yes, --confirm-destructive or a deployment command during
preparation. Apply can provision resources and trigger builds; plan does not
prove a Free account, affordable operation, valid IdP or live model support.
A new empty service may lack preserved secrets and refuse startup until configured.
The dashboard path avoids accidentally applying or deleting other resources.

## 5. Enable real OpenAI chat only after separate spending approval

The production path uses AsyncOpenAI, Chat Completions, Standard/default processing,
reasoning_effort="none", tool discovery and actual MCP invocation. No fixture
provider can be selected through the hosted environment. The independently
reviewed historical traces remain separate from current live validation.

The approved November 3 pricing snapshot lists gpt-6-luna USD 0.10 input, 0.50
output and 0.01 cached input per million tokens. It is within its 30-day freshness
window on November 4. Model/account availability and current pricing cannot be
newly verified here because the official OpenAI pages are blocked. Before paid
activation, verify the official model/pricing pages and account availability;
never alter the verification date without actual evidence or silently substitute
a model/mode. Expired/unknown pricing is refused. Account failure is a blocker,
not permission to downgrade the model or replace live responses with fixtures.

After explicit approval of total/per-reviewer allowances and a review expiry:
privately set the restricted API key, the approved positive budgets, future
HOSTED_APPROVAL_UNTIL and HOSTED_PAID_ENABLED=true; restart to synchronize
configuration. Initial durable kill is still ON. In the private service shell,
as UID 10001 and using the existing secure environment, enable deliberately:

```sh
/app/.venv/bin/python -m yemen_customer_service.hosting.control enable --allow-paid
```

Do not execute this during preparation. No further application code change is
needed for activation under the approved model/pricing. Only then may individually
invited reviewers submit real messages and receive real model/tool responses.
Test one separately approved hosted task before advertising live chat as verified.
An assessor requiring an own-order success needs separate approved isolated data:
there are no preloaded orders. All seven tools remain registered and protected;
product/policy chat, scoped memory and explicitly confirmed tickets are available.

Limits remain USD 0.05 estimated, 8 model requests including attempts, 60 cumulative
active seconds and 10 seconds/tool. Shared/principal lifetime reservations,
one-operation concurrency, rate limits, expiry and kill are checked server-side.
Missing usage/interrupted reservations/over-bound results cause sticky blocking
across restarts. Do not clear counters, delete attempts or reset a database to
recover. An in-flight call can incur usage after expiry/kill; estimates cannot
guarantee an exact OpenAI invoice ceiling. Use restricted provider project controls
and alerts too. Railway's own AI Agent usage controls do not cap this separate
OpenAI API key; infrastructure and model budgets are independent.

Emergency stop (no new model call):

```sh
/app/.venv/bin/python -m yemen_customer_service.hosting.control disable
```

Also set HOSTED_PAID_ENABLED=false, expiry=0 and restart, or stop the service in
Railway. An environment change requires restart/configure; the private disable
command updates the durable gate immediately. Do not use a process-kill loop as
a budget reset. Preserve accounting and reconcile uncertain usage privately.

## 6. Credit, persistence and operational limits

The reviewed official container rates are RAM USD 10/GB-month, CPU USD
20/vCPU-month, egress USD 0.05/GB, and used volume storage USD 0.15/GB-month.
These are dated source rates, not a Railway invoice or guarantee of current
account billing. Free credit is only USD 1/month. Remaining credit, not merely
resource limits, determines whether a review stays free. Recheck the account
before deployment; do not upgrade or purchase credits if it runs out.

Estimate a short window from measured GB-hours, CPU-hours, actual used disk and
egress. Continuous 0.2 GB RAM alone would be approximately USD 2/month at the
quoted monthly rate, before CPU/egress/storage: do not promise 24/7 free uptime.
Measured health-only idle RAM is not a fully loaded reviewer session. Actual
usage meters may differ from local cgroup measurements. OpenAI usage is separate,
paid only after its own approval, and not covered by Railway credit.

The official usage-control source gives a USD 10 minimum hard limit: do not
claim a configurable USD 1 Railway hard cap. Verify Free credit-exhaustion/account
behavior privately, watch remaining credits and stop manually before depletion.
Source rules state workloads stop at exhausted credit; availability still requires
account confirmation. This is a bounded scheduled academic review, not an uptime SLA.

Serverless sleeps after no outbound packets (roughly 5–10 minutes); open Streamlit
WebSockets, responses and OIDC/model traffic can prevent sleeping. Cold wake may
return 502 and is not a data-loss or auth-bypass reason. Never rely on sleep to
keep spending within the Free credit. Free restart Always is unsupported; this
configuration uses Never to avoid unattended crash loops. Manual recovery retains
the disk and sticky cost state. Resource exhaustion mid-call leaves an uncertain
reservation and correctly blocks future paid calls.

Keep private backups with SQLite's online backup API or stop the service before
copying database/WAL state. Never restore older usage into a fresh allowance.
Disable paid mode before restore and reconcile the newest accounting privately.
The seven-day content purge is startup/manual, not an automatic retention SLA:
run the private purge during/after the review while retaining cost/audit/revocation
records. Do not delete the volume to save credits until private backups and
accounting are secured. Monitor its small capacity; purge content without erasing
spend records, and stop safely rather than silently upgrading when full.

## 7. Reproduce offline verification and common failures

```sh
uv sync --frozen
docker build -t customer-service-railway:review .
# Standard build: no secret mounts or session-specific certificate override.
container_id=$(docker create customer-service-railway:review)
docker cp "$container_id:/usr/local/bin/caddy" /tmp/hosting-caddy
docker rm "$container_id"
CADDY_TEST_BINARY=/tmp/hosting-caddy .venv/bin/pytest -q --tb=short
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
uv lock --check --offline
uv build --offline
npm ci --prefix .railway --ignore-scripts
npm test --prefix .railway
npm audit --prefix .railway
.venv/bin/python -m tests.hosting.railway_resource_probe --run-local-containers --image customer-service-railway:review
git diff --check
```

The resource probe starts **only local loopback containers**, with fake OIDC
settings, no API key, zero paid budgets in the real hosted database and a separate
fixture-mode database for workload tests. Its explicit flag is mandatory. It
copies only public fixture source read-only, exercises the official SDK HTTP
fixture and genuine MCP, bilingual AppTest, product/policy chat, memory and exact
ticket confirmation. It retains unique reports, failures, stopped containers and
private volumes in ignored evidence. Do not run it against a real hosted service,
copy its fixture database to Railway, or label its JSONL as live evidence.

| Problem | Safe response |
| --- | --- |
| Startup refused | Check private required variables, actual mount path/ownership and separate secrets without printing values; never bypass validation |
| Health 503/timeout | Match PORT/domain target 8080, /healthz, Railway health hostname and Docker entrypoint; do not start a second public Streamlit listener |
| Root/nonroot volume error | Preserve the root entrypoint's brief assignment and UID drop; do not chmod database 777 or remove the mount guard |
| OIDC denied/callback error | Verify exact origin/callback, issuer/discovery, aud/azp, nonce, expiry and private issuer/subject invitation; no email/unsigned-header fallback |
| Chat temporarily unavailable | Inspect private paid flags, expiry, allowances, kill and sticky unknown state; no customer cost/debug panel or automatic enable |
| Limited outbound / model unavailable | Stop; resolve eligibility/current provider support privately without a paid Railway upgrade or model substitution |
| OOM/crash/disk full | Retain failure evidence, disable paid calls and inspect resource/disk state; do not erase accounting, retry writes or remove functionality |
| Cold-wake 502 / credit exhausted | Observe account metrics; allow a manual page retry only for availability; do not replay a task or promise uninterrupted Free hosting |

## 8. Final academic hosted acceptance (not yet completed)

- [ ] Actual Free account/region/remaining-credit/egress entitlement verified.
- [ ] Reviewed commit deployed manually, one mounted volume, HTTPS login URL recorded.
- [ ] Real approved/unapproved OIDC users, logout/expiry/replay and two-user isolation pass.
- [ ] Real browser Secure/HttpOnly/Lax, CORS/XSRF/WebSocket and private-file denials pass.
- [ ] Actual Railway restart preserves scoped data and all spending/kill records.
- [ ] Desktop/mobile English/Arabic/RTL, mixed IDs/prices, keyboard focus/loading/errors reviewed.
- [ ] Independently current model/pricing/account compatibility confirmed; separately approved key/budgets/expiry/enable configured privately.
- [ ] One separately approved hosted OpenAI conversation uses real MCP with grounded answer and recorded usage; billing still requires invoice reconciliation.
- [ ] Exact draft edit/confirm/cancel/replay, rate/concurrency and emergency stop checked safely.
- [ ] Individual assessor invitations supplied privately and credit window monitored.

The original three submission traces and cost_analysis.md are unchanged. Actual
OIDC/browser/provider validation, Free account eligibility, uptime/credit duration
and Railway-specific restart observations are pending, not inferred from tests.

## 9. Actual offline results and measurement limits

- Full regression: **258 passed, 0 failed, 0 skipped**, 80.08 seconds, one upstream
  Authlib httpx deprecation warning. This includes all 251 baseline tests unchanged
  plus six PORT wiring/invalid-port guards and one explicit local-probe opt-in guard.
- Native IaC SDK: **4 passed, 0 failed/skipped**; pinned SDK 3.12.0, Node 24.19.0,
  npm 11.9.0. Frozen npm ci succeeds; npm audit reports zero known vulnerabilities
  for this authoring dependency graph. No Railway CLI/account plan or apply ran.
- Python workspace: 3.12.14; MCP 1.30.0, OpenAI 2.54.0, Streamlit 1.66.1, Authlib
  1.9.3. Ruff lint/format, dependency compatibility, frozen uv lock, source/wheel
  build, whitespace, unchanged-original and credential/artifact reviews passed.
- Local Docker production image (Python 3.12.16): 1,063,333,915 bytes, below the
  documented 4 GB image maximum. Cgroup RAM limit was 499,998,720 bytes after Linux
  page rounding from requested 500,000,000; one vCPU, zero swap. Health-only idle
  current RAM: **96,833,536 bytes**. Peak including AppTest, five scripted SDK
  calls, real MCP and monitoring: **235,720,704 bytes (224.8 MiB)**. An earlier
  same-code image sample peaked at **236,281,856 bytes (225.3 MiB)**; the README
  reports that higher observed sample. No OOM/kill in either successful run.
- Actual local PORT=8080 proxy/health works with healthcheck.railway.app hostname;
  tested private paths return no database/secret contents. Main hosted database
  keeps zero customers/calls and kill ON/paid OFF. A real container restart retained
  its SQLite sentinel and disabled gates. Writable image layer: 0 bytes at that
  observation; combined private test-volume file payload: 317,023 bytes, below
  0.5 GB. The local named volume itself is not quota-limited; actual Railway
  capacity, filesystem overhead and retention must still be checked there.

The Railway-tagged tested image was
sha256:5f933b52bdf5d8eaebd3973963cac69db16dc74ec95ca5673ee5bf2cd99e0b6b.
Its production Python/config files match merged main; subsequent documentation
updates record the final test counts.

The peak includes a separate test-driver process running actual AppTest/controller
alongside the real web/proxy worker and MCP. It is a finite conservative sample,
not a multi-user browser or sustained live-model benchmark. Page cache counts
in cgroup usage; there is no inference of provider billing from these numbers.
Longer chats, more sessions, backups, growing memory/audits and platform overhead
can differ. Monitor the actual service during its approved review window.

Retained ignored evidence includes the initial npm offline-cache miss, a probe
page-rounding assertion, fixture directory permission failure and an overly broad
probe assertion that mistook AWAITING_CONFIRMATION's audited deny for an MCP fault.
Those were probe/setup defects; production code and prior tests were not changed
to make them pass. Original failure records, unique reports, fixture databases and
stopped local containers/volumes remain private. Only the original reviewed three
JSONL files remain official submission traces.


## Dockerfile compatibility correction — November 4, 2026

The supplied actual Railway build failed during Dockerfile validation:

> dockerfile invalid: flag '--mount=type=secret,id=proxy_ca' is missing a
> type=cache argument (other mount types are not supported)

The original lines 8, 12 and 18 used optional BuildKit secret mounts for a managed
cloud proxy CA. Railway rejects the mount syntax before executing RUN, regardless
of whether the optional file exists. The correction removes all three secret
mounts and their conditional PIP_CERT/SSL_CERT_FILE exports. Each RUN now executes
its original pip/uv command directly, with normal verified HTTPS trust. No custom
certificate, credential, insecure/trusted-host option or TLS-disable flag is added.

The uv version, frozen sync commands, Python requirements/lockfile, Caddy copy,
nonroot startup and ENTRYPOINT remain unchanged. Application code, native Railway
configuration, authentication, storage, consent and spending controls are untouched.
Rebuild the reviewed commit using the ordinary docker build command above; actual
Railway rebuild/deployment requires separate approval and is not performed here.

Verification of this correction: 258 Python tests passed, 0 failed/skipped, with
one existing Authlib deprecation warning (101.64 seconds). Four offline native
Railway configuration checks passed; configuration itself is unchanged. Ruff,
Python dependency compatibility (63 installed packages), frozen uv lock (66
resolved), source/wheel builds, whitespace and sensitive-file reviews passed.
Standard docker build --check completed with no warnings, and the Dockerfile
contains no RUN mount flags or custom CA/TLS-disable settings.

The attempted ordinary docker build did **not** finish: the managed cloud's
intercepting HTTPS proxy certificate is not trusted inside the stock Python
image. Pip stopped at uv installation with SSLCertVerificationError / self-signed
certificate in certificate chain. The build reached RUN, so this is separate
from the supplied Railway parser error; it is not a successful image build.
The failed log remains private in artifacts/railway-build-fix/docker-build.log.
TLS verification was left enabled; no certificates, secrets, base-image tags or
application code were altered to manufacture a pass. A full build of the exact
Dockerfile on a builder whose HTTPS route is trusted by the stock system remains
required. The user subsequently explicitly approved publication of this narrowly
scoped correction with the environment-specific full-build limitation documented;
that approval does not establish a successful image build or authorize deployment.
No deployment, paid API request or merge occurred.
