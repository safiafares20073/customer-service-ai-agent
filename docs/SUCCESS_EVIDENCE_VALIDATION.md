# Live OpenAI success evidence — validation report

**Result: PASS for inspected internal consistency and sanitization checks.**

- Task: `fa24226fb82347b299bf17662bead7ac`
- Model: `gpt-6-luna`; provider `openai`; reported live evidence label `live_openai`.
- Outcome: `completed`, 10 trace events, 3 model requests, 2 successful MCP calls (`search_products`, `get_store_policies`).
- Token usage: **2,789 input**, **82 output**, **0 cached input** as recorded.
- Recomputed API usage cost: **USD 0.0003199**, using historical snapshot input $0.10/M, output $0.50/M, cached $0.01/M.
- SQLite `tasks`, `cost_records`, and `audits` corroborate the trace; zero support-ticket writes.
- Answer correctly describes synthetic **Example Headphones ($25)** and **14-day returns with original receipt**, based on the report's verified facts.
- Trace passed a limited secret-pattern and allowlisted-field scan. No evidence-line redactions were needed; `traces/success_1.jsonl` is a **byte-for-byte copy** of the original JSONL.

## Validation scope and limits

- The evidence was supplied as a ZIP exported from GitHub Codespaces by the user; checked internally against its SQLite ledger, report, and pricing snapshot. No independent provider receipt or HTTP request log is available to independently authenticate the OpenAI calls.
- The ZIP's source hashes were not accompanied by a separately trusted Codespaces manifest; the hashes below establish integrity of **this received bundle**, not source origin.
- Database was inspected read-only, not included in the public trace export. No API calls or paid actions were performed during validation.
- Cost is calculated from returned usage and configured rate snapshot, **not a verified invoice**.
- This is one successful task, not a completion of the two other required recovery/failure traces.
- Before GitHub publication, review file against repository policy. Do not commit the original ZIP, database, lock, or full raw report.

## Verification checks

- PASS: Archive contains only expected five regular files
- PASS: Exactly ten ordered events
- PASS: All events tagged live OpenAI and same task
- PASS: Task complete in report and trace
- PASS: Three usage records
- PASS: Two authorized MCP tools successful
- PASS: Token totals
- PASS: Cached tokens recorded as zero
- PASS: Cost recomputed from historical pricing
- PASS: Report individual usage matches trace
- PASS: Model and pricing snapshot consistent
- PASS: SQLite task is completed within per-task budget
- PASS: SQLite usage agrees with three provider records
- PASS: SQLite MCP and agent audits match success
- PASS: Read-only run created zero tickets
- PASS: Report fact grounding manually compared with supplied synthetic facts
- PASS: No detected sensitive patterns in JSONL
- PASS: Only expected trace fields
- PASS: Trace timestamps ordered
- PASS: Report automated checks passed, invoice not verified

## File checksums (SHA-256 of received bundle entries)

- `artifacts/live_smoke/attempt.lock`: `740d6a3604a94b25c21168ba638c7957a38ccf4fede8c030e56bf077dcf0d09d`
- `artifacts/live_smoke/events/fa24226fb82347b299bf17662bead7ac.openai.jsonl`: `5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb`
- `artifacts/live_smoke/report.openai.json`: `2ca9c53634db46926883b444884cf4ee873b4b185c19b5a59abaaa70419c3bea`
- `artifacts/live_smoke/synthetic.sqlite3`: `499f6e07cbf414e0beab3de3fcf01cb05ff5ab3588eca9990e2894d7cd2ec55b`
- `config/model_pricing.json`: `679ff95e3e5ad11742a7cce9253017f8b3d6d833e28a0068caa9e94d24d4bdb6`

## Submission trace SHA-256

`5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb`

## Repository import review — November 3, 2026 (Asia/Aden)

The supplied report above is retained verbatim; this section records additional
checks executed in this workspace. Its five-file archive check refers to the
original live_evidence_bundle.zip. The later success_evidence_reviewed.zip
contains exactly two regular files: this supplied report and the success trace.
Both archives passed path, duplicate-name, link/type, encryption and size checks
before extraction into distinct private ignored receipt directories.

- Original ZIP SHA256:
  `c2e9e5ce0530418060b249ac3704f4623a96ba74ce5e6852704ea324a7a6f568`.
- Reviewed ZIP SHA256:
  `1aece295e35d4e352e0e591927528dd320cfbc6e0e902db0cc760d8a788e1750`.
- The reviewed trace, original trace and submission trace have identical bytes
  and the SHA256 printed above. No lines, values, timestamps or labels changed.
- All five original entry hashes match this report and the receipt inventory
  before and after validation, including attempt.lock. Uploaded ZIPs and private
  original evidence remain unchanged. No initialization, migrations or writes
  were performed against the original database; SQLite used mode=ro, query_only,
  trusted_schema off and disabled extension loading. Integrity check returned ok.
- Ten offline unittest checks passed: integrity/hashes, strict JSON/schema and
  event order, terminal task/state/report, MCP audit/transcript agreement, three
  usage records, Decimal totals, model/pricing/limits, answer grounding/no writes,
  public-export safety, and read-only database preservation. Network sockets were
  disabled in the validator. Duplicate JSON keys and nonfinite values are rejected.
- Recorded MCP audits are allow/OK for search_products and get_store_policies,
  followed by agent allow/COMPLETED. Assistant call IDs match successful tool
  responses. Three cost snapshots record usage_source=openai and cached input 0;
  their values agree with report and trace. This corroborates recorded MCP
  execution; no raw transport handshake capture is present in the bundle.
- Grounding was separately reviewed against stored tool responses: one USD 25
  Example Headphones product and the 14-day/original-receipt returns policy. The
  final answer reports these facts without claiming a ticket or order action.
- Both public files passed limited credential/email/private-key/token patterns.
  The trace contains only allowlisted metadata and no prompts, answers, customer
  identity, consent/access references or session hashes. Private database token
  hashes were also checked for absence from both public files. The task UUID is
  an execution correlation identifier, not an authentication capability.

The historical pricing snapshot hash differs from the current repository file;
validation used the received historical bytes and matching pricing version, not
silent repricing. The run's exact source commit and provider response/request
receipts are not included, so this review does not authenticate provider origin,
attribute execution to an exact repository commit, establish current model access,
or verify billing. SHA256 establishes received-file integrity only. One recorded
success does not establish all five live inputs or live adversarial robustness.

The offline validator and output are retained privately under
artifacts/success-evidence-validation/. Public artifacts exclude the raw database,
original report, attempt lock, receipt inventories and transcripts.

## Regression results for this import

- `python /tmp/validate_success_evidence.py`: **10 passed, 0 failed**; no skips
  (a copy and captured output are retained under the private validation directory).
- `PHASE4_EVIDENCE_DIR=artifacts/success-evidence-validation/regression .venv/bin/pytest -q --tb=short --junitxml=artifacts/success-evidence-validation/regression.xml`:
  **135 passed, 0 failed, 0 skipped**, 78.54 seconds. Provider-fixture regressions
  use genuine MCP subprocesses; this command does not repeat live OpenAI execution.
- `.venv/bin/ruff check .`: passed.
- `.venv/bin/ruff format --check .`: 58 files already formatted.
- `uv pip check --python .venv/bin/python --cache-dir /tmp/phase5-evidence-uv-cache`:
  61 installed packages compatible.
- `uv lock --check --offline --cache-dir /tmp/phase5-evidence-uv-cache`: passed,
  64 resolved packages.
- `git diff --check`, document-link checks, new-file whitespace/credential checks
  and exact changed-file inventory: passed. No application code, tests or locked
  dependencies changed. No commit, push, deployment or paid API call occurred.

Remaining Phase 5 work: recovery and explicit-failure execution traces; measured
cost-analysis document and monthly projection; secure authenticated hosting and
public URL; browser/mobile/Arabic visual review; final README/deployment guide
and submission checks. Provider invoice reconciliation remains unverified.
