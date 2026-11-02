# Customer Service AI Agent

LLM4Yemen Track B, Week 5 capstone.

**Current status: Phase 1 — planning and project structure only.** There is no
working agent, MCP server, database, Streamlit UI, or deployment yet. No runtime
tests, coverage measurements, execution traces, or deployment checks have run.

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
  agent/          # Future LLM loop, permissions, and budget enforcement
  tool_server/    # Future official SDK MCP server; never name this package mcp
  storage/        # Future SQLite repositories and migrations
  ui/             # Future Streamlit interface
tests/
  unit/
  integration/
  security/
docs/
```

Python 3.11 or later is the planned baseline. `pyproject.toml` contains package
metadata only; runtime dependencies and a reproducible lockfile will be added
and validated in a later approved phase. There is no runnable entry point yet.
`.env.example` documents anticipated configuration with no credentials. Future
local configuration can use an ignored `.env`; credentials must never be committed.

Phase 1 verification checks file presence, Git status, and `git diff --check`.
These checks do not establish application correctness. Phase 2 requires explicit
approval; subsequent phases and their evidence are described in the plan.
