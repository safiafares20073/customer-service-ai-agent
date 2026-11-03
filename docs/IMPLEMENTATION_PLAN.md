# Implementation plan

The next authorized preparation is the separately gated runner described in
[LIVE_TRACE_RUNNER.md](LIVE_TRACE_RUNNER.md). It reuses the reviewed recovery
helpers, adds durable shared allowances and permanent per-scenario locks, and is
validated offline only. Actual paid execution and hosting remain unauthorized.

Current trace-preparation work is documented in [TRACE_SCENARIOS.md](TRACE_SCENARIOS.md):
offline-only provider-fixture rehearsals with real MCP, a controlled test-server
storage fault and harness-only public-read retry, plus an explicit one-turn task
failure. No production failure policy changes or official fixture submission
files. Live collection needs the separately bounded approval described there.

Phases 1–4 are complete. Phase 5 planning, success-evidence review and offline
trace rehearsals are authorized. Live calls and hosting require separate approval.
Phase 2 evidence is recorded in [PHASE_2.md](PHASE_2.md) and the requirements matrix.
Phase 3 evidence and live-validation limitations are recorded in [PHASE_3.md](PHASE_3.md).
Phase 4 evidence and local UI limitations are recorded in [PHASE_4.md](PHASE_4.md).
Other listed checks are future acceptance criteria. Use one agent,
one MCP server, one SQLite database, and one Streamlit application.

## Authoritative source and scope

Reviewed source: user-supplied `Week5_Capstone_Official_Chapter12_10.pdf`,
Chapter 12.10, printed pp. 578–581 (four PDF pages). The preceding architecture
fragment and following §12.11 example are not §12.10 requirements. The excerpt's
LMS cost-analysis bullet ends at “monthly project”; this plan interprets it as a
monthly cost projection with explicit workload assumptions, without assuming a
required formula or numerical target.

Official schedule: Day 1 planning (3h); Day 2 loop (6h); Day 3 MCP + memory (5h);
Day 4 safety + cost (5h); Day 5 deployment + submission (4h). These are the book's
time allocations, not claims of actual effort or deadlines. Our proposed phases
reorder MCP before the agent loop to meet the user's genuine-integration goal;
no official deliverable is omitted by that ordering. Stop after Phase 4 for review.

Official requirements are mapped separately in the requirements matrix. The
exact seven tools, official SDK/stdio choice, authentication/reference design,
Arabic acceptance case, lockfile, extra adversarial cases, coverage measurement,
and hosting persistence safeguards are user requirements or optional quality
improvements, not additional official rubric items. The book specifies no
coverage threshold or JSONL field schema in this excerpt.

## Phase 1 — specification and scaffold

Deliver the one-page, six-category agent specification (including explicit
`ask_on_write` mode), supporting seven tool contracts, Python package
layout, safe configuration templates, this plan, requirements matrix, and accurate
README. Verify file presence, TOML parseability, ignore rules, Git status, and
`git diff --check`. No application code, dependency installation, execution traces,
LLM calls, or deployment. Stop for approval.

## Phase 2 — persistent store and real MCP server

- Select compatible Python and official `mcp` SDK versions; add minimal validated
  dependencies and a reproducible lockfile. Never create a top-level `mcp` module.
- Implement versioned SQLite schema and parameterized access for synthetic
  products, policies, customers, orders, tickets, conversation memory, audit
  events, and task/call costs. Keep runtime files outside source control.
- Implement all seven tools in `tool_server` with the official SDK. Launch over
  stdio; send logs to stderr so stdout remains protocol-only.
- Establish trusted development session context and server permission checks;
  never accept a principal selected by LLM arguments. Implement expiring order
  references, confirmation registration, and idempotent ticket writes.
- Define a trusted client adapter that keeps security references outside model
  schemas/results and injects them only into real MCP requests. Test rejection
  of model-supplied references, paired order fields, cross-principal/session
  reference reuse, and atomic confirmation consumption. Test identical retries
  after confirmation consumption and conflicting payloads with the same key.
- Verify from an actual MCP client subprocess session: initialize, list exactly
  seven tools, call each tool, exercise malformed inputs and denied calls. Test
  persistence after reopening SQLite and prevent cross-customer access.

Exit evidence: real SDK/version details, lockfile, passing named tests, sanitized
protocol evidence, SQLite persistence and permission checks. No simulated calls
may substitute for protocol integration. Real customer data is unnecessary.

## Phase 3 — single-agent LLM loop and controls

- Select provider/model, secure credential binding, and dated verified USD
  pricing. Check available credentials by names/presence without exposing values.
- Implement one bounded LLM loop using MCP-discovered schemas and MCP invocation.
  Apply turns, timeouts, conservative cost reservations, actual usage accounting,
  final-answer termination, and safe error handling.
- Add principal-scoped persistent conversation memory and sanitized audit events.
  Keep security references in trusted application state, outside model context.
- Validate with controlled provider responses and real MCP transport, then a small
  explicitly approved paid smoke run. Label controlled responses as test fixtures.
- Official Day 2 acceptance: exercise the loop on five distinct inputs: product
  listing, product search/policy answer, product details, authorized order status,
  and confirmed ticket creation. Save JSONL traces from actual executions and
  label fixture-provider versus live-provider runs accurately. The three spec
  examples alone do not satisfy the five-input check.
- Official Day 3 acceptance: stop the agent process, restart against the same
  SQLite database, and verify it remembers a prior conversation fact for the
  same customer; reopening a database alone is insufficient.
- Test max turns, final answers, exhausted budget, unknown usage/prices, retries,
  MCP errors, and persistence. Do not claim a real LLM run from fixture tests.
- Verify deterministic limit responses make no extra LLM call, and that ticket
  confirmation/resumption preserves task budget, turns, and cumulative active
  execution time rather than starting a new task.

Exit evidence: passing loop/control tests and genuine, redacted live-run evidence
only if credentials and paid-run approval are available. Report actual spend.

## Phase 4 — Streamlit and adversarial validation

- Build bilingual chat, authorized order access, and explicit editable ticket
  confirmation/cancellation. The latest Phase 4 request supersedes the earlier
  task-cost-view item: API token usage, costs, budgets, turns and debug references
  remain backend-only; no customer-facing cost/limit panel. Product prices remain
  normal store content. UI confirmation issues a payload-bound reference through
  trusted code. Local synthetic fixture identity is not production authentication.
- Test product/policy injection, malicious customer messages, poisoned memory,
  forged tool results, unauthorized order enumeration, fake consent, confirmation
  replay, and budget-reset attempts. Assert denied side effects and no data leaks.
- Official Day 4 acceptance: execute at least three distinct hostile inputs:
  product text instructing order-data exfiltration; a customer message claiming
  fake ticket consent; and poisoned memory instructing a budget/permission bypass.
  Verify the agent is not deceived using answer and side-effect assertions. Record
  actual outcomes, including failures; do not infer safety from the prompt alone.
- Exercise all three acceptance examples using documented synthetic fixtures,
  including an Arabic request. Reopen sessions to validate memory isolation.
- Run meaningful unit, MCP integration, security, and UI smoke checks; report
  passed, failed, skipped, and unrun outcomes separately. Measure coverage only
  using an installed runner against an identified commit.

Exit evidence: reproducible test commands and actual outcomes, sanitized traces
from executed runs, UI smoke evidence, known limitations. Never commit sensitive
traces or manufacture screenshots, test counts, or coverage.

## Phase 5 — authenticated public deployment

- Select **Render or Railway**, as specified on Day 5, with support for Streamlit,
  an MCP subprocess, and a persistent writable SQLite volume. Ephemeral storage
  cannot satisfy persistence.
- Configure secure secrets, TLS, real authentication, per-customer authorization,
  request limits, and appropriate data retention. Disable demo identity mode.
  Render is selected for the prepared single-container configuration; real provider
configuration and deployment acceptance remain pending.
- Keep MCP stdio private within the deployment. Do not expose database files,
  debug output, secrets, or internal security references to public clients.
- Run startup, functional acceptance, access-denial, and restart-persistence checks
  against the real hosted service. Confirm cost limits and capture actual results.

Exit evidence: real reachable public URL, dated deployment and smoke-test results,
documented persistence/authentication setup, and remaining limits. Deployment is
incomplete until these checks execute; an intended URL is not evidence.

## Official LMS submission checklist (future, not created in Phase 1)

- Public GitHub repository, with README covering real setup, usage, limitations,
  and actual verification; currently repository visibility has not been verified.
- Live public demo URL from the verified Render or Railway deployment.
- `traces/success_1.jsonl`: actual successful task execution.
- `traces/near_failure_recovery.jsonl`: actual run encountering and recovering
  from a problem; transparently label any deliberately induced fault.
- `traces/explicit_failure.jsonl`: actual run with an explicit failure outcome.
- One-page `agent_spec.md` with all six official elements.
- `cost_analysis.md` reporting measured average USD/task and a monthly cost
  projection with sample size, model/pricing date, workload assumptions, and
  limitations. Also document the average cost in the README (Day 5).

Do not generate submission traces or cost numbers until those executions happen.
Validate JSONL line parsing, redaction, and correspondence to actual run outcomes
as project quality checks; the source supplies filenames but no event schema.

## Evidence discipline

Maintain the requirements matrix as implementation progresses. Record commands,
versions, commit, dates, and actual outcomes only when executed. Generated local
raw evidence belongs in ignored `artifacts/`. Publish only reviewed, sanitized
submission traces at the three exact `traces/` paths above; do not commit raw logs,
credentials, customer data, or internal references. Preserve truthful outcomes
when redacting and document redactions. Preserve failures and distinguish
fixture tests from live-provider behavior. Never commit
secrets or customer data. Do not expand to additional agents or tools without
revising the specification and obtaining approval.


## Phase 5 secure-hosting preparation — November 4, 2026

Authorized implementation is prepared from merged cost-analysis main. See
[SECURE_HOSTING.md](SECURE_HOSTING.md) for the exact boundaries and executed checks,
and [DEPLOYMENT.md](DEPLOYMENT.md) for the gated release procedure. Added native
OIDC invitation authorization, separate production UI/startup, a versioned hosted
SQLite extension, durable shared spending reservations/kill state, bounded
concurrency, private retention controls, Render disk/container/proxy configuration
and offline authentication/security/restart/UI tests. Development mode remains
local-only, the seven tool contracts and original traces remain unchanged.

Actual deployment, real IdP/cookie/browser acceptance, public URL, manual narrow
screen review and separately approved live chat are remaining release gates.
Neither a healthy local container nor mocked issuer tests complete those gates.
No paid calls or account provisioning occurs during preparation.
