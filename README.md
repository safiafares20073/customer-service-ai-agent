# Customer Service AI Agent

LLM4Yemen Track B, Week 5 capstone.

**Current status: Phase 2 — SQLite storage and real MCP stdio integration.**
The seven-tool official FastMCP server, synthetic database, trusted client adapter,
and automated protocol/security tests are implemented. There is no LLM agent
loop, Streamlit UI, public deployment, or submission trace yet.

The planned application is a single LLM agent that answers product and policy
questions, checks authorized orders, and creates support tickets after consent.
It will use the official Python MCP SDK, SQLite persistence, permission checks,
audit logs, and USD cost accounting.

Read [the agent specification](agent_spec.md),
[implementation plan](docs/IMPLEMENTATION_PLAN.md), and
[requirements matrix](docs/REQUIREMENTS_MATRIX.md) before implementation.

## Project layout

```text
src/yemen_customer_service/
  agent/          # Future LLM loop and budget enforcement
  tool_server/    # Official SDK FastMCP server, trusted adapter, console demo
  storage/        # SQLite migrations, synthetic fixtures, authorized operations
  ui/             # Future Streamlit interface
tests/
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

`.env.example` has no credentials. The server reads process environment variables;
it does **not** automatically load `.env`. Memory and cost tables are foundations:
agent memory policy, actual LLM usage/cost accounting, and hard budget enforcement
remain Phase 3. Approval is required before that phase. Nothing has been deployed.
