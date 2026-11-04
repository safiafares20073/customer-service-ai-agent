# Customer Service AI Agent

LLM4Yemen Track B — Week 5 capstone. One bounded OpenAI agent discovers and calls
seven tools through the official MCP Python SDK, with SQLite memory, authorization,
audit logging, cost tracking and a bilingual Streamlit interface.

**Demo:** https://yemen-customer-service-review-production.up.railway.app

The owner reports a working Railway deployment with Google OIDC and real OpenAI
chat. This workspace cannot independently access its health endpoint (proxy CONNECT
403). The final changes below are offline-tested preparation for review, not an
automatic deployment. **The owner reports hosted ticket confirmation now works. The latest dark-theme,
assistant RTL and optional email invitation changes still need review and hosted
acceptance before final submission.**

## Architecture and tools

Browser -> invite-only Google OIDC -> trusted Streamlit controller -> single
OpenAI tool-calling loop -> genuine MCP stdio subprocess -> persistent SQLite.
Model arguments cannot establish identity, ownership or consent. MCP is private;
there is no public database or MCP endpoint and no package named mcp in this project.

| MCP tool | Purpose |
| --- | --- |
| list_products | Paginated public catalog summaries |
| search_products | Bounded catalog text search |
| get_product_details | Price, description and actual stock availability |
| get_store_policies | Returns, shipping, privacy and support policies |
| verify_order_access | Verify trusted authenticated ownership |
| get_order_status | Read a verified own order using a private scoped reference |
| create_support_ticket | Create an explicitly confirmed, idempotent ticket |

The synthetic catalog contains Example Headphones (USD 25, in stock), Example
Keyboard (USD 40, in stock), and Example Mouse (USD 15, out of stock). Returns
require the original receipt within 14 days. These facts come from MCP data, not
UI answer templates. List/search catalog entries do not establish stock: detail
tools must be consulted. No real customer data is used or requested.

## Run locally

Use Linux/WSL2, Python 3.12 and uv. POSIX process/file locks are required.
Dependencies are pinned in uv.lock; validation versions are in the final report.

```sh
uv sync --frozen
# Storage + genuine MCP only; no model request:
.venv/bin/customer-service-demo
# Loopback-only UI with clearly labeled scripted provider fixtures:
UI_PROVIDER=fixture APP_ENV=development .venv/bin/customer-service-ui --demo
```

Open http://127.0.0.1:8501 on the same machine. Choose English or العربية.
Development identities and their seeded orders are local-only; never expose this
launcher, its capabilities or development database publicly. Windows users should
run these commands in WSL2. Commands read environment variables; .env is not loaded
automatically. Use [.env.example](.env.example) only as an empty-credential template.

The hosted entrypoint is a separate Docker launcher: one Caddy proxy, private
Streamlit worker, one mounted disk and native OIDC. See
[Railway setup](docs/RAILWAY_DEPLOYMENT.md). No change to the existing live secrets,
Google configuration, volume, USD 3 approved global allowance or accounting was
made during this final task. Do not reapply new-deployment zero-budget defaults
to the already configured live service.

## Assessor access and walkthrough

An administrator can privately preapprove the professor's exact primary Google
email in HOSTED_REVIEWER_EMAILS_JSON and add it to Google Test Users if required.
Native cryptographically validated Google OIDC plus email_verified=true permits
first enrollment; subsequent authorization uses an immutable issuer/subject
principal binding. Existing HOSTED_REVIEWERS_JSON users continue unchanged.
No manual subject, tokens, passwords or new registration portal are needed.
See [private setup and migration](docs/PROFESSOR_ACCESS_AND_DARK_RTL.md).

Follow [FINAL_DEMO_GUIDE.md](docs/FINAL_DEMO_GUIDE.md) for administrator steps and a
five-task walkthrough covering catalog/stock/policies, Arabic, cancel, edit/confirm
and unauthorized order denial. Existing rate limits also apply to demonstrations;
logging out never resets the principal's allowance.

## Permissions, memory and spending

- Native OIDC plus invitation validation binds each principal. Login expires after
  at most 15 minutes; logout revokes capabilities and pending consent. No model
  message, chat “yes”, guessed order ID or unsigned header proves authorization.
- A ticket request must call create_support_ticket to produce an editable draft.
  Only the trusted Confirm control authorizes the exact payload. Edits invalidate
  old confirmation; Cancel writes nothing and makes no additional model call.
  Confirmation resumes the same task/counters, with server-side idempotence.
- SQLite scopes conversations, tasks and tickets by principal. Restart tests prove
  scoped memory and durable accounting. Production initializes public catalog
  data only, without demo identities or preloaded orders. Protected own-order
  success is tested locally; the public demo has no preloaded private orders.
- Each task permits at most 8 model requests, USD 0.05 estimated, 60 cumulative
  active seconds and 10 seconds/tool. Durable global/per-principal reservations,
  rate limits, one-operation concurrency, approval expiry and kill remain enforced.
  The owner-reported approved global cap is USD 3; it was not inspected, changed,
  reset or increased here. Missing/ambiguous usage blocks further paid calls.
- Secrets stay in host private settings. Customer views omit API accounting,
  capabilities and debug details. Assistant Markdown supports basic formatting
  after redaction, with HTML and external links/media disabled; user text stays plain.

Production uses the official OpenAI SDK, gpt-6-luna, Chat Completions with
reasoning_effort="none", Standard/default processing, no automatic SDK retries
and no model fallback. Paid execution requires separate explicit authorization.
Never place API keys in Git, Docker images, browser widgets or public documentation.
Historical compatibility/pricing provenance is documented in the
[compatibility audit](docs/OPENAI_COMPATIBILITY_AUDIT.md); current account/model
support and pricing must be checked privately before future authorized use.

## Evidence and measured costs

The three reviewed original files remain byte-for-byte unchanged:

- [success_1.jsonl](traces/success_1.jsonl): completed product/policy task.
- [near_failure_recovery.jsonl](traces/near_failure_recovery.jsonl): completed after
  one disclosed harness-controlled read fault and bounded recovery in the same task.
- [explicit_failure.jsonl](traces/explicit_failure.jsonl): terminal turn_limit,
  deliberately limited to one model request; incomplete rather than fabricated success.

[Cost analysis](cost_analysis.md) records six requests across n=3 tasks, including
failure: 5,500 input, 152 output and 0 cached tokens; **USD 0.0006260 total**, mean
**USD 0.000208666667/task**. At historical November 3, 2026 Standard prices, projected
model costs for 100/1,000/10,000 tasks are USD 0.02086667/0.20866667/2.08666667.
These are usage-derived estimates, not independently verified invoices or hosting
prices; the sample size and workload assumptions limit extrapolation.

## Verification and remaining limits

**Final offline regression: 283 passed, 0 failed, 0 skipped**, one existing Authlib
warning; four Railway configuration checks pass. Real local Chromium desktop/mobile
RTL/Markdown/control checks passed. No fresh local Docker image-build pass is claimed.

See [FINAL_VALIDATION.md](docs/FINAL_VALIDATION.md), the
[requirements matrix](docs/REQUIREMENTS_MATRIX.md), and
[final checklist](docs/FINAL_SUBMISSION_CHECKLIST.md) for exact outcomes and sources.
The [one-page specification](agent_spec.md) contains all six official elements.

```sh
CADDY_TEST_BINARY=/tmp/hosting-caddy .venv/bin/pytest -q --tb=short
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
uv lock --check --offline
uv build --offline
npm ci --prefix .railway --ignore-scripts
npm test --prefix .railway
docker build --check .
docker build -t customer-service-railway:review .
git diff --check
```

The full suite needs a real Caddy binary; the Railway guide documents extraction.
It exercises actual MCP subprocesses and explicitly labeled SDK/OIDC fixtures,
not paid OpenAI or real Google login. Local headless Chromium visual/DOM checks
are distinguished from hosted/mobile-device checks. The known cloud proxy CA
restriction can block the full Docker build without weakening TLS; no fresh local
image-build pass is claimed. Owner-reported Railway operation is separate evidence.

Text-only model proposals do not create draft forms or tickets; clearer model/tool
instructions reduce this ambiguity but cannot guarantee live-model compliance.
Malformed arguments remain denied. Hourly task exhaustion now has a safe localized
wait message instead of a generic failure; limits are unchanged. The specific live
failure is not conclusively attributed to either case without live records.
Actual hosted ticket confirmation, post-review deployment, professor access and
browser/provider acceptance remain required. No paid calls, live configuration
changes, deployment or merge occurred in this final improvement workflow.


## Latest targeted correction

The native dark appearance from pre-polish revision a9bae01 is restored; the
navy/teal/light overrides are removed. Only a minimal native primary-label contrast
correction remains. Assistant Markdown has per-message direction, with actual
Arabic paragraphs/lists/markers RTL and English messages LTR, even on an Arabic
page. Safe formatting, redaction and all ticket/permission/spending behavior remain.

Optional private Google-email enrollment is additive and disabled when unconfigured.
Its versioned extension stores keyed invitation hashes and stable opaque principals,
without resetting existing sessions, data or accounting. Existing model, pricing,
limits, USD 3 authorization, original traces and cost analysis are unchanged.
See PROFESSOR_ACCESS_AND_DARK_RTL.md in docs for current exact checks and release gates;
earlier final-polish visual/test results above are historical.
