# Requirements matrix

## Latest targeted correction — November 4, 2026

The owner now reports real Railway Google/OpenAI/product/policy/ticket workflows
are tested and working. The new candidate restores pre-polish native dark styling,
scopes assistant RTL and adds optional verified-Google-email first enrollment.
See [PROFESSOR_ACCESS_AND_DARK_RTL.md](PROFESSOR_ACCESS_AND_DARK_RTL.md) for current
source revision, migration, actual checks and manual release gates. Prior reports
below retain their historical validation scope; they do not imply the owner has
not since tested the existing deployment. The new candidate has not been deployed.


## Current final review candidate — November 4, 2026

The owner reports a deployed Railway service, Google OIDC and real OpenAI chat at
https://yemen-customer-service-review-production.up.railway.app. Public health
access is blocked here by proxy CONNECT 403, so current hosted behavior is not
independently verified. Existing approved global USD 3, private data, credentials,
allowlist and deployment were not inspected or modified. Final code remains a
review candidate; use [FINAL_VALIDATION.md](FINAL_VALIDATION.md) and
[FINAL_DEMO_GUIDE.md](FINAL_DEMO_GUIDE.md) for exact evidence and pending acceptance.
Historical planned/unverified statements below describe their original phases.


## Recorded cost analysis complete — 2026-11-04

[cost_analysis.md](../cost_analysis.md) independently recomputes all six usage
records from the unchanged three official traces and documents n=3 attempted
tasks, including terminal failure. Totals: 5,500 input, 152 output, 0 cached
tokens, USD 0.0006260 estimated. Mean: approximately USD 0.000208666667/task.
Monthly model-token projections at 100/1,000/10,000 tasks are USD 0.02086667 /
0.20866667 / 2.08666667 using unrounded mean and historical Standard rates.
The document and README distinguish recorded usage-derived estimates from
independently unverified provider billing, with small-sample, scenario-mix and
infrastructure exclusions. No paid calls or trace/source edits were made.
This completes the cost-document preparation gate; hosting, authenticated demo
access, visual review and final submission remain pending.

## All three reviewed submission trace artifacts present — 2026-11-04

[traces/explicit_failure.jsonl](../traces/explicit_failure.jsonl) is imported
unchanged for task `d4d9f9a23d3447d8952ffa3610883947`. Its five events record one
model request, one successful list_products read, then terminal turn_limit under
a deliberately reduced one-request allowance. This is a recorded incomplete task,
not a completed customer answer or a successful safety block relabeled as failure.
Usage is 850 input / 17 output / 0 cached tokens as recorded; computed USD 0.0000935.
[EXPLICIT_FAILURE_EVIDENCE_VALIDATION.md](EXPLICIT_FAILURE_EVIDENCE_VALIDATION.md)
preserves the supplied independent report and distinguishes current public-file
checks from private SQLite/plan/lock checks performed by the prior reviewer.
The required original SHA256 matches the received/exported bytes. No events were
modified, reconstructed or generated during import. Provider exchange origin and
invoice billing remain independently unverified.

All three official trace files now exist with their reviewed original hashes and
accurate completed/completed/turn_limit outcomes. Their combined recorded usage
is 5,500 input / 152 output / 0 cached tokens and computed USD 0.0006260 across
six model requests; these are usage-derived calculations, not billed costs.
Success had private bundle checks in this workspace; recovery and failure private
checks are attributed to their supplied independent reports. Overall capstone
submission is not complete: secure hosting/authentication, live demo URL, visual
review and final documentation remain pending; cost analysis is now documented above.
No paid API call was made here; earlier trace-pending statements below are historical.

## Reviewed live recovery evidence — 2026-11-03

[traces/near_failure_recovery.jsonl](../traces/near_failure_recovery.jsonl) is now
imported unchanged for task `561a396ba302496aa17a278bc928daff`: nine events,
one disclosed list_products storage fault, one harness-controlled retry and
successful completion in the same task. The two usage records total 1,861 input,
53 output, zero cached tokens as recorded, and computed USD 0.0002126.
[RECOVERY_EVIDENCE_VALIDATION.md](RECOVERY_EVIDENCE_VALIDATION.md) preserves the
supplied independent report and explains the current import validation scope.
The original trace hash stated by that report matches the received bytes.
The private databases/ledger and raw model answer are not in this public ZIP;
the prior reviewer reports their corroboration, which was not repeated here.
Neither provider origin nor invoiced billing is independently authenticated.
This is adapter-controlled recovery, not model-led self-repair. No new API call
was made during import. Explicit-failure evidence is now reviewed as described above.
Historical preparation/rehearsal statements below are superseded for this recovery
artifact only; fixture evidence has not been relabeled.

## Historical gated live runner preparation — not live execution

[LIVE_TRACE_RUNNER.md](LIVE_TRACE_RUNNER.md) documents the separately gated runner,
shared reviewed recovery policy, durable two-task/nine-attempt/USD 0.10 estimated
plan, one-attempt locks, and no-cost preflight. Offline tests use provider_fixture
labels and actual MCP subprocesses. No paid requests, new live traces, hosting
or independent billing verification occur. The two remaining official submission
files stay pending until qualifying live executions and independent review.

## Historical remaining trace rehearsals — fixture evidence only

See [controlled trace scenarios](TRACE_SCENARIOS.md). On merged-main baseline
`c051375cae765f22229d06aec6b288eb8e76ad82`, an offline harness executes a real
catalog storage fault followed by one successful MCP retry within the same task,
and a separate one-turn terminal failure. Provider decisions/usage are scripted;
MCP initialization/discovery/calls and SQLite side effects are real. Production
loop, server, adapter, security behavior and success_1.jsonl are unchanged.
Controlled recovery is a harness-only adapter policy, not live-model reasoning
or production auto-retry. The two official recovery/failure files remain missing;
fixture evidence is retained privately and is not promoted to live evidence.
The linked plan bounds a future separately approved live attempt; no paid calls
or hosting changes are performed in this step.

## Reviewed live success evidence — 2026-11-03

[traces/success_1.jsonl](../traces/success_1.jsonl) now contains the unchanged
10-event success trace for task `fa24226fb82347b299bf17662bead7ac`.
[Validation report](SUCCESS_EVIDENCE_VALIDATION.md) records cross-checks against
the original report, SQLite task/state, MCP audits, three usage records and dated
pricing. Totals: 2,789 input tokens, 82 output, zero cached as recorded; computed
USD 0.0003199. The answer agrees with the recorded product/policy results.
Original bundles, database and attempt.lock remain private and unchanged.
This verifies consistency of supplied live-labeled execution records, not an
independent provider receipt, invoice, current model availability or deployment.
No new API calls were made during success import. Recovery evidence is now
reviewed as described above; other live functional scenarios remain
unverified. All three reviewed trace artifacts are now present. Step 1 statements
below are historical.

## Historical Phase 5 Step 1 status clarification — 2026-11-03

Planning/evidence preparation only. Remote merged main
`0fe6d114e649efa318a7da0bd0350e2b55e56cbe` was checked against all 59 tracked
local files; contents match. Phase 4 is committed, pushed and merged; historical
“uncommitted” wording below describes its implementation-time review.
An owner-reported Codespaces live smoke succeeded, but its files have not been
received or independently validated here. “Live pending” below therefore remains
accurate for repository-verifiable live evidence, not a denial of that report.
No new live calls, trace files, measured cost analysis, production authentication
or deployment were created in Step 1. Existing fixture results are not relabeled.

The [final acceptance checklist](FINAL_SUBMISSION_CHECKLIST.md) separates official
academic requirements from project safeguards and optional enhancements.
[Step 1 baseline and file/test inventory](PHASE_5_STEP_1.md),
[evidence import protocol](EVIDENCE_IMPORT_PROTOCOL.md), and
[minimal hosted design](HOSTED_DEMO_DESIGN.md) are design documents, not runtime
implementation evidence. No proposed tests are reported as executed.

Source reviewed: supplied `Week5_Capstone_Official_Chapter12_10.pdf`, §12.10,
printed pp. 578–581. Page citations refer to printed book pages. Requirements
below are paraphrased from that excerpt, not inferred from adjacent sections.
The final cost-analysis bullet is truncated at “monthly project” in the supplied
excerpt; a monthly cost projection is the documented interpretation.

Phase 4 adds a locally tested Arabic/English Streamlit customer interface and
adversarial boundary tests to the existing OpenAI SDK agent and seven real MCP tools.
Provider-fixture execution and supplied success-record consistency are verified;
independent provider authentication/billing and public deployment remain pending.
“Documented” never implies runtime validation. See
[PHASE_4.md](PHASE_4.md), [PHASE_3.md](PHASE_3.md), and the historical
[PHASE_2.md](PHASE_2.md).

## Official requirements and submission evidence

| Official item | Source | Implementation / evidence location | Current verification status |
| --- | --- | --- | --- |
| Solve a real task end-to-end, public URL, cost tracking | Goal, p. 578 | Agent, deployment, tracker; plan Phases 2–5 | Agent/MCP orchestration and accounting fixture-tested; supplied live-labeled product/policy success records reviewed; public URL pending |
| Choose one of eight domains | Day 1, pp. 578–579 | Customer service, `agent_spec.md` §1 | Documented: listed domain selected |
| One-page `agent_spec.md` | Day 1, p. 579 | Concise six-section `agent_spec.md`; detailed contracts moved to supporting design | Verified: temporary A4 PDF is one page at 10pt, 12pt leading, 36pt margins; other renderers may paginate differently |
| Goal in one sentence | Day 1, p. 579 | `agent_spec.md` §1 | Documented |
| 5–10 allowed tools | Day 1, p. 579 | `agent_spec.md` §2 | Documented: seven |
| Termination: max_turns + budget + final_answer | Day 1, p. 579 | `agent_spec.md` §3 | Implemented; fixture tests verify final answers, eight requests, cost reservations, timeouts, and no extra final request |
| Budget cap in USD/task | Day 1, p. 579 | `agent_spec.md` §4 | USD 0.05 estimated cap with conservative reservations tested; live token bounds and billing unverified |
| Policy mode: auto / ask_on_write / always_ask | Day 1, p. 579 | `agent_spec.md` §5 | Local UI confirmation/cancel/edit plus agent/MCP authority verified; production login pending |
| Three input/output success examples | Day 1, p. 579 | `agent_spec.md` §6 | Fixture executions passed with real MCP; supplied product/policy and catalog-recovery evidence reviewed; live order/ticket examples remain unverified |
| Basic tool-calling loop; no multi-agent yet | Day 2, p. 579 | `agent/`; plan Phase 3 | Implemented: one official OpenAI SDK loop; fixtures and supplied Codespaces success records reviewed; no independent provider receipt |
| Test on five inputs | Day 2, p. 579 | Five cases enumerated in plan Phase 3 | All five scenarios fixture-tested with real MCP; supplied live product/policy success reviewed; other live scenarios pending |
| Save JSONL traces | Day 2, p. 579 | Actual loop runs; plan Phase 3 and submission checklist | Fixture traces retain their labels; all three unchanged live-labeled submission traces reviewed; billing unverified |
| Bind at least one MCP server (own server allowed) | Day 3, p. 580 | `tool_server/`; plan Phase 2 | Verified: official FastMCP 1.30.0 stdio subprocess; initialize, discover and call tests pass |
| SQLite memory; remembers after restart | Day 3, p. 580 | `storage/`, agent restart test; plan Phase 3 | Separate agent OS processes remember a scoped conversation fact; cross-customer isolation verified with provider fixtures |
| Permission layer and audit log | Day 4, p. 580 | Server and storage; plan Phases 2–3 | Agent, MCP and trusted UI boundaries tested; native OIDC invitation authorization implemented/tested offline; real IdP acceptance pending |
| Cost tracker | Day 4, p. 580 | Agent and SQLite task/call costs; plan Phase 3 | Implemented: Decimal accounting and reservations; success raw usage reconciled to USD 0.0003199; recovery trace/report cost verified at USD 0.0002126; invoices unverified |
| Three hostile prompt-injection inputs; must not be deceived | Day 4, p. 580 | Three explicit cases in plan Phase 4 with outcome/side-effect checks | Phase 4: product, forged-consent and persistent-memory cases executed with scripted provider attacks + real MCP; all boundary assertions passed; live robustness unverified |
| Simple Streamlit UI | Day 5, p. 580 | `ui/`; plan Phase 4 | Implemented and tested locally with Streamlit 1.66.1 AppTest and actual loopback server; Arabic/English and approval flows verified |
| Deploy to Render or Railway | Day 5, p. 580 | Plan Phase 5 | Render configuration and private mounted-disk container prepared/tested locally; no deployment |
| Write README and document average cost | Day 5, p. 580 | README; measured average added in Phase 5 | README documents n=3 usage-derived mean USD 0.000208666667/task; sample/model/rates and monthly estimates linked; provider billing unverified |
| Public GitHub repository | LMS item 1, p. 581 | Current project repository | Repository exists locally; public visibility unverified |
| Live demo URL | LMS item 2, p. 581 | Verified deployed service | Missing until Phase 5 |
| `traces/success_1.jsonl` | LMS item 3, p. 581 | Unchanged supplied success trace; docs/SUCCESS_EVIDENCE_VALIDATION.md | Complete locally: report/SQLite/MCP audits/tokens/cost checked; provider receipt and billing unverified |
| `traces/near_failure_recovery.jsonl` | LMS item 3, p. 581 | Unchanged reviewed trace; docs/RECOVERY_EVIDENCE_VALIDATION.md | Complete locally: SHA256, event order, one-task retry, tokens/cost and report consistency verified; private DB checks attributed to prior reviewer; billing unverified |
| `traces/explicit_failure.jsonl` | LMS item 3, p. 581 | Unchanged reviewed trace; docs/EXPLICIT_FAILURE_EVIDENCE_VALIDATION.md | Complete locally: expected terminal turn_limit, original SHA256, five events, one read/request, usage/cost and report verified; private DB checks attributed to original reviewer; billing unverified |
| Submit `agent_spec.md` | LMS item 4, p. 581 | Root specification | Present; final submission not performed |
| `cost_analysis.md`: avg cost/task and monthly projection | LMS item 5, p. 581 | Measured sample and documented projection assumptions; plan Phase 5 | Complete: total USD 0.0006260, n=3 average including failure, 100/1,000/10,000-task projections, dated rates/formula/limits; provider billing unverified |

The book's Day 1–5 time allocations are recorded in the implementation plan.
They are planning guidance, not measured execution evidence. The supplied excerpt
sets no coverage threshold, trace event schema, specific model, or exact seven
tool names. No claims are made about unseen portions of the book.

## Project requirements and additional quality checks

The following detail includes user requirements and project design choices.
Where it overlaps official items above, it adds verification detail rather than
new official obligations. Exactly seven customer-service tools, official SDK,
genuine integration, no dependency shadowing, and honest evidence are explicit
user requirements. The chosen authentication design, extra security cases,
lockfile, Arabic case, and optional coverage are quality improvements. Real
authentication and persistent hosting are project release gates, not claims
about extra official rubric requirements.

| Requirement | Planned implementation / current document | Verification evidence required | Phase / current status |
| --- | --- | --- | --- |
| Goal | `agent_spec.md` §1 | Inspect explicit scope and exclusions | 1: documented |
| 5–10 allowed tools | `agent_spec.md` §2; contracts in `docs/AGENT_DESIGN.md` §2 | Inspect tool names, inputs, outputs, and access rules | 1: documented |
| Termination: turns, budget, final answer | `agent_spec.md` §3 | Inspect explicit limits; runtime boundary tests planned | Implemented and verified in Phase 3 provider-fixture tests; live bounds unverified |
| USD budget per task | `agent_spec.md` §4 | Inspect USD 0.05 limit; reservation and usage tests planned | Conservative estimated pre-request cap and usage reconciliation verified; not a provider invoice guarantee |
| Permission policy | `agent_spec.md` §5; `docs/AGENT_DESIGN.md` §5 | Inspect ownership and confirmation rules; denial tests planned | Trusted UI, per-session identity, explicit consent/edit/cancel and server-side checks verified with real MCP; no public demo login |
| Three input/output success examples | `agent_spec.md` §6; detailed fixtures in `docs/AGENT_DESIGN.md` §6 | Inspect three fixture-based examples; acceptance runs planned | Fixture executions passed with real MCP; supplied product/policy and catalog-recovery evidence reviewed; live order/ticket examples remain unverified |
| Minimal Python structure; no dependency shadowing | `pyproject.toml`, `src/yemen_customer_service/`, `tests/` | File presence, TOML parse; verify no top-level `mcp.py` or `mcp/` | Verified: official mcp/openai import-origin tests; no dependency shadowing; locked dependencies |
| Safe configuration | `.gitignore`, `.env.example` | Inspect empty credential field and ignore rules; no real credentials added | Empty credential template, explicit paid gate, demo opt-in and no key printing tested/reviewed |
| Accurate documentation and roadmap | `README.md`, `docs/IMPLEMENTATION_PLAN.md`, this matrix | Inspect status language and phased acceptance criteria | Updated for actual Phase 4 behavior, latest no-cost-panel requirement, retained failures, and remaining deployment/live work |
| Single-agent LLM loop | `agent/` | Controlled-response tests plus separately identified live LLM run | Implemented with official OpenAI SDK 2.54.0; fixtures passed and supplied Codespaces success records reviewed; provider origin not independently authenticated |
| Genuine official MCP integration | `tool_server/`, agent MCP client | Official SDK dependency/version; actual stdio initialization, discovery, calls | Agent and all seven tools exercised using real initialized stdio ClientSessions; no mock MCP |
| `list_products` | `tool_server/` | MCP call verifies pagination, result limits, summaries | Implemented; verified by test_discovery_and_all_public_tools plus malformed-input cases |
| `search_products` | `tool_server/` | MCP call verifies matching, bounded query, safe SQL | Implemented; real MCP matching and SQL-literal search verified |
| `get_product_details` | `tool_server/` | MCP calls for known and missing product IDs | Implemented; real MCP details and missing-product error verified |
| `get_store_policies` | `tool_server/` | MCP calls verify topic filtering and policy version | Implemented; real MCP topic filtering/version and invalid topic verified |
| `verify_order_access` | `tool_server/` | Own-order success, foreign/missing denial, forged principal rejection | Implemented; own-order success, foreign/missing and identity-forgery denial verified |
| `get_order_status` | `tool_server/` | MCP calls verify scoped/expired references and minimal disclosure | Implemented; own status, foreign/session/expiry denials and ownership recheck verified |
| `create_support_ticket` | `tool_server/` | MCP calls verify confirmation, edited drafts, ownership, idempotent retries | Implemented; confirmation, linked access, payload changes, idempotence, rollback and concurrency verified |
| SQLite persistent memory | `storage/` | Close/reopen database and restart checks; cross-principal isolation | Agent-process exit/restart and cross-customer memory isolation verified; fixture language output clearly labeled |
| Server-side permissions | `tool_server/`, trusted session context | Unauthorized calls denied even when UI/agent is bypassed | Verified through direct MCP clients, independent of trusted adapter checks |
| Trusted security references and ticket confirmation | Client adapter, `tool_server/` | References hidden from model; forged/cross-session references denied; paired order fields; atomic consent; identical retry succeeds without duplicate and changed-payload retry fails | Implemented adapter and server checks; hiding, expiry, cancel, scope, payload binding and retries tested |
| Audit logging | `storage/`, `tool_server/`, `agent/` | Assert allow/deny/error events, task correlation, redaction | MCP and agent lifecycle events implemented; no raw prompts, messages, references, or exception text in logs |
| Cost tracking and hard limit | `agent/`, `storage/` | Actual usage accounting; reservation, retry, unknown usage, limit tests | Estimated cap and usage edge cases fixture-tested; supplied three-call usage reconciled at historical rates; billed cost unverified |
| Limits across ticket confirmation/resumption | `agent/`, trusted task state | Same task retains usage/turns/active-time limits; deterministic limit response makes no LLM call | Same task ID, session, counters, elapsed time, cost and original limits persist; tested across real process exit/resumption |
| Prompt-injection defenses | `tests/security/` and permission boundary | Malicious catalog, policies, memory, messages, and results cannot authorize side effects or leak data | Three hostile scenarios + exhausted-limit subcase passed with scripted provider fixtures and actual MCP; not a claim of universal live LLM robustness |
| Streamlit UI | `ui/` | Executed chat, confirmation, cost-display, and session-isolation smoke checks | Verified: bilingual/RTL chat, exact editable draft, confirm/cancel, duplicate/replay/session guards, safe errors; API accounting/debug details excluded from customer views |
| Public deployment | Render or Railway configuration to be selected | Actual public endpoint, authenticated functional checks, persistent-volume restart | 5: Render container/disk/OIDC implementation prepared; real deployment and URL pending |
| Honest tests, traces, and coverage | Future test suite; ignored `artifacts/` | Actual runner outputs with commit/versions; no zero-test readiness claim | 187 passed, 0 failed, 0 skipped on explicit-failure import; fixture regressions remain labeled; all three reviewed live-labeled submission traces present; no coverage claim |
| No secrets committed | Ignore rules and secure configuration practices | Review staged changes before any future commit; inspect safe configuration | No real secrets added; generated databases, costs, logs and test evidence remain ignored; hosted secrets are private runtime-only |

## Historical Phase 2 verification

Validated on Python 3.12.14 and official `mcp` 1.30.0 with uv 0.12.23.

- `.venv/bin/pytest -q --junitxml=/tmp/phase2-results.xml`: **46 passed, 0 failed,
  0 skipped** in 22.80 seconds. These are storage/protocol/security tests, not the
  official five agent executions or three hostile LLM-input acceptance tests.
- `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`: passed.
- `uv pip check --python .venv/bin/python --cache-dir /tmp/phase2-uv-cache`:
  37 installed packages checked; no dependency conflicts.
- `uv lock --check --offline --cache-dir /tmp/phase2-uv-cache`: passed.
- `uv build --offline --cache-dir /tmp/phase2-uv-cache`: source distribution
  and wheel built successfully. Outputs are ignored local build artifacts.
- Official SDK import-origin test passed; source contains no `mcp.py` or `mcp/`.
- Credential review, public error/audit/stderr redaction tests, and
  `git diff --check` cover this working tree; they are not a claim of an external
  penetration test or dependency vulnerability audit.

Tests ran with managed-environment execution permissions after the sandboxed
transport attempt stalled. No transport mocks or skipped tests were substituted.
The initial default-cache dependency check failed because the cache was read-only;
using the documented writable cache succeeded. Phase 3 was subsequently authorized;
current results follow.

## Initial Phase 3 verification (before the compatibility audit)

- Baseline: merged `main` commit `9fbc74884d104f0b0e26a3565bb8fb75330e194c`.
- Python 3.12.14; official OpenAI SDK 2.54.0, MCP SDK 1.30.0; uv 0.12.23.
- `.venv/bin/pytest -q --junitxml=/tmp/phase3-all-results.xml`: **102 passed,
  0 failed, 0 skipped**, 55.67 seconds. Includes all 46 unchanged Phase 2 tests
  and 56 Phase 3 tests. No live test is hidden inside that count.
- Five official functional scenarios, memory after real agent-process exit,
  cross-customer denial, ticket resumption after process exit, turn/time/tool/cost
  limits, provider errors, missing usage/pricing, cache accounting, redaction,
  and SDK import/paid-request guards are covered with provider fixtures + real MCP.
- `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, frozen lock check,
  dependency compatibility check, build, credential review, and Git whitespace
  checks are the static/package checks for this working tree; see PHASE_3.md.
- The first agent-suite run was 50 passed / 1 failed due to delayed-response SDK
  shutdown; the lifecycle fix passed the affected test and full regressions.
- The initial November 2 pricing assumption was superseded by the November 3
  compatibility audit: Flex/Batch rates had been mislabeled Standard. Current
  Standard prices are input 0.10, output 0.50, cached 0.01 USD/million for
  gpt-6-luna only, per the corrected user-verified excerpt. Independent
  pricing/model-page retrieval was blocked by proxy CONNECT 403. No model/account
  availability, live tool-calling, actual provider token usage, or billed cost has
  been verified. No paid execution was approved or performed.
- Phase 4 prompt-injection acceptance exercises, UI, deployment, invoice/average
  cost analysis, and official live submission evidence remain pending. No commit,
  push, PR merge, or environment publication was performed for Phase 3.


## Focused compatibility audit — November 3, 2026

See [OPENAI_COMPATIBILITY_AUDIT.md](OPENAI_COMPATIBILITY_AUDIT.md).
The user's verified model/pricing/latest-model excerpt confirms Chat Completions
function calling requires reasoning_effort none (default medium); requests now
set none explicitly. Corrected Standard prices are input 0.10, output 0.50,
cached input 0.01 USD/million. Earlier half-price rates belonged to Flex/Batch.
The snapshot records November 3 in Asia/Aden; timezone-aware freshness validation
preserves future-date rejection. Old-price pending tasks fail closed without
silently repricing, resetting counters, issuing another request, or writing tickets.

- Affected suite: **57 passed, 0 failed, 0 skipped** in 17.70 seconds.
- Full suite: **106 passed, 0 failed, 0 skipped** in 52.45 seconds, including all
  46 unchanged Phase 2 tests and 60 Phase 3 tests.
- SDK fixtures assert Chat Completions path, explicit none reasoning effort,
  Standard service tier, and the full completion limit. Reasoning-token accounting
  does not double-count the reasoning subset; Standard reservations assume no cache.
- Lint/format, dependency compatibility, frozen lock check, whitespace review,
  and safe no-request CLI preflight passed. No fixture claims live compatibility.
- Independent official-page access remains blocked (proxy CONNECT 403). Documented
  compatibility and rates rely on the user's November 3 verified excerpts. Actual
  account/model execution, tokenizer bounds, invoices and billed costs are untested.
  No paid API calls, commits, pushes, merges, deployment, or Phase 4 work occurred.


## Prepared one-task live smoke test — not executed

See [LIVE_SMOKE_TEST.md](LIVE_SMOKE_TEST.md). A dedicated runner uses the existing
agent and genuine MCP for the exact headphones/returns question, with Standard
pricing, explicit none reasoning effort, the existing task limits, an atomic
one-attempt interlock, and an offline evidence/cost verifier. Human review of the
complete answer remains required; lexical anchors are not a grounding certificate.

- Harness fixture rehearsal: **7 passed, 0 failed, 0 skipped**, 2.68 seconds.
- Full regression: **113 passed, 0 failed, 0 skipped**, 55.28 seconds. These are
  provider-fixture tests; no live OpenAI execution or billed USD is included.
- Safe preflight, Ruff lint/format, and tracked/untracked whitespace checks passed.
- An initial rehearsal found a sentence-punctuation bug in the price anchor;
  it was fixed, and both grounded/incorrect-price fixture cases passed afterward.
- No default live-smoke database, interlock, report, or trace was created. The
  current environment has no configured credential binding, and enforced HTTP
  policy does not allow api.openai.com. Approval plus secure key/network setup
  are prerequisites for the future paid command. No live smoke call is authorized.

## Actual Phase 4 verification

Baseline merged main: `4554ac898a3e89a6ea7dc98c900e1a73c0633d2b`.
Python 3.12.14; Streamlit 1.66.1; MCP 1.30.0; OpenAI SDK 2.54.0; uv 0.12.23.

- `PHASE4_EVIDENCE_DIR=artifacts/phase4-evidence .venv/bin/pytest tests/ui tests/security/test_phase4_injection.py -q --tb=short --junitxml=artifacts/phase4-evidence/focused-after-fix.xml`:
  **22 passed, 0 failed, 0 skipped**, 19.55 seconds.
- `PHASE4_EVIDENCE_DIR=artifacts/phase4-evidence .venv/bin/pytest -q --tb=short --junitxml=artifacts/phase4-evidence/full-suite.xml`:
  **135 passed, 0 failed, 0 skipped**, 89.98 seconds. The original 113 tests were
  neither removed nor weakened; 22 new UI/controller/adversarial tests executed.
- Malicious product: PASS, private foreign delivery data absent from answer/model
  input, server ACCESS_DENIED, zero writes. Forged UI consent: PASS, task pauses
  without consent registration or a create call. Poisoned memory: PASS, unknown
  control tool denied and counters retained; exhausted-turn subcase makes no
  extra provider request. Reports are uniquely retained as ignored JSON evidence.
- Initial AppTest path setup errors and a confirmed draft-save failure are retained
  in `artifacts/phase4-evidence/`; the failures were fixed and affected/full tests
  rerun. Safety blocks are PASS evidence, never LMS explicit-failure traces.
- Real local launcher: `UI_PROVIDER=fixture APP_ENV=development DATABASE_PATH=/tmp/phase4-local-ui.sqlite3 .venv/bin/customer-service-ui --demo --port 18504`.
  Both `/_stcore/health` and `/` returned HTTP 200; health body was `ok`. The server
  was stopped afterward. No public deployment or live-provider execution occurred.
- Ruff lint/format passed. `uv pip check --python .venv/bin/python --cache-dir /tmp/phase4-uv-cache`
  checked 61 installed packages with no conflicts. Frozen lock check passed.
  `uv build --offline --cache-dir /tmp/phase4-uv-cache` built the source
  distribution and wheel successfully; outputs remain ignored. Tracked and
  untracked whitespace, document links, and credential-pattern reviews passed.
- The original schema stays version 2; seven MCP tools and their server handlers
  are unchanged. Only trusted journal edit/cancel APIs were added for atomic UI
  workflow handling. Latest UI requirements supersede the earlier cost-panel plan;
  API accounting/limits remain backend-only.
- AppTest validates text/widgets/RTL CSS and actual backend workflows; mobile
  pixels, accessibility, live model behavior, production login and deployment
  remain unverified or Phase 5 work. No paid calls, commits, pushes, PR merges,
  environment publication, or Phase 5 implementation occurred for this phase.


## Secure-hosting preparation — November 4, 2026

The official public-deployment/URL gates remain incomplete. The following are
project safeguards verified offline, not new official rubric requirements or
claims of live identity-provider/provider-billing validation.

| Safeguard | Implementation | Verification / remaining acceptance |
| --- | --- | --- |
| Invitation-only authentication | Native Streamlit/Authlib OIDC, exact issuer/subject allowlist, opaque HMAC principal | Offline real code/signature/state/nonce/PKCE tests; actual provider configuration/login pending |
| Protected sessions | 15-minute maximum application age, audience/azp checks, durable revocation, scoped capabilities | Expiry/logout/replay, invitation removal, cross-login/principal and real MCP denial tests |
| Safe fresh production database | Base schema 2 plus hosted extension 1; public catalog only | Development/fixture promotion rejected, no seeded accounts/orders; mounted-volume startup tested |
| Consent and agent preservation | Shared existing renderer/controller, seven unchanged MCP contracts, transaction-side hosted write gate | Exact edit/confirm/cancel, idempotence and cumulative limits; previous tests retained |
| Shared spending and kill | Durable pre-request reservations, lifetime global/principal totals, sticky unknown block, single-operation OS lock | Restart, concurrent process, crash reservation, usage overflow and disabled-provider tests; no paid calls |
| Secure proxy/runtime | Private worker, HTTPS origin, Caddy Secure cookie/header hardening, private secrets, health route | Real local Caddy and container checks; public TLS/WebSocket acceptance pending |
| Retention and persistence | Seven-day startup/manual content purge, retained accounting/revocation, private disk | Real process and container restart tests; operational backup/restore and scheduled purge remain operator responsibilities |
| Bilingual UI | Shared English/Arabic widgets and RTL CSS, protected login and logout | AppTest text/workflow checks; browser/mobile pixel and accessibility review pending |

See [SECURE_HOSTING.md](SECURE_HOSTING.md) for final executed counts, retained
initial failures, upstream warning and limitations. Original success/recovery/
failure traces and cost_analysis.md are unchanged; no new fixture output is
presented as live evidence. Hosted implementation preparation is distinct from
actually deploying and supplying assessor access.


## Railway Free adaptation — November 4, 2026

| Item | Actual status / evidence |
| --- | --- |
| Free compatibility and sources | CONDITIONAL: official railwayapp/docs source at dcbeb29573190a245d9af7cc43fbbdde0dee7375 lists 0.5 GB RAM, 1 vCPU, one 0.5 GB volume, 4 GB image and USD 1/month credit; rendered site blocked; account eligibility/egress/credit not verified |
| Supported Railway configuration | .railway/railway.ts with separately pinned SDK and lockfile; four offline SDK assertions pass; no plan/apply/provisioning or platform-side schema acceptance claimed |
| Resource fit / startup / health | Actual local production image with conservative 500 MB RAM/no swap and 1 vCPU: peak 236,281,856 bytes; five fixture SDK calls, real MCP, bilingual AppTest, confirmation and private disk restart pass; no OOM; actual Railway/browser/live capacity pending |
| Live OpenAI readiness | Existing official SDK/model/Standard/none configuration and real MCP unchanged; activation by private settings plus operator approval remains available; current external model/pricing/account verification and hosted live task pending |
| Security/spending preservation | No production source or existing tests changed; server-validated OIDC, scoped memory/consent/capabilities, durable limits/unknown-usage block, concurrency and kill retained |
| Regression/static evidence | 258 passed, 0 failed/skipped (one Authlib warning); 4 IaC checks, Ruff, Python dependencies/lock/package build and container checks pass; SDK audit reports zero known vulnerabilities; details in RAILWAY_DEPLOYMENT.md |
| Official final artifacts | Three traces and cost_analysis.md unchanged; no new fixture output presented as live evidence; real public URL and actual hosted acceptance still pending |

Railway preference supersedes the historical Render selection above. No Free
uptime, zero total cost, provider billing verification, current account access,
real authentication exchange or deployment is inferred from local fixture tests.


## Final academic and quality review

| Requirement | Current evidence / verification boundary |
| --- | --- |
| Six-element, one-page specification | agent_spec.md preserves goal, seven allowed tools, max_turns/budget/final_answer/time termination, USD 0.05, ask_on_write and three examples. A4/11 pt/15 mm print profile verified as one page; viewer-dependent pagination is not guaranteed. |
| One agent, five functional inputs and MCP | Existing functional scenario tests and real stdio discovery/calls retained; 25 focused final cases add hosted ticket/format/rate/error and factual-source coverage. Scripted SDK tests are not live-model executions. |
| SQLite memory, permissions, audits and cost | Cross-process persistence/scoping, ownership/consent, real MCP and durable accounting tests retained; existing live database/ledger never changed. |
| Three hostile inputs | Existing product-content, forged-consent and poisoned-memory fixture attacks rerun unchanged; not a claim of universal live-model resistance. |
| Ticket failure | Reproduced prose-without-form and rate/invalid-argument failures offline; clarified draft-tool instructions, localized rate refusal and retained exact trusted confirmation/idempotence. No conclusive attribution or hosted fix claim without private outcomes and approved retest. |
| Prices/availability/policies | Real MCP samples confirm P-100 USD 25 in_stock, P-200 USD 40 in_stock, P-300 USD 15 out_of_stock, 14-day original-receipt returns and unknown-product refusal; stricter prompting is not a deterministic hallucination proof. |
| Streamlit Markdown and RTL | Filtered assistant Markdown/plain user text; local real Chromium desktop/mobile-emulation checks show bold, actual RTL root/fields, safe focus/contrast, responsive ticket controls and no horizontal overflow. Actual hosted browser/device checks pending. |
| Authentication and professor access | Existing invite-only Google OIDC preserved; operator instructions cover Google Test Users and exact validated issuer/subject. Unknown professor subject is a manual prerequisite, never fabricated. |
| Deployment and URL | Owner-reported deployed URL now documented. Workspace health attempt blocked; no new deployment or fresh full-image build success is claimed. |
| Public repository | GitHub HTML returned 200 with Public label on November 4; final review branch publication is separate from LMS submission or an external-network access guarantee. |
| Traces and cost analysis | All three original hashes/bytes and cost_analysis.md unchanged. n=3/six requests, recorded usage estimates, historical pricing and invoice limits preserved. |
| Final readiness | GO for independent PR review after final automated checks; NO-GO for an unconditional final submission until reviewed-commit hosted ticket, professor access and hosted acceptance are complete. |

Exact final commands/counts and any retained initial failures are in
FINAL_VALIDATION.md. No security test is removed; rendering collectors adapt to
Markdown and the timing fixture adds explicit cancellation checks without changing
production limits. No paid calls, secret changes, live records, deployment or merge.


## Dark restoration / assistant RTL / professor access

| Requirement | Current implementation and evidence boundary |
| --- | --- |
| Original visual design | Native dark base and 12 px chat corners from pre-polish a9bae01; remove light/navy/teal overrides. Measured body contrast 18.11:1 and minimally corrected native primary-label contrast 5.72:1. |
| Assistant Arabic Markdown | Per-message native containers scope paragraphs/headings/lists/markers RTL; English messages remain LTR on Arabic page. Actual Chromium desktop/mobile checks, not CSS-string evidence alone; physical/hosted devices pending. |
| Simple professor access | Optional private HOSTED_REVIEWER_EMAILS_JSON; exact case-only normalized primary email, Google issuer, verified cryptographic identity and boolean email_verified required for first enrollment. No portal, shared account or anonymous paid access. |
| Stable identity and compatibility | Durable immutable email-HMAC -> issuer/subject principal binding; later authorization by subject, substitution/replay denied. Existing HOSTED_REVIEWERS_JSON remains independent. Legacy session/data/spend migration and race tests pass. |
| Additive persistence | Base schema 2 and hosted schema 1 unchanged; invitation extension v1 creates one table plus metadata atomically/idempotently. No volume, identity, spending, budget or expiry reset. |
| Regression and preserved scope | All baseline cases retained; new synthetic Authlib/SQLite and real MCP ticket/read/isolation tests. Exact counts and initial retained fixture failures in the targeted validation report. |
| Hosted acceptance | Owner-reported existing business flows remain working; new code/email-first login/theme need separately approved deployment and actual professor/browser retest. No live state or paid calls changed here. |
