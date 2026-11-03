# Recovery evidence — independent ZIP review

**Result: PASS for bundle consistency and safety checks.**

- Scenario: `near_failure_recovery` (controlled read fault, harness-only recovery, not model-led self-repair).
- Source commit reported: `0e9632abc93ceefd41e7bcf569c9a84de9e69dd4`.
- Task: `561a396ba302496aa17a278bc928daff`; terminal status `completed`; model requests **2**.
- MCP sequence: `list_products` error (`INTERNAL_ERROR`) → retrying → success, followed by task completion.
- JSONL events: **9**, preserved byte for byte.
- Usage: **1,861 input**, **53 output**, **0 cached input** tokens.
- Computed cost: **USD 0.0002126** from captured usage and supplied historical rate snapshot; no provider invoice verification.
- SQLite task, tool audits and cost records match the report and trace; the durable plan ledger records a single passed recovery attempt and two recorded calls.
- Zero support tickets and zero confirmations recorded. Private databases, ledger and attempt lock are excluded from this public ZIP.

## Validation method and scope

Inspected supplied `recovery_evidence_bundle.zip`, exactly six regular entries. Validated archive filenames/types, duplicate/encryption/size limits; parsed nine JSONL events; matched task IDs, labels, event sequence and timestamps, reports, usage, historical rates and exact Decimal totals. Inspected both SQLite databases in temporary files with read-only connections; verified `PRAGMA integrity_check` and matching task, audit, cost and plan states. Basic credential-pattern scanning found no obvious secrets in the exported trace.

**Checks:** `26`/`26` passed. No OpenAI API calls were made during review. The ZIP came from the user, not directly from a provider. Its contents and model responses are not independently authenticated via provider receipts; hashes establish integrity of supplied bytes only. The final answer is not included in this public trace, so independent semantic grounding cannot be fully demonstrated from the export alone. Source commit is taken from the supplied report, not authenticated against a provider response. No screenshot, billed receipt, or deployment was verified.

## Provenance and hashes

- Original ZIP SHA-256: `40391abb1ee84b3fd8d2f9c69fd118b2321123362d5eae7c38f77199b4dea786`
- Original trace SHA-256: `55e903d6b3726a5d13d68091a77ac6cee92de0bc99a7a8c57f947de359e6a841`
- Public submission trace SHA-256: `55e903d6b3726a5d13d68091a77ac6cee92de0bc99a7a8c57f947de359e6a841` (unchanged bytes)
- Report and raw database records inspected privately; neither is included in the public submission.

## Follow-up

Import `traces/near_failure_recovery.jsonl` into the repository **without changing its bytes**, attach this report under `docs/RECOVERY_EVIDENCE_VALIDATION.md`, update the requirements matrix/checklist, run offline regression, and request review before commit/merge. Do not claim the separate explicit-failure trace is complete or send further paid requests without separate approval.

## Repository import verification — November 3, 2026 (Asia/Aden)

The preceding independent report is retained verbatim. The current import review
received recovery_evidence_reviewed.zip, which contains exactly two regular files:
this report and traces/near_failure_recovery.jsonl. The six-entry original recovery
bundle, SQLite databases, plan ledger, attempt.lock and raw final answer were not
supplied here. Their checks above are the prior reviewer's findings, not newly
repeated database or semantic-grounding checks in this workspace. The original
ZIP hash above is a reported provenance identifier, not independently rehashed.

- Received reviewed ZIP SHA256:
  `c2b736dfd9a67360bd5807d540cc16ce99cf40d03f09ccc04c4320fa4454dbc3`.
- Independently computed received/submission trace SHA256:
  `55e903d6b3726a5d13d68091a77ac6cee92de0bc99a7a8c57f947de359e6a841`.
  This equals both hashes in the supplied report. The export is byte-identical;
  no event, timestamp, ordering, label or value was changed and no redaction was
  needed. Equality corroborates the report's original-hash claim but does not
  authenticate a provider receipt or independently establish source origin.
- ZIP paths, exact member names, duplicate names, encryption, file types, links
  and uncompressed sizes were checked before private extraction. Entry CRCs were
  verified when reading. Both originals and receipt hashes remain private under
  ignored artifacts/evidence-imports/reviewed-recovery-c2b736df/.
- Ten local offline unittest checks passed: archive/hash consistency, rejection
  of duplicate JSON keys/nonfinite values, event-specific field allowlists,
  correlation/provider labels, exact recovery sequence, ordered timezone-aware
  timestamps, completed outcome, usage/cost arithmetic, conservative reservations,
  trace limits, report consistency and safety, and unchanged prior success trace.
  The ten tests include grouped assertions, not a new claim to reproduce the
  earlier reviewer's 26 private-bundle checks. Network sockets were disabled.
- The actual sequence is started, reserved, usage, tool(error/INTERNAL_ERROR),
  tool(retrying/INTERNAL_ERROR), tool(success), reserved, usage, finished(completed).
  All nine lines share task 561a396ba302496aa17a278bc928daff and live_openai labels.
  The retry control event is not a third MCP call. This corroborates recorded
  controlled harness recovery, not a new execution or model-led repair.
- Returned usage records contain 850/17 and 1011/36 input/output tokens, cached 0
  in each. Decimal recomputation with the report's historical Standard rates
  (USD 0.10 input, 0.50 output, 0.01 cached per million) yields USD 0.0000935 and
  USD 0.0001191, totaling USD 0.0002126. No reasoning subset is added twice.
  The public ZIP lacks the historical pricing snapshot, so its authenticity,
  version hash and original request processing tier were not independently checked.
- Recorded reservations cover actual computed costs while remaining below USD
  0.05 per task. Two counted requests and 6.203943762000108 active seconds remain
  below the eight-request/60-second task limits; the recorded error-to-success
  span is below ten seconds. Trace timing is corroborative, not an independent
  wall-clock or transport measurement.
- Both public files passed limited credential, bearer-token, email, private-key,
  userinfo-URL and API-key pattern scans. The trace uses only allowlisted metadata
  and contains no raw text, customer identity, session hashes, authorization or
  confirmation references. Task correlation UUIDs and artifact SHA256s are not
  authentication capabilities. No private database, ZIP or lock is publicly added.

Provider invoices, request receipts, source-commit execution attribution and the
full final answer remain unverified from this public bundle. The first report's
source commit is a supplied assertion. The unchanged public trace and reviewed
report support the recovery submission artifact with these explicit limitations.
No original evidence was overwritten, initialized, migrated or deleted.

## Executed offline regression and static results for this import

- `.venv/bin/python /tmp/validate_recovery_import.py`: **10 passed, 0 failed,
  0 skipped**. Validator and captured output retained privately under
  artifacts/recovery-evidence-validation/.
- `PHASE4_EVIDENCE_DIR=artifacts/recovery-evidence-validation/security TRACE_SCENARIO_EVIDENCE=artifacts/recovery-evidence-validation/scenarios LIVE_RUNNER_TEST_EVIDENCE=artifacts/recovery-evidence-validation/cases .venv/bin/pytest -q --tb=short --junitxml=artifacts/recovery-evidence-validation/full-suite.xml`:
  **187 passed, 0 failed, 0 skipped**, 90.20 seconds. These are offline provider-
  fixture regressions with genuine MCP subprocesses, not additional live runs.
- `.venv/bin/ruff check .`: passed.
- `.venv/bin/ruff format --check .`: passed, 70 files already formatted.
- `uv pip check --python .venv/bin/python --cache-dir /tmp/recovery-evidence-uv-cache`:
  61 installed packages compatible.
- `uv lock --check --offline --cache-dir /tmp/recovery-evidence-uv-cache`: passed,
  64 resolved packages.
- `git diff --check`, Markdown-link checks, credential-pattern review and new-file
  whitespace checks: passed. Four intended files only. No application, test,
  dependency or prior success-trace changes; no private bundle/database/lock added
  to the public file set. All received original entry and archive hashes preserved.

Only explicit_failure.jsonl remains among the three required submission traces.
Cost analysis, secure hosting/authentication, visual/browser/RTL review and final
submission documentation remain incomplete. No API requests, commits, pushes,
merges or deployments were performed during this import.
