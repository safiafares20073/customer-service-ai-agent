# Remaining trace scenarios: offline rehearsal and live-run plan

Date: 2026-11-03 (Asia/Aden). Baseline: merged main
`c051375cae765f22229d06aec6b288eb8e76ad82`. The previous local success-evidence
commit had identical tracked contents; the clean checkout was detached at the
new merged main before work. No commit, push, deployment or paid request occurs.

Chapter 12.10, printed pp. 579–581, requires saved JSONL and the three exact
submission filenames. It does not prescribe a trace schema or a live provider.
This project's approved evidence standard additionally requires genuine live
submission executions. Therefore these rehearsals are NOT copied into
traces/near_failure_recovery.jsonl or traces/explicit_failure.jsonl. Neither file
is created. The genuine prior success_1.jsonl remains byte-identical, SHA256
`5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb`.

## Design: keep the production failure policy intact

The established Agent stops on unsuccessful tool results, and the production
server marks errors nonretryable. Changing those defaults merely to obtain a
recovery trace would be inappropriate. No src/, SDK, pricing, schema, seven-tool
contract, authorization, confirmation or production trace format is changed.

Instead, tests/trace_scenarios.py supplies an explicitly experimental harness-only
ReadRecoveryClient subclass of the trusted adapter. It calls the inherited MCP
invoke path for every attempt. It retries only list_products, only an explicitly
retryable INTERNAL_ERROR, at most once for the entire task. It does not retry
writes, authorization errors, nonretryable results, timeouts or transport failures.
It checks the same task's known costs/budget before retry; the existing Agent
tool timeout surrounds both attempts, and the existing active-time deadline
surrounds the entire loop. No new model request is made to perform the retry.
No task, principal, session, consent, counters or pricing snapshot is replaced.
This demonstrates controlled harness recovery, NOT automatic production/UI
recovery and NOT model reasoning about an observed fault.

tests/fault_mcp_server.py runs the official FastMCP server with the same seven
tools over real stdio. Its test-only execute wrapper deliberately issues a
SQLite query against a nonexistent table on the first list_products call. The
real OperationalError is sanitized into INTERNAL_ERROR, explicitly retryable
only for this controlled public-read fault. The next actual invocation uses the
normal store query and normal server dispatch. Error/retry events are emitted
when observed/attempted, never reconstructed afterward. The server's existing
audit convention labels a returned error envelope deny/INTERNAL_ERROR; this is
an actual failed storage operation, not an ownership/security-denial scenario.

## Actual rehearsals

Command (no API key required):

```sh
.venv/bin/python -m tests.trace_scenarios
```

The command has no paid option or live provider factory. It uses SDKScript's
official OpenAI SDK HTTP fixtures at fixture.invalid, and initialized genuine
MCP subprocess sessions with discovery. Every trace has provider=fixture and
evidence=provider_fixture. Usage numbers are deliberately scripted, NOT measured
OpenAI tokenization or billing. Fixture tests use the existing November 3 price
snapshot and a fixed historical date; live pricing freshness must not be bypassed.

| Scenario | Actual task / outcome | Actual fixture usage and cost |
| --- | --- | --- |
| Near failure recovery | ccfaaec713a2491fb6acc5b592f2b4b7; completed; first catalog MCP call failed, second succeeded | 2 model requests; 200 input / 40 output / 0 cached; USD 0.00004 fixture calculation |
| Explicit failure | 460619dcb50c4cd2b902ed0730921da0; turn_limit; one real MCP read succeeded but no final answer could be requested | 1 model request; 100 input / 20 output / 0 cached; USD 0.00002 fixture calculation |

Recovery trace has nine actual events: started, reserved, usage,
tool(error), tool(retrying), tool(success), reserved, usage, finished(completed).
The retry event is a control action, not a third MCP invocation. Audits contain
list_products deny/INTERNAL_ERROR, list_products allow/OK, agent allow/COMPLETED.
Final response matches the actual USD 25 synthetic headphones result.

Explicit failure trace has five events: started, reserved, usage, tool(success),
finished(turn_limit). This is a deliberately reduced one-request allowance, below
the eight-request maximum. It produces a deterministic incomplete response,
including the last verified read result, without an extra LLM request. Audits
contain list_products allow/OK and agent deny/TURN_LIMIT. It is a genuine task
failure caused by a disclosed execution constraint, not a security block relabel.

Both executions retain one task ID, cumulative usage and active time, the USD
0.05 estimated budget and 60-second active/10-second tool limits (except the
explicitly reduced turn allowance). Zero tickets or confirmation grants exist.
The persisted tasks, state, cost rows, snapshots, trace usage and terminal events
are cross-checked. Discovery must yield the same seven registered tools.

## Evidence retention and negative controls

Evidence is ignored/private under artifacts/phase5-trace-fixtures/:

- near_failure_recovery-38031a8c34274f638e51771aeed16c63/: report.json,
  events/<task>.fixture.jsonl and synthetic.sqlite3.
- explicit_failure-5e4dd308f5694de19263416387f54c59/: equivalent evidence.
- pytest/: unique directories for every repeated run and negative control.
- focused-initial.xml, focused-after-fix.xml, full-suite.xml: actual test results.
- initial-failures/: copies of four initial harness exceptions, including their
  original traces, FAIL reports and databases, retained outside pytest rotation.

Each run writes its report with exclusive creation even on exceptions. Output
directories use a new UUID; no previous execution is overwritten. Harness
exceptions produce HARNESS_EXCEPTION without raw exception strings in the report.
Fixture output into any resolved traces/ directory is rejected. Raw databases,
capabilities, reports and fixture events must not be committed as submission traces.

Initial focused run: 3 passed / 4 failed, 5.34 seconds. The four negative controls
exposed a harness validator dereferencing an absent last_result after a deliberate
failure. The validator now marks grounding false rather than raising. Application
failure behavior did not change. Initial XML and all four failed runs were retained.
Corrected focused run: 7 passed / 0 failed / 0 skipped, 5.40 seconds.

Persistent-error, nonretryable-error, ACCESS_DENIED and tiny-timeout controls
correctly fail recovery acceptance and retain FAIL reports. Tests pass only if
those failures remain truthful: at most two MCP attempts for persistent error,
one for nonretryable/denial, one model request, no unauthorized writes or consent.
The recovery harness must not transform an unexpected failure into successful
evidence. A new controlled run is a new task; it never rewrites an old trace.

## Separately bounded live evidence plan — approval required

There is no live runner for these cases in this change. No API key is requested.
The current fixture command cannot be switched to live using environment values.

1. Review/approve this harness-only recovery policy and the controlled server
   fault. After that review, prepare a separate paid-gated live runner; reuse the
   existing Agent, Journal, official provider and genuine MCP transport. Keep
   the fault wrapper strictly local and record that recovery is adapter-controlled.
   Add a persistent exclusive attempt lock per scenario. No retries of entire runs.
2. Use an environment with authorized api.openai.com access, such as Codespaces.
   Verify the exact source commit and current official gpt-6-luna Standard prices;
   keep Chat Completions reasoning_effort=none, service_tier=default, no SDK retries,
   and the existing output cap. If pricing/model support changed, stop for review;
   do not use the fixture's fixed-date override or silently substitute a model.
3. Obtain explicit paid approval for at most TWO tasks: recovery <=8 model
   requests / USD 0.05 estimated; failure <=1 request / USD 0.05 estimated.
   Combined maximum nine model attempts, USD 0.10 estimated reservations, 120
   active seconds across the two tasks, and ten seconds per tool operation
   including the recovery retry. Provider billing is not guaranteed by estimates.
   Preserve reservations/unknown usage and stop further execution if costs become
   unknown. No automatic rerun or spending beyond this separate allowance.
4. Securely configure the key locally; do not put it in chat, source, traces or
   terminal output. Live code must instantiate only the approved official provider;
   it must not reuse SDKScript, scripted usage, or prerecorded model responses.
   Use isolated synthetic databases with no real customer data; never host demo auth.
5. Ask for a catalog answer via list_products. For recovery, require the observed
   controlled fault, actual subsequent successful read and grounded final answer
   under one task. For failure, start with one-turn Limits and require an actual
   tool call then a terminal turn_limit with no extra request. An unconstrained
   live model may choose another tool or answer directly: preserve that outcome,
   mark the intended scenario unfulfilled, and stop. Further paid attempts require
   approval; never force-fit events or relabel an unrelated run.
6. Disable paid mode/unset the key afterward. Preserve locks, historical pricing,
   source commit, report, trace, SQLite snapshot and available provider identifiers.
   Apply EVIDENCE_IMPORT_PROTOCOL.md: read-only consistency, audit/usage/budget,
   grounding, secret checks, hash preservation and honest billing limits.
7. Only qualifying live events may be copied to the two exact official paths
   after independent review. Preserve byte order/values/outcomes; document any
   field redaction separately. Keep failed attempts and unknown checks visible.
   Until then, both required submission files remain incomplete.

## Final verification of this change

```sh
.venv/bin/pytest tests/agent/test_trace_scenarios.py -q --tb=short --junitxml=artifacts/phase5-trace-fixtures/focused-after-fix.xml
.venv/bin/python -m tests.trace_scenarios
PHASE4_EVIDENCE_DIR=artifacts/phase5-trace-fixtures/security-regression .venv/bin/pytest -q --tb=short --junitxml=artifacts/phase5-trace-fixtures/full-suite.xml
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python --cache-dir /tmp/phase5-trace-uv-cache
uv lock --check --offline --cache-dir /tmp/phase5-trace-uv-cache
uv build --offline --cache-dir /tmp/phase4-uv-cache
git diff --check
```

- Focused: **7 passed, 0 failed, 0 skipped**, 5.40 seconds.
- CLI rehearsal: both scenarios PASS, with private report paths listed above.
- Full regression: **142 passed, 0 failed, 0 skipped**, 80.00 seconds. All 135
  existing tests and source files remain unchanged; seven new tests are added.
- Ruff lint passed; format check passed (62 files already formatted).
- Dependency compatibility passed (61 installed packages); lock check passed
  (64 resolved packages); source distribution and wheel built successfully.
- Initial lint found one long line, fixed by formatting. Initial offline build
  with the fresh /tmp/phase5-trace-uv-cache failed because setuptools was absent
  from that cache. Reusing the existing populated /tmp/phase4-uv-cache succeeded;
  both logs are retained as build-initial.log and build-final.log. No package
  download, dependency change or fake build result was substituted.
- Tracked and new-file whitespace/link checks, credential-pattern review,
  production-code diff, original 135-test file preservation, success-trace hash,
  fixture event hashes and official-filename absence checks passed.

Only three test/harness files and four documentation files change. No src/,
pricing, dependency, original evidence or submission-trace files change. Remaining
limitations: deterministic provider fixtures cannot prove live behavior, measured
provider usage or invoice costs; the experimental recovery policy is harness-only;
new controlled live executions require a separately prepared gated runner and
explicit spending approval. No hosting work was started.
