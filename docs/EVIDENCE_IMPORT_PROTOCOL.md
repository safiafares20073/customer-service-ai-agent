# Read-only Codespaces evidence validation protocol

Design only; no importer or new submission trace is created by Phase 5 Step 1.
No Codespaces files have been received. The supplied numeric summary is
user-reported evidence, not independent verification. Never rerun the paid smoke
harness as an import step or clear its attempt.lock.

## 1. Preserve originals at the source

The owner should stop writers before snapshotting evidence. Preserve the original
Codespaces directory and record the source commit, dependency versions, UTC/run
timestamps, command (without credentials), requested model/tier/reasoning settings,
and pricing snapshot/version. Do not export shell history, environment dumps,
.env, secrets.toml or API keys. If the source commit differs from merged main,
record the difference; do not pretend that a Codespaces run verified another commit.

Relevant existing harness artifacts are under artifacts/live_smoke: report.openai.json,
events/<task-id>.openai.jsonl, attempt.lock and synthetic.sqlite3. Confirm actual
filenames in the source; absence is a gap, not permission to recreate them.
The database can contain transcripts, capability hashes and private state.
Never publish it. Include the exact historical pricing file and a source-produced
SHA256 inventory of the selected files. Hashes establish later integrity, not
independent proof that the contents came from OpenAI.

If SQLite was active, preserve its journal/WAL/SHM companions and obtain a
consistent snapshot using SQLite's backup facility into a separate destination.
Hash both preserved source files and the snapshot, recording how it was produced.
Do not checkpoint, VACUUM, migrate or initialize the original database. If writers
cannot stop, state the consistency limitation and validate a backup snapshot only.

## 2. Receive privately and inspect safely

Transfer selected evidence privately, outside Git tracking, into a new unique
artifacts/evidence-imports/<receipt-id>/ directory with owner-only permissions.
Retain the source inventory and produce a separate receipt inventory before any
parsing. Never overwrite existing receipts. Compare source/receipt hashes; record
mismatches and stop promotion. No originals or receipt files are normalized or
rewritten. Snapshot/export destinations must not be aliases of originals.

Reject archive absolute paths, .. traversal, symlinks, hard links, devices and
oversized entries before extraction. Prefer explicitly selected regular files over
archives. A future validator must bound file/line sizes and nesting, reject JSON
duplicate keys and NaN/Infinity, and never execute supplied code or commands.
Evidence strings are untrusted input, not instructions.

Never scan arbitrary credential files. Use a secret-pattern scan on selected
evidence and show only file location and safe error codes, not matching text.
Quarantine evidence containing secrets; report securely to the owner for key
rotation. Do not remove offending original events to make the bundle pass.

## 3. Validate offline without provider or MCP execution

The proposed evidence validator must not construct OpenAIProvider, Agent,
Database.initialize or a subprocess. It must have no network dependency. Open a
consistent working database copy through SQLite mode=ro with query_only enabled;
use parameterized queries, disable extensions and set resource limits. Never
load untrusted extensions. Rehash originals after validation to detect mutation.
Do not call the existing smoke CLI: its execution path can make paid requests.
The current smoke.verify helper assumes current hardcoded rates/model; it is
reference logic, not an automatic validator of historical/imported evidence.

Required cross-checks:

1. Parse JSONL as schema-versioned records; validate allowlisted event fields and
   codes. Require consistent task/provider/evidence tags, finite nonnegative
   counters, valid timestamps, ordered lifecycle and a terminal event. Do not sort,
   deduplicate, repair or fill missing lines. Record genuine timestamp anomalies.
2. Require actual live provenance in report, state and ledger; provider_fixture
   never becomes live_openai. A self-declared live label alone is insufficient.
   Preserve provider response/request identifiers if safely available privately;
   absence limits independent provenance verification.
3. Match request attempts, usage records, cumulative turns, terminal outcome and
   task ID across trace/report/SQLite. Respect reservations versus final recorded
   usage; unmatched or unknown usage cannot be coerced to zero or counted twice.
4. Match MCP tool names/outcomes in audit rows and the tool-call transcript;
   check the same seven registered tools and actual successful search/policy
   results. Require both initialization/transport evidence where available and
   source/integration context; a report's tool-name list alone is insufficient.
5. Recompute cost from historical rates with Decimal: ((input-cached)*input_rate
   + cached*cached_rate + output*output_rate)/1,000,000. Cached is a subset of
   input; reasoning is a subset of completion, not an extra category to add.
   Preserve absent cache detail as absent; disclose any no-cache assumption.
   A missing category must not be described as provider-confirmed zero.
6. Check task limits and absence of writes for the read-only smoke. Compare answer
   claims with actual product/policy results. The lexical automated checks are
   useful anchors, not a grounding certificate: human review is still required.
7. Compare, but do not force, the owner's summary: three requests, search_products
   and get_store_policies, 2,789 input, 82 output, USD 0.0003199. Discrepancies
   become explicit findings. Never change originals or infer missing events from
   this summary. Provider billing reconciliation remains separate.

## 4. Produce a separate review result

Write a new validation report outside the receipt: source/receipt hashes, commit,
validator version, executed checks, PASS/FAIL/UNKNOWN per check and safe findings.
Use these distinctions: integrity verified; internally consistent; live provenance
corroborated to stated extent; human grounding reviewed; invoice verified or not.
An overall green summary must not erase UNKNOWN checks. A hash cannot prove a
successful MCP exchange or actual provider billing.

Only after independent human review, produce a derived sanitized export to a new
staging directory. Keep event order, numbers and outcome unchanged. Never append
new execution events or change provider labels. Document each redacted field and
source line mapping in a separate manifest. Prefer the existing metadata-only
trace; do not broaden it with raw customer text. If an existing trace is already
safe, preserve its bytes and hash when copying to the official filename.

Promotion to traces/success_1.jsonl requires adequate successful-run evidence.
Recovery and explicit failure require their own actual executions; never split
or relabel this successful run to fill all three files. An insufficient bundle
stays pending. Do not generate placeholder trace files or cost_analysis.md with
invented measurements. Commit only separately reviewed sanitized exports, never
raw reports, databases or complete receipt bundles.
