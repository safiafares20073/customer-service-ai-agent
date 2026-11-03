# Customer Service AI Agent

LLM4Yemen Track B, Week 5 capstone.

**Current status: Phase 5 reviewed execution traces and recorded cost analysis.**
One official OpenAI SDK agent discovers and calls seven MCP tools over genuine
stdio, with scoped SQLite memory, permissions, cost controls and a locally tested
Arabic/English Streamlit UI. Three reviewed execution traces are available:
[success](traces/success_1.jsonl), [controlled recovery](traces/near_failure_recovery.jsonl)
and [explicit failure](traces/explicit_failure.jsonl). The terminal failure remains
`turn_limit`; fixture tests are kept separate from these live-labeled records.

[Cost analysis](cost_analysis.md): **USD 0.0006260 total**, approximately
**USD 0.000208666667 per attempted task (n=3, including the failure)**, from six
recorded model requests and November 3, 2026 Standard rates. This is usage-derived
estimated cost, not independently verified provider billing. Monthly model-token
projections and limitations are documented in that file. No paid calls were made
for the analysis. Secure public authentication/deployment, browser/mobile visual
review and final submission documentation remain pending.

The [gated evidence runner](docs/LIVE_TRACE_RUNNER.md) remains paid-disabled by
default; further execution requires separate approval. Current setup and historical
phase evidence follow below. No public demo URL or hosting completion is claimed.

The application is a single LLM agent designed to answer product and policy
questions, checks authorized orders, and creates support tickets after consent.
It uses the official Python MCP SDK, SQLite persistence, permission checks,
audit logs, and USD cost accounting.

Read [the agent specification](agent_spec.md),
[implementation plan](docs/IMPLEMENTATION_PLAN.md), and
[requirements matrix](docs/REQUIREMENTS_MATRIX.md) before implementation.

## Project layout

```text
src/yemen_customer_service/
  agent/          # OpenAI loop, durable state, pricing, traces, guarded console
  evidence/       # Separately gated trace scenarios and durable plan limits
  tool_server/    # Official SDK FastMCP server, trusted adapter, console demo
  storage/        # SQLite migrations, synthetic fixtures, authorized operations
  ui/             # Local-only bilingual Streamlit app and trusted controller
tests/
  agent/          # SDK-provider fixtures + real MCP, limits, process restart
  unit/
  integration/
  security/
docs/
```

## Run locally

From the repository root, using Python 3.12.14 and `uv` (validated with 0.12.23):

```sh
uv sync --frozen
.venv/bin/customer-service-demo
```

The demo seeds synthetic data, launches a genuine MCP server subprocess,
initializes a client session, discovers the seven tools, and lists products.
It makes no LLM or external service requests. Dependencies are locked in `uv.lock`;
Python >=3.11 is declared, but this phase was tested on 3.12.14 only.

For the authenticated **synthetic development** workflow:

```sh
.venv/bin/customer-service-demo --enable-demo-auth --customer demo-a
```

This shows order DEMO-100 and a synthetic ticket draft. A ticket is created only
after typing `CONFIRM`. Customer `demo-b` owns DEMO-200. These identities are
fixtures, not a production login system. No passwords or API keys are required.
The SQLite file defaults to ignored `data/customer_service.sqlite3`; use
`--database /path/to/synthetic.sqlite3` to select a separate demo file.

For a raw MCP client, start `.venv/bin/customer-service-mcp` with `DATABASE_PATH`
set to an initialized database. Its stdout is reserved for MCP protocol messages;
use the SDK client or the demo rather than typing human commands into it.
An unbound server permits public reads and rejects private operations.

```sh
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
git diff --check
```

See [Phase 2 design, security boundaries, and actual verification](docs/PHASE_2.md).
The tests launch real stdio MCP subprocesses; direct handler calls do not replace
integration tests. A restricted runner must permit subprocess stdio/event-loop
operations. Never bypass tests when the runner cannot support them.

## Phase 3 agent

Safe preflight, with no API request:

```sh
.venv/bin/customer-service-agent --preflight
```

The provisional model is `gpt-6-luna`, configurable through `OPENAI_MODEL`.
Credentials come from `OPENAI_API_KEY` or `LLM_API_KEY`; never put values in source
control or chat. Commands read process environment variables and do not load
`.env` automatically. Pricing is model-specific, dated, and recorded in
[config/model_pricing.json](config/model_pricing.json): the user's official
corrected Standard excerpt dated November 3, 2026 lists USD 0.10 input, 0.50
output, and 0.01 cached input per million tokens. Independent retrieval was blocked;
subsequent supplied execution records have been reviewed, while provider origin,
current account availability and billed costs remain independently unverified.
The [compatibility audit](docs/OPENAI_COMPATIBILITY_AUDIT.md) corrected the
previous Flex/Batch rates mislabeled as Standard and now explicitly sets
`reasoning_effort="none"`, as required for this model’s Chat Completions function
calling. Documented support relies on the verified source excerpt; later reviewed
execution records are linked above and do not independently authenticate a provider
exchange or current account access.

No paid call is enabled by default. After separate explicit paid-run approval,
secure credential setup, and live model checks, the guarded invocation is:

```sh
.venv/bin/customer-service-agent --allow-paid --enable-demo-auth --customer demo-a "Find headphones under $30"
```

This command has **not** been run against OpenAI in this phase. It uses synthetic
fixture identity only, not production authentication. Ticket requests pause for
review of the exact draft and an explicit `CONFIRM`; declining performs no write.
Task counters and costs survive confirmation and agent-process resumption.

The agent permits at most eight SDK requests, USD 0.05 in conservative estimated
cost, 60 cumulative active seconds, and 10 seconds per tool. SDK retries are
disabled. Missing usage or unsupported pricing stops further requests without
inventing zero cost. Token-based computed costs are not provider invoices.
No model substitution or alternate pricing tier is attempted on provider errors.

See [Phase 3 implementation, verification, and limitations](docs/PHASE_3.md).
Provider-fixture estimates and JSONL evidence are explicitly labeled; they do not
prove live model behavior. Raw prompts/answers/arguments are excluded from traces.
The original Phase 2 schema and all seven tool contracts are preserved.

The [single-task live smoke harness](docs/LIVE_SMOKE_TEST.md) produced the supplied
reviewed success record; see [validation scope](docs/SUCCESS_EVIDENCE_VALIDATION.md).
Its safe preflight is
`.venv/bin/python -m yemen_customer_service.agent.smoke --preflight`.
The paid runner requires separate explicit approval and has a persistent
one-attempt interlock. Fixture rehearsals do not establish live success.

## Phase 4 customer interface (local synthetic demo)

From the repository root, with Python 3.12.14 and uv:

```sh
uv sync --frozen
UI_PROVIDER=fixture .venv/bin/customer-service-ui --demo
```

The launcher binds only to loopback on port 8501. Use the browser on the same
machine; no public demo login or deployment is provided. On Windows 10, run in
WSL2 Ubuntu because the existing backend uses POSIX file guards. No API key or
paid model request is needed in fixture mode. `--customer demo-b` selects the
other synthetic identity **at the trusted launcher**, never in a customer widget.

Choose English or العربية. Chat can list products, explain policies, and check
the bound customer's own order (DEMO-100 for demo-a, DEMO-200 for demo-b).
Support-ticket requests display the exact editable draft, with distinct Confirm
and Cancel actions. Editing revokes pending consent. Confirmation resumes the
same task without resetting counters; cancellation makes no provider request.
API token/cost/limit information stays in backend records and documentation.
Product prices are ordinary store information, separate from API cost accounting.

```sh
PHASE4_EVIDENCE_DIR=artifacts/phase4-evidence .venv/bin/pytest -q --tb=short
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
uv lock --check --offline
uv build --offline
```

Final Phase 4 regression: **135 passed, 0 failed, 0 skipped**. The malicious
product, forged-consent, and poisoned-memory scenarios passed their boundary
checks with genuine MCP and explicitly scripted provider decisions. They do not
establish live-model prompt-injection robustness. Unique ignored evidence files
retain each run; safety blocks are not exported as explicit task-failure traces.
See [PHASE_4.md](docs/PHASE_4.md) for workflow, security findings, commands, and limits.
Phase 5 trace and cost documentation are prepared; public authentication and
deployment remain pending. Do not expose this development identity workflow.
