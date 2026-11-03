# Phase 2: SQLite and genuine MCP integration

Historical Phase 2 scope/evidence. Current agent functionality is described in
[PHASE_3.md](PHASE_3.md); the Phase 2 tests and database schema remain intact.

Implemented scope: storage, exactly seven FastMCP tools, trusted local adapter,
synthetic console demo, and automated tests. No LLM loop, Streamlit, deployment,
live-provider runs, submission traces, cost analysis, or coverage claim.

## Reproduce locally

Run from the repository root. Validated environment: Python 3.12.14, uv 0.12.23,
official `mcp` 1.30.0. Python >=3.11 is declared; other versions were not tested.

```sh
uv sync --frozen
.venv/bin/customer-service-demo
.venv/bin/customer-service-demo --enable-demo-auth --customer demo-a
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
uv lock --check --offline
uv build --offline
git diff --check
```

`uv.lock` records resolved dependency versions and artifact hashes. Install via
the frozen lockfile, not an unlocked `pip install`. Package downloads use normal
TLS verification. Build artifacts, databases, caches, logs, and the virtual
environment are ignored. In this cloud workspace, append
`--cache-dir /tmp/phase2-uv-cache` to uv commands because the default cache location
is read-only. Offline build/lock checks assume the dependencies are already cached.

The console demo's ticket prompt requires an explicit `CONFIRM`. Declining writes
no ticket. All output uses synthetic fixtures. Do not enter real customer data.
This demo is a protocol smoke client, not an agent execution or a submission trace.

## Components and protocol

- `storage/database.py`: transactional migrations tracked by `PRAGMA user_version`
  (currently 2), foreign keys, repeatable synthetic seeding, newer-schema rejection.
- `storage/store.py`: parameterized catalog queries, ownership checks, capabilities,
  transactional tickets, minimal audit records, principal-scoped memory helpers.
- `tool_server/server.py`: official `mcp.server.fastmcp.FastMCP`, seven tools and
  stdio only. No HTTP endpoint, authentication tool, or confirmation tool is added.
- `tool_server/client.py`: actual `stdio_client` + `ClientSession.initialize`,
  `list_tools`, and `call_tool`. A trusted adapter strips security references from
  model-visible results and schemas, and injects them into subsequent wire calls.
- `tool_server/demo.py`: explicitly opted-in, synthetic local session launcher and
  human confirmation prompt; no LLM dependency or simulated tool handler calls.

Both schemas and results are validated. Extra fields, unknown tools, coercible
but wrong types, excessive limits, blank queries, and malformed references are
rejected with fixed error messages. This includes errors occurring before normal
SDK dispatch: default SDK validation diagnostics can contain argument values, so
the FastMCP subclass validates/sanitizes that boundary first. Successful calls
still dispatch through FastMCP's official tool manager. Outputs are validated
against bounded Pydantic models before returning them. MCP clients receive
structured results and equivalent JSON text; errors have `isError=true`.

## Trust and permissions

This release supports **synthetic data and development fixture identities only**.
It is not production authentication. A trusted local operator may provision
`demo-a` or `demo-b` only with explicit demo enablement and development mode.
There is no remote API to mint identities or confirmations. Local DB write access
and the process launcher are administrative trust boundaries. Never expose them
to the model or an untrusted customer.

The launcher binds a random session capability through the child process
environment, not command arguments or tool fields. SQLite stores its SHA-256 hash,
customer binding, task correlation ID, and 1-hour expiry. Each private operation
revalidates the session; callers cannot supply a customer ID in a tool call.
The server and adapter reject authenticated demo launches in production mode.
The server does not load `.env` automatically. No real secrets are required.

Order verification checks ownership before issuing a random 5-minute reference,
bound to session and order. Status lookups and linked tickets recheck ownership,
session binding, and expiry. Missing and foreign orders return the same denial.
Responses omit customer IDs, addresses, payment data, and order item details.

Trusted code must display the draft before `confirm_ticket(..., confirmed=True)`;
future UI code must call `cancel_ticket()` on every edit or cancellation. Model
invocations cannot register consent or provide/override wire references. The
server checks a 5-minute confirmation bound to session and canonical payload
(subject, message, optional order ID, idempotency key). A false confirmation or
cancel hook revokes pending consent; changed payloads cannot use previous consent.

Ticket insertion, consent consumption, and the principal-scoped idempotency record
are one `BEGIN IMMEDIATE` transaction. A failed insert leaves consent unconsumed.
Identical retries return the existing ticket without requiring a second write;
different payloads with the same key are denied. Authentication and linked-order
access are still rechecked before a retry result. Concurrent identical calls
cannot create duplicate tickets. Raw capabilities are not persisted or logged.

Audit events contain generated request/task correlation IDs, timestamp, hashed
principal reference, allowed tool name, outcome, and fixed result code. They omit
arguments, message text, raw references, and exception text. Anonymous calls have
anonymous correlation. Tool-call audit coverage is implemented; a complete agent
audit lifecycle and retention/cleanup policy remain future work. Audit recording
follows the domain transaction; it is not an atomic tamper-proof compliance log.

## Persistence and future foundations

The SQLite schema contains products, policies, customers, orders, tickets, memory,
audits, tasks, cost records, sessions, order access, and confirmation grants.
Initial seed data contains three products, four policies, two customers and two
orders, and no invented pre-existing tickets or model costs. Seeding again does
not overwrite existing domain data. New database files have mode 0600.

Trusted memory helpers store and retrieve at most 20 recent records for the
authenticated principal. Tests verify data across distinct OS processes and
customer isolation. This does not satisfy the later requirement for an actual
LLM agent to remember after restart: the agent does not exist yet.

Task and cost tables are storage foundations only. No provider/model, pricing,
token measurement, cost reservation, budget enforcement, or average cost is
implemented. No cost records are fabricated. Grant expiry is enforced on access;
automatic deletion of old records is not implemented. An operator who controls
the local database can change it, as expected for this development trust model.

## Verification evidence

The test suite uses actual SDK clients and new server subprocesses; it does not
mock MCP transport or call handlers as a substitute. Protocol tests initialize,
discover exactly seven tools, call each one, validate schemas and results, and
exercise denial paths. Other tests cover malformed inputs, isolation, reference
expiry, consent changes/cancellation, transactional failure, concurrent retries,
restart persistence, and SDK import origin. Storage-only tests are identified as
such and are not claimed as protocol tests.

Actual results and check outcomes for this working tree are recorded in the
requirements matrix. The first sandboxed test attempt stalled in subprocess
transport and was stopped; the same public-tools test then passed unchanged with
managed-environment execution permissions. The full suite was run with those
permissions. No tests were weakened or skipped to accommodate that runner.

No live LLM calls, official five-agent-input acceptance runs, three hostile LLM
prompt tests, JSONL submission traces, deployment checks, or coverage measurements
have been performed. Those remain later-phase requirements.
