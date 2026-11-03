# Customer Service AI Agent

LLM4Yemen Track B, Week 5 capstone.

**Current status: Phase 3 implementation; live OpenAI validation pending.**
One official OpenAI SDK agent discovers and calls the existing seven MCP tools
through genuine stdio communication. It includes scoped SQLite memory, task
resumption, cost reservations/accounting, time/turn limits, and redacted JSONL
metadata tracing. Tests use explicitly labeled provider fixtures and real MCP.
No live OpenAI execution, billed-cost measurement, Streamlit UI, public deployment,
or submission trace is claimed.

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
  tool_server/    # Official SDK FastMCP server, trusted adapter, console demo
  storage/        # SQLite migrations, synthetic fixtures, authorized operations
  ui/             # Future Streamlit interface
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
live model/account availability and tool-calling execution remain unverified.
The [compatibility audit](docs/OPENAI_COMPATIBILITY_AUDIT.md) corrected the
previous Flex/Batch rates mislabeled as Standard and now explicitly sets
`reasoning_effort="none"`, as required for this model’s Chat Completions function
calling. Documented support relies on your verified source excerpt; actual live
account/model behavior remains untested.

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
The original Phase 2 schema and all seven tool contracts are preserved. Phase 4,
including its prompt-injection acceptance exercises, remains unauthorized.

A [single-task live smoke test](docs/LIVE_SMOKE_TEST.md) is prepared but has not
been executed. Its safe preflight is
`.venv/bin/python -m yemen_customer_service.agent.smoke --preflight`.
The paid runner requires separate explicit approval and has a persistent
one-attempt interlock. Fixture rehearsals do not establish live success.
