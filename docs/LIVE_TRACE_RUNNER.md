# Gated live recovery/failure runner — prepared, not executed

Date: 2026-11-03 (Asia/Aden). Baseline merged main:
`1c82b43c0307437eb97f4becdefd0db324700c70`.
No paid request, deployment, commit or push is performed by this preparation.
The production Agent, seven tools, database schema, SDK provider and security
boundaries are unchanged. success_1.jsonl retains SHA256
`5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb`.

## Architecture and reviewed policy reuse

Run from the repository using Python 3.12/uv on Linux (Codespaces recommended).
The separate evidence.live module is not imported by the customer UI. The
reviewed ReadRecoveryClient and controlled fault server were moved unchanged
from tests into evidence/recovery.py and evidence/fault_server.py. Existing
offline rehearsals import those shared helpers, rather than maintaining a second
retry implementation. tests/fault_mcp_server.py remains a compatibility launcher.

The live CLI imports no SDKScript or fixture-response module. It constructs only
OpenAIProvider.from_environment(paid_approved=True), rejects fixture mode, a
different model or endpoint, and uses the existing official SDK Chat Completions
path. No prerecorded messages/usage are substituted for returned model responses.
Offline tests call execute_case with explicitly labeled fixture providers; those
events have provider_fixture labels and cannot become live submission evidence.

Both scenarios initialize/discover the same seven tools through genuine MCP
stdio subprocesses. A scenario-only CatalogOnlyClient permits list_products;
all other tool invocations are rejected before dispatch. A proposed ticket pauses
without consent and fails scenario acceptance. No confirmation API is exposed to
the model, and no ticket write or private read is needed.

- **near_failure_recovery:** one real SQLite query against a deliberately missing
  table fails in the disclosed fault server. The reviewed adapter retries only
  the explicitly retryable INTERNAL_ERROR from list_products, once per task.
  Both actual MCP attempts share Agent._tool's ten-second timeout. The second
  invocation uses the normal catalog handler. The run must then finish within
  the same task with an answer grounded in the actual headphones name/USD price.
  This is disclosed adapter-controlled recovery, not model reasoning about a fault.
- **explicit_failure:** normal FastMCP server; Limits(turns=1), with the existing
  USD/time/output limits. Acceptance requires a real successful catalog call then
  a terminal turn_limit and deterministic incomplete response, with no second
  model request. The terminal task failure is genuine; a successful safety denial
  or a model's direct answer does not qualify for this scenario.

Unexpected tools, direct/ungrounded answers, persistent faults or incomplete
scenario evidence fail acceptance and block the other scenario. The runner never
forces a model response, invents a missing event, or automatically reruns a task.

## Paid gates, allowances and crash behavior

Default invocation and --preflight are local read-only operations: no SDK/client
construction, network check or evidence-directory creation. Preflight wins even
if paid flags are also supplied. It reports only whether a credential is present.
Actual execution requires ALL of:

- --allow-paid, --approve-plan, --enable-demo-auth and APP_ENV=development;
- a securely configured key, exact gpt-6-luna, current supported pricing, unchanged
  prior success trace and a clean committed Git working tree;
- an owner-only evidence directory with no symlink components, no active process,
  no previous attempt for that scenario, and no failed/unfinished plan member.

--approve-plan acknowledges **at most two tasks, nine total model attempts and
USD 0.10 combined conservative estimated allowance**. Recovery permits at most
eight requests; explicit failure permits one. Each task retains USD 0.05 estimated,
60 active seconds, ten seconds/tool (including the retry) and <=512 output tokens.
SDK automatic retries remain disabled. Setup/shutdown time is not claimed as
part of the existing Agent's cumulative active-time counter.

The fixed CLI evidence root is artifacts/live_submission. Both commands must use
the same checkout/root. A nonblocking OS file lock serializes scenario processes.
A durable SQLite plan ledger allocates each scenario once and reserves cost and
an attempt immediately before each SDK call, in addition to the Agent's own
reservations. It counts failed requests too. Before a request, it enforces the
scenario cap, nine-attempt total, both USD caps, and no pending/unknown reservation.
Actual returned usage reconciles both ledgers. Cached input discounts apply only
to reported cached tokens; absent cache details stay null and use conservative
uncached costing, rather than a fabricated provider-confirmed zero. An unknown/invalid reply, usage
outside the conservative bound, crash, failed safety check or aborted run blocks
all further attempts. An interrupted reservation remains held; it is not freed.

Each scenario has an exclusively created directory and attempt.lock. Neither is
removed on failure. SQLite synchronous=FULL persists plan reservations. Reports,
pricing snapshots and locks use exclusive creation; JSONL is append-only from
actual execution. A crash can leave incomplete evidence: retain it and stop,
never clear a lock or reconstruct the missing records. No automatic task resumption
or second scenario execution exists. Manually changing roots, restoring/deleting
state or making calls outside this runner is outside its allowance guarantees.

These are **estimated** caps, not an OpenAI invoice ceiling. Unexpected provider
usage is recorded truthfully even if it exceeds a reservation; no later call is
allowed. Costs are never converted to fabricated zero. Provider-side project
limits/alerts are additional protection and may not be hard spending limits.

## Model/pricing checks and limits of preflight

Configuration requires gpt-6-luna, Standard/default processing, explicit
reasoning_effort=none, and the dated official pricing excerpt: input USD 0.10,
output USD 0.50, cached input USD 0.01 per million. Pricing.load enforces the real
current date in the declared verification timezone, 30-day freshness, future-date
rejection, model/tier/source/provenance and positive finite rates. The prepared
runner additionally checks exact reviewed rates/model documentation/compatibility
and binds the historical snapshot hash in the shared plan. Changed pricing or
mode fails closed rather than repricing previous work.

Preflight verifies stored configuration, not independently fetched current
official pricing, API account availability, network access, live tool selection
or billing. Before a separately approved execution, recheck official model and
pricing pages and the account's model access; if anything changed, stop for review.
No alternate endpoint, model or processing tier is silently selected.

## Private evidence, review and export

Under artifacts/live_submission:

```text
plan.active.lock
plan.sqlite3
near_failure_recovery/     # created only by its authorized attempt
  attempt.lock
  model_pricing.json
  synthetic.sqlite3
  events/<task-id>.openai.jsonl
  report.openai.json
explicit_failure/          # equivalent evidence for its own attempt
```

Original databases contain synthetic transcripts/capability hashes and remain
private. Reports use allowlisted metadata, never raw model text, arguments,
credentials, security references or exception strings. SDK/HTTP debug logging
is suppressed for the live section, including descendant loggers; API-key
environment variables are removed from the runner process after SDK construction.
The child MCP environment does not receive the key. The parent shell needs its
own cleanup, which the scoped commands below provide.

Reports cross-check task/state/terminal events, seven-tool discovery, actual
audit order, tool failure/retry/success order, usage records, request counts,
pricing versions, task and plan costs, limits and absence of writes/consent.
The failure scenario is PASS only for expected terminal failure; its status
remains turn_limit. Other failures retain FAIL, including constructor/setup errors
with no_provider_execution provenance when no provider execution started.

The run's Git commit and Python/SDK versions are recorded on completed report
generation. SDK response/request identifiers and independent provider receipts
are not currently captured. Price/name anchors are not a complete semantic
grounding certificate: privately inspect the actual final answer against stored
tool results after recovery. Do not publish raw transcript/database content.

No official submission trace is automatically produced. After independent offline
validation and human grounding review, follow EVIDENCE_IMPORT_PROTOCOL.md to
copy qualifying genuine events unchanged to the two official filenames. Preserve
source hashes and original locks/databases; record any export redactions separately.
No provider invoice verification or live compatibility result is claimed now.

## Exact Codespaces commands — live commands need later approval

After this runner has been reviewed, committed and merged through a separately
approved workflow, open Codespaces on main. Do not run paid commands from an
uncommitted local patch. In the repository root:

```sh
git switch main
git pull --ff-only
uv sync --frozen
git status --short
export APP_ENV=development
export OPENAI_MODEL=gpt-6-luna
export MODEL_PRICING_FILE=config/model_pricing.json
.venv/bin/python -m yemen_customer_service.evidence.live --scenario near_failure_recovery --preflight
.venv/bin/python -m yemen_customer_service.evidence.live --scenario explicit_failure --preflight
```

The working tree must be clean. Review preflight output, current pricing, the
approved two-task allowance and absence of old attempts. Do not remove an old
evidence root to make preflight pass. The following commands are for later
explicit paid approval only; no key is requested during preparation. Each uses
a hidden prompt in a subshell so the value is not echoed, stored in command
history or retained as an exported parent-shell variable. Do not use shell tracing.

First, approved recovery attempt only:

```sh
(
  set +x
  unset OPENAI_API_KEY OPENAI_LOG
  read -r -s -p 'OpenAI API key (hidden, approved run only): ' LLM_API_KEY
  printf '\n'
  export LLM_API_KEY
  trap 'unset LLM_API_KEY OPENAI_API_KEY OPENAI_LOG' EXIT
  .venv/bin/python -m yemen_customer_service.evidence.live --scenario near_failure_recovery --allow-paid --approve-plan --enable-demo-auth
)
```

STOP if the exit status is nonzero or the report is not PASS. Privately review the
report, original answer, trace and SQLite evidence before the next approved task.
Do not rerun recovery regardless of outcome. After successful review and approval
for the second task, run only:

```sh
(
  set +x
  unset OPENAI_API_KEY OPENAI_LOG
  read -r -s -p 'OpenAI API key (hidden, approved run only): ' LLM_API_KEY
  printf '\n'
  export LLM_API_KEY
  trap 'unset LLM_API_KEY OPENAI_API_KEY OPENAI_LOG' EXIT
  .venv/bin/python -m yemen_customer_service.evidence.live --scenario explicit_failure --allow-paid --approve-plan --enable-demo-auth
)
unset LLM_API_KEY OPENAI_API_KEY OPENAI_LOG
```

Without paid flags, no further API calls are enabled by this runner. Both permanent
attempt locks also prevent repetition. Other applications using the same key are
outside this runner's controls. Revoke/disable the dedicated project key in the
provider console when finished if no further use is authorized. Never share it here.

## Offline verification and retained defects

Tests use SDK HTTP fixtures with genuine MCP, plus direct durable-ledger checks:
missing flags/key, read-only preflight, production/dirty-source rejection,
stale/future/wrong pricing, model mismatch, concurrent process lock, one-attempt
preservation, symlinks/submission paths, two tasks/nine requests, per-task/shared
reservations, unknown/inflight usage across restart, fixture/live mode mismatch,
unqualified answers/ticket proposals, denied writes/private reads, descendant SDK
log suppression and no extra request after a cap.

Initial focused run: 38 passed / 1 failed, 8.20 seconds. A valid price followed by
sentence punctuation was rejected by the new grounding regex. The runner now
reuses the existing reviewed smoke price_anchor helper, with tests for punctuation,
USD 250, USD 25.50 and wrong prices. Initial XML and four initial execution
directories are retained in ignored artifacts/phase5-live-runner-tests/.
Corrected focused run before the final logging test: 51 passed / 0 failed /
0 skipped, 8.47 seconds. The subsequent full regression includes the final logging test.


## Final executed verification

```sh
PHASE4_EVIDENCE_DIR=artifacts/phase5-live-runner-tests/security-regression TRACE_SCENARIO_EVIDENCE=artifacts/phase5-live-runner-tests/legacy-scenarios LIVE_RUNNER_TEST_EVIDENCE=artifacts/phase5-live-runner-tests/final-cases .venv/bin/pytest -q --tb=short --junitxml=artifacts/phase5-live-runner-tests/full-suite.xml
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python --cache-dir /tmp/phase5-live-runner-uv-cache
uv lock --check --offline --cache-dir /tmp/phase5-live-runner-uv-cache
uv build --offline --cache-dir /tmp/phase4-uv-cache
git diff --check
```

- **187 passed, 0 failed, 0 skipped**, 78.95 seconds: existing 142 regressions
  plus 45 new safety/integration tests. No existing test assertions were weakened.
- Ruff lint and format passed (69 files already formatted).
- Dependency check: 61 installed packages compatible; lock check: 64 resolved
  packages; source distribution and wheel builds succeeded. No dependency changes.
- Both scenario preflight commands executed locally: PREPARED_ONLY_NO_REQUEST,
  credential configured=false, no scenario locks, and no live_submission directory
  created. No SDK client, request, price-page retrieval or paid run was used.
- AST comparisons confirm the reviewed recovery class and controlled fault server
  were moved without semantic changes. Production agent/storage/tool/UI sources
  and success_1.jsonl are byte-identical to the merged baseline.
- Fixture run reports and actual MCP traces/databases are private under the test
  artifact directory, with provider_fixture labels. Deliberate unknown/wrong-answer/
  ticket-proposal controls remain FAIL and block subsequent scenario claims.
- Documentation links, new-file whitespace, credential patterns, source import
  review, success hash and absence of the two official submission files checked.

Ready for code review and later separately approved live execution; not a claim
that either live scenario passed. No credentials were requested or displayed,
no paid requests were made, and no commits, pushes or hosting actions occurred.
