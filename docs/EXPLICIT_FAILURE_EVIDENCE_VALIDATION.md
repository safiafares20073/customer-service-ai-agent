# Explicit-failure live evidence — independent review

**Result: PASS (34/34 local integrity and consistency checks).**

Source: privately supplied `failure_evidence_bundle.zip`; review performed on its received bytes, without live network or provider calls. The report and trace are **execution records labeled `live_openai`**, not independently authenticated provider receipts.

## Evidence and outcome

- Task ID: `d4d9f9a23d3447d8952ffa3610883947`. Source commit recorded by runner: `6f181405cb5f5557f57e41f69fdf1a3bd607d36c`.
- Scenario: `explicit_failure` (one-model-request task limit). Final outcome: **`turn_limit`**, with acceptance result **PASS**. This is a genuine recorded terminal incomplete task, **not a successful completed customer answer**.
- Events: five in their original sequence: `started → reserved → usage → tool(success) → finished(turn_limit)`. Tool called: `list_products`.
- Report, task database and shared plan agree: **one model request**, **850 input / 17 output / 0 cached input tokens**, computed **USD 0.0000935**. Usage cost recomputed from bundled 2026-11-03 Standard prices: $0.10/M input, $0.50/M output, $0.01/M cached input.
- MCP/database audits: `list_products allow/OK`, `agent deny/TURN_LIMIT`; zero created tickets, memory records, order-access grants, and confirmations.
- The shared plan records recovery and explicit-failure cases as `passed`, with three recorded model requests overall. Persistent `attempt.lock` exists and was **not** modified.
- Runtime report declared 13 acceptance checks true; current review independently checked bundle structure, trace consistency, SHA-256, SQL records, cost arithmetic and public-export safety.

## Checks (34 passed)

- PASS: Expected six archive entries
- PASS: Safe regular file entries
- PASS: Bounded archive sizes
- PASS: Original trace hash matches report
- PASS: Exactly five events
- PASS: Expected event order
- PASS: One task ID across events
- PASS: Live evidence labels consistent
- PASS: Event timestamps ordered
- PASS: Final event records turn limit
- PASS: One successful permitted read
- PASS: One model request in report
- PASS: Runner internal checks passed
- PASS: Source revision recorded
- PASS: Agent duration within bound
- PASS: Historical dated pricing consistent
- PASS: Usage matches report
- PASS: Cost recomputed with historical rates
- PASS: Estimated reservation within cap
- PASS: Audit report matches expected
- PASS: No secrets in public trace
- PASS: Trace uses expected fields only
- PASS: Both SQLite databases intact
- PASS: Plan records two successful tasks
- PASS: Plan contains three recorded API calls
- PASS: Explicit-failure plan matches trace
- PASS: Shared plan stayed within task and combined limits
- PASS: Task database records terminal outcome
- PASS: Task database cost matches evidence
- PASS: Database audits match expected
- PASS: No ticket, memory or confirmation writes
- PASS: Exactly one task record
- PASS: Attempt lock retained
- PASS: Report expressly disclaims invoice verification

## Source integrity

- Original live JSONL SHA-256: `a8bd7b17b4c7d2adb2810d28ba60622109b0b2be02a639e750713ea2abe0fbe6`.
- Original bundle SHA-256: `c0341b9506859a0a539da435df6f61a2db9b11f19dd0d4416f40b1a2eccd364b`.
- The submission JSONL is copied **byte-for-byte** into `traces/explicit_failure.jsonl`; no edits, fabricated events or redactions.
- The reviewed deliverable ZIP includes **only** this JSONL and this Markdown report. Original SQLite databases, full runner report, private pricing snapshot, secret-derived session hashes and permanent lock are **excluded**. The originals remain in the private Codespaces evidence directory; this ZIP does not delete or alter them.

## Limitations

- The private SQLite files corroborate the received report and trace, but their source origin, the provider exchange, request IDs and invoice were not independently authenticated. File hashing establishes integrity of the **received** evidence, not external provenance.
- Price is an **estimated usage calculation**, not confirmed billed cost. This review does not assert current model access or prices.
- The scenario demonstrates honest termination on a deliberately reduced **one-request** limit; it does not establish a natural outage, provider failure, or automatic error recovery. The separately recorded `near_failure_recovery` scenario covers recovery.
- The tool was a read-only catalog lookup with a synthetic data store; do not interpret this as evidence of production customer safety or a live hosted deployment.
- Credential/privacy detection is a limited syntactic scan, not a guarantee against every possible secret. No public trace fields include content, identities, prompt text, response bodies or capabilities.

## Submission follow-up

Import `traces/explicit_failure.jsonl` and `docs/EXPLICIT_FAILURE_EVIDENCE_VALIDATION.md`, update `docs/REQUIREMENTS_MATRIX.md` and `docs/FINAL_SUBMISSION_CHECKLIST.md`, rerun offline/full tests and static checks, and request branch review before merging. No further OpenAI paid runs are needed to preserve this evidence.

## Repository import review — November 4, 2026 (Asia/Aden)

The independent report above is preserved verbatim. This workspace received only
failure_evidence_reviewed.zip containing the public trace and this report. The
six-entry original bundle, private SQLite databases, pricing snapshot, full runtime
report, plan ledger and attempt.lock were not supplied here. The 34 checks above
are attributed to the original reviewer; they were not repeated against private
SQLite in this import. The original bundle hash is a supplied provenance claim,
not an archive independently rehashed in this workspace.

- Received reviewed ZIP SHA256:
  `c7688cb26661bafbadc41ded0eecf4ec73bf4f1e5fd673e18b73117895077474`.
- Received trace and unchanged submission export SHA256:
  `a8bd7b17b4c7d2adb2810d28ba60622109b0b2be02a639e750713ea2abe0fbe6`.
  This matches the user-required original hash and the independent report. It
  establishes received-byte integrity, not independently authenticated API origin.
- Exactly two regular archive members passed bounded-size, path traversal,
  absolute/Windows path, duplicate-name, encryption/type/link and CRC checks.
  Original entries and a receipt inventory were retained privately in ignored
  artifacts/evidence-imports/reviewed-explicit-failure-c7688cb2/.
- Eleven local offline tests independently checked the supplied hash/bytes,
  strict JSON parsing (duplicate keys and nonfinite values rejected), event-specific
  field allowlists, task/provider/evidence labels, exact event order, timestamps,
  terminal outcome, single-request counters, reservations and limits, Decimal cost,
  report consistency/disclosures, credential patterns and all three trace hashes.
  Network sockets were disabled; no SDK provider or MCP session was constructed
  by this file validator. These checks do not reexecute the recorded task.
- The actual order is started, reserved, usage, tool(success), finished(turn_limit).
  All five lines use task d4d9f9a23d3447d8952ffa3610883947 and live_openai labels.
  One reservation and one usage event are recorded. No extra request or fabricated
  success appears. Terminal task status remains turn_limit; acceptance PASS means
  the intended failure evidence qualifies, not that the customer task completed.
- The sole tool event is list_products success. Private audit assertions
  (allow/OK then agent deny/TURN_LIMIT), no-write findings and shared-plan states
  belong to the prior report; this public ZIP cannot independently reproduce them.
- Recorded 850 input, 17 output and 0 cached tokens yield USD 0.0000935 with the
  report's historical Standard rates (0.10/0.50/0.01 USD per million). The USD
  0.0015978 reservation covers that calculation and is below the USD 0.05 task cap.
  One counted turn and 2.754383993999909 recorded active seconds are within the
  disclosed one-request/60-second allowances. Trace timestamps are corroborative,
  not independent wall-clock measurement. The original pricing snapshot/tier and
  provider receipts are not in this ZIP; billing remains independently unverified.
- The source revision named in the report exists as latest merged main at import
  (`6f181405cb5f5557f57e41f69fdf1a3bd607d36c`) and its tracked tree matches the
  local baseline. This checks repository existence/content, not API execution
  attribution to that revision or independent authenticity of model responses.
- Both public files passed limited API-key/token/private-key/email/userinfo-URL
  and bearer-credential scans. Trace values contain only expected metadata: no
  customer identity, prompts/answers, tool arguments, session hashes, access or
  confirmation references. Task UUIDs and artifact SHA256s are correlation/integrity
  identifiers, not authorization capabilities. No database, ZIP, pricing snapshot,
  attempt lock or raw private report is included in the public change set.

All three official trace files now match their reviewed original hashes. Recorded
live usage is not an independently verified provider invoice; the prior reviewers'
private-bundle findings and this import's public-file checks remain distinguished.
No event was edited or reconstructed. No paid API request was made during import.

## Executed offline verification for repository publication

- `.venv/bin/python /tmp/validate_explicit_failure_import.py`: **11 passed,
  0 failed, 0 skipped**. Validator and output are retained privately under ignored
  artifacts/explicit-failure-evidence-validation/.
- `PHASE4_EVIDENCE_DIR=artifacts/explicit-failure-evidence-validation/security TRACE_SCENARIO_EVIDENCE=artifacts/explicit-failure-evidence-validation/scenarios LIVE_RUNNER_TEST_EVIDENCE=artifacts/explicit-failure-evidence-validation/cases .venv/bin/pytest -q --tb=short --junitxml=artifacts/explicit-failure-evidence-validation/full-suite.xml`:
  **187 passed, 0 failed, 0 skipped**, 76.79 seconds. Includes existing permission,
  authorization, confirmation/replay, prompt-injection, redaction, SDK import,
  spending and fixture/live-provenance tests with genuine MCP transport.
  Regression provider responses are fixtures, not new live-model evidence.
- `.venv/bin/ruff check .`: passed.
- `.venv/bin/ruff format --check .`: passed, 71 files already formatted.
- `uv pip check --python .venv/bin/python --cache-dir /tmp/failure-evidence-uv-cache`:
  61 installed packages compatible.
- `uv lock --check --offline --cache-dir /tmp/failure-evidence-uv-cache`: passed,
  64 resolved packages.
- `uv build --offline --cache-dir /tmp/phase4-uv-cache`: source distribution and
  wheel built successfully; build outputs remain ignored.
- `git diff --check`, document links, new-file whitespace, credential-pattern and
  exact four-file inventory checks: passed. Public files exclude databases,
  private ZIPs, pricing snapshots, raw runner reports, credentials and attempt locks.
  Existing source/tests/dependencies and the prior two trace bytes are unchanged.

All three trace artifacts qualify for independent GitHub review, not a claim
that the overall capstone is submitted or that provider billing is verified.
Cost analysis, hosted demo/authentication, browser/mobile/RTL visual review and
final submission documentation remain separate pending deliverables. No paid
requests or deployment occurred during this import. Publication is permitted
only after these checks; merging still requires separate approval.
