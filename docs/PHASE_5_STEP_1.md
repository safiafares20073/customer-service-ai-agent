# Phase 5 Step 1: baseline and submission preparation

Review date: 2026-11-03 (Asia/Aden). This step prepares documentation only.
Hosting, authentication, evidence-import tooling, paid execution, deployment,
Git commits and pushes are not implemented or performed by this step.

## Verified repository baseline

- Remote merged `main`: `0fe6d114e649efa318a7da0bd0350e2b55e56cbe`.
- Local checkout: `phase-4-streamlit-security`, commit
  `a6326ad9abfc59896232f2ccf5d2ffbbec5d2026`.
- Initial working tree was clean. All 59 tracked file paths and their contents
  matched the immutable GitHub archive of remote main. No branch switch, fetch,
  reset, merge or source edit was needed. The local `main` ref remains older;
  it must not be mistaken for the verified remote baseline.
- Downloaded archive SHA256:
  `eeb6a82babe8ec851311a40739fa4dbc14f1013cdc21eea822ca28440e85ca7f`.

Read the specification, supporting design, implementation plan, requirements
matrix, Phase 2/3/4 documents, compatibility audit, live-smoke harness, UI launcher,
controller, database, store, MCP client/server and tracing code during this and
the immediately preceding planning review.

The supplied official PDF was reread using `pdftotext -layout`. Its SHA256 is
`59c0cef8926910152c33342631e6168c1d9a08384fcbc0bbbf9f46f8a4565f27`.
Only section 12.10, printed pages 578–581, is authoritative for the academic
checklist. Section 12.11 and the architecture diagram preceding 12.10 are not
additional requirements. The final cost-analysis parenthesis ends at “monthly
project”; monthly projection is the documented interpretation of incomplete text.

## Evidence boundaries

The last independently executed pre-push regression was 135 passed, 0 failed,
0 skipped in 83.52 seconds. Step 1 does not rerun the application suite or turn
historical tests into new execution evidence. Phase 4 fixtures prove exercised
boundaries, not live-model prompt-injection robustness or browser pixel quality.

The owner reports a Codespaces live run with gpt-6-luna, three model requests,
search_products and get_store_policies over actual MCP, 2,789 input tokens,
82 output tokens, computed USD 0.0003199, and automated_checks_passed=true.
These are uninspected external claims. No Codespaces evidence was supplied or
imported here. The arithmetic matches the current uncached Standard rates; that
does not verify usage provenance, cached categories, answer grounding or billing.
Follow [the evidence protocol](EVIDENCE_IMPORT_PROTOCOL.md) before publication.

The current matrix's “uncommitted Phase 4” statement is historical, and its
live-pending statements mean repository verification is pending. No new live
execution is implied by correcting those status distinctions.

## Next implementation inventory — proposed, not created

Use [the acceptance checklist](FINAL_SUBMISSION_CHECKLIST.md) and
[hosted-demo design](HOSTED_DEMO_DESIGN.md) as the review gates.

| Proposed file | Minimum purpose |
| --- | --- |
| `src/yemen_customer_service/ui/auth.py` | Native OIDC claims validation/allowlist integration and opaque principal lookup; no custom password login |
| `src/yemen_customer_service/ui/hosted.py` | Separate production launcher with fail-closed settings and platform port |
| `src/yemen_customer_service/ui/app.py` | Production login gate, safe logout and authenticated controller selection; retain local guard |
| `src/yemen_customer_service/ui/service.py` | Authenticated session binding, production no-demo initialization, existing consent/task behavior |
| `src/yemen_customer_service/storage/store.py` | Trusted production capability provisioning/revocation; scoped principal creation; demo guard unchanged |
| `src/yemen_customer_service/storage/database.py` | Public-catalog-only initializer if needed; never use seed_demo=True in production |
| `src/yemen_customer_service/tool_server/client.py`, `server.py` | Permit only trusted production capabilities while retaining private stdio and server validation |
| `src/yemen_customer_service/agent/spending.py`, `agent/loop.py` | Durable global/principal reservations, concurrency, kill switch before each request |
| `src/yemen_customer_service/agent/state.py` | Transactional spending/task association only if required; keep task counters intact |
| `src/yemen_customer_service/evidence/validate.py` | Separate offline, read-only validator; no provider construction, import writes or automatic export |
| `render.yaml` | One instance, persistent disk, health/port configuration; no embedded secrets |
| `.streamlit/config.toml`, `.env.example`, `pyproject.toml`, `uv.lock` | Safe production settings, credential names, entry point and only necessary locked dependencies |
| `docs/PHASE_5.md`, `docs/DEPLOYMENT.md` | Actual implementation/results, operator instructions, private reviewer access procedure |
| `README.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/REQUIREMENTS_MATRIX.md` | Truthful final status and evidence links |
| `cost_analysis.md`, three exact `traces/*.jsonl` paths | Create only after actual evidence validation; not placeholders |

These are exact proposed paths, not authority to implement now. A schema change
for identity mapping or atomic shared reservations needs a versioned migration
and migration tests; do not reuse an unrelated table or silently change schema 2.
Prefer no new table for identity mapping if a collision-resistant opaque principal
can safely reference the existing customers table. Confirm installed OIDC support
and identity-claim semantics before finalizing dependencies.

## Proposed no-live test inventory

All tests below are future work; none were created or claimed passed in Step 1.

- `tests/evidence/test_validation.py`: valid fixture-labeled bundle accepted only
  as fixture; fixture-to-live promotion rejected; missing files, duplicate JSON
  keys, nonfinite numbers, malformed lines, mixed task/provider, absent terminal
  events, inconsistent turns/tokens/cost and pricing mismatch rejected; unknown
  usage stays unknown; no original file hash changes; safe redacted diagnostics;
  symlink/path traversal/archive links/oversize input rejected. Use temporary
  test files, never named official submission traces. Reject network attempts.
- `tests/security/test_hosted_auth.py`: missing/unapproved claims, forged account
  selectors, logout/expiry, cross-principal memory/order/task access, development
  mode in production, stale approval and confirmation replay denied via real MCP.
- `tests/ui/test_hosted_app.py`: AppTest login gate, distinct approved users,
  exact draft approval/edit/cancel, safe failures, retained English/Arabic controls.
- `tests/agent/test_shared_spending.py`: concurrent reservations, process restart,
  per-principal/global cap, unknown usage, cancellation, kill switch and exhausted
  allowance cause no further provider call; fixtures only.
- `tests/integration/test_hosted_restart.py`: actual agent/MCP subprocess restarts
  with isolated persistent SQLite, no development seed, capability expiry/revocation,
  unfinished task counters retained, no automatic write replay.
- `tests/unit/test_deployment_config.py`: production refuses missing security
  configuration, disk path and allowance; one-instance configuration; no secrets.

Preserve the 135-test baseline. Future verification commands: `uv sync --frozen`,
`.venv/bin/pytest -q`, `.venv/bin/ruff check .`,
`.venv/bin/ruff format --check .`, `uv pip check --python .venv/bin/python`,
`uv lock --check`, `uv build`, and `git diff --check`. Report exact outcomes and
runner limitations. Browser/hosted and paid checks require separate execution;
local fixture tests cannot substitute for them.

## Step 1 verification actually performed

- `git status --short`, `git branch --show-current`, `git log -3 --oneline`:
  clean initial working tree; local branch/commit recorded above.
- `git ls-remote origin refs/heads/main` plus read-only in-memory GitHub archive
  comparison: all 59 tracked paths and file bytes match merged main. No archive
  was extracted into the repository or used to overwrite working files.
- `pdftotext -layout` and `sha256sum` on the supplied PDF: section 12.10 reread,
  exact deliverables and source truncation recorded.
- Inline Python documentation review: exactly four new documentation files and
  the matrix addendum; links resolve, whitespace clean, no credential-shaped
  values, and report.openai.json matches the actual smoke harness filename.
- `.venv/bin/ruff check .`: all checks passed.
- `.venv/bin/ruff format --check .`: 57 files already formatted.
- `git diff --check`: passed; new untracked Markdown also checked for trailing
  whitespace and final newline separately.

No new automated tests were added. The full 135-test application suite was not
rerun for documentation-only work; its previous result is historical, not a
Step 1 result. No cost measurement, import, provider request, hosted login,
deployment or visual-browser test occurred. No commits or pushes were made.
