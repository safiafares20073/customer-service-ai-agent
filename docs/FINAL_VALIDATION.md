# Final capstone review candidate — November 4, 2026

Baseline: merged main a9bae01d0d8f8ba57b97185d56bf0f5846073626.
This work edits local source/tests/docs only. The Railway URL, operational Google
OIDC, real chat and approved global USD 3 budget are **owner-reported**, not
independently inspected private state. No live database, secret, invitation,
spending configuration, mounted volume or deployment was changed. No paid call
or new live trace was produced.

## Findings and justified corrections

1. A model can return a textual ticket proposal with finish_reason stop and no
   tool call. The existing loop accepts it as completed, so no Pending draft/form
   exists. That is distinct from MCP writing. System and safe tool descriptions
   now explicitly require a create_support_ticket proposal before asking for UI
   approval, explain that it pauses before any write, and specify omitted/null
   unknown order IDs and short valid idempotency keys. Wire contracts stay intact.
   The existing exact-draft trusted confirmation/write path is preserved.
2. Task-start rate denial was indistinguishable from a generic failure in the UI.
   A typed internal TaskRateLimit, retaining ACCESS_DENIED wire semantics, now maps
   to a localized wait message. Thresholds, principal counting and all budgets are
   unchanged. It is a plausible explanation after several demonstration questions,
   not a proven diagnosis of the live error without its private task records.
3. Invalid model arguments also reproduce a generic closed failure: blank optional
   order IDs and invalid idempotency keys are still rejected, not silently repaired.
   Tests cover this and a prose-proposal -> chat yes -> actual unconfirmed draft
   sequence. Text consent still creates no ticket. Actual hosted fault attribution
   remains pending; offline fixtures do not prove the real model now behaves correctly.
4. Assistant st.text displayed literal Markdown. It is replaced by redacted basic
   Markdown with unsafe_allow_html false, escaped HTML/brackets/price dollar signs,
   and omitted external links/media. User text remains st.text. Rendering helpers
   in two existing tests now include Markdown; their original assertions remain.
5. Existing RTL checks inspected CSS strings rather than the actual computed app
   root. Real Chromium found the root LTR despite right-aligned fields. Direction
   is now explicit on the application root, chat, labels, alerts, fields and controls;
   code/IDs isolate LTR. Responsive navy/teal/neutral styling, readable placeholders,
   focus outlines and white primary-button text improve the shared renderer.
6. Prompt grounding distinguishes catalog summaries from stock detail data, requires
   tool-based policy claims, and rejects inference of warranties/refunds/orders.
   Nine deterministic source-grounding samples read genuine MCP outputs for all
   three product prices/stocks, 14-day receipt policy and unknown-product refusal.
   These test plumbing and boundaries, not universal live hallucination resistance.

No agent replacement, extra tool, schema migration, model substitution, consent
bypass, paid retry policy or change to limits/authentication was introduced.

## Actual evidence and commands

The final command outputs and failed intermediate attempts are retained privately
in ignored artifacts/final-polish. They are test evidence, never submission JSONL.

- Focused hosted/UI rerun: 34 passed, 0 failed/skipped, 22.29 seconds. Earlier
  failures identified old st.text-only selectors and an escaped-redaction assertion;
  those were adapted without deleting or relaxing content/security assertions.
- Grounding suite: 9 passed, 0 failed/skipped, 5.82 seconds, actual MCP + explicitly
  scripted SDK HTTP transport. Hosted ticket tests include English/Arabic exact
  draft edit/confirm/cancel, SQLite persistence and create audit, stale revision,
  replay, same-task accounting, rate denial and malformed arguments.
- Full regression command: `.venv/bin/pytest -q --tb=short --junitxml=artifacts/final-polish/full-final.xml`.
  Final result: **283 passed, 0 failed, 0 skipped**, 95.99 seconds, one existing
  Authlib deprecation warning. All 258 baseline cases remain; two rendering
  collectors support the new component, preserving every content assertion.
- Real local Chromium 154.0.8037.57, loopback-only Streamlit and fixture provider:
  desktop 1280x960 and mobile-emulated 390x844. Bold rendered as a strong element;
  English computed LTR, Arabic app/input RTL/right; ticket fields RTL/right;
  no horizontal overflow; responsive Confirm/Cancel order, cancellation and white
  primary text on teal passed. Screenshots reviewed locally. This is real browser
  DOM/visual evidence for the shared renderer, not Railway/Google/live-model or
  physical-device certification. An initial missing selector/stale server cache and
  RTL/contrast observations are retained. The test server required restart because
  file watching was intentionally disabled.
- Spec is shortened without removing any of its six requirements, seven tools,
  exact limits, permissions or three examples. A4 print verification: **one page**, 11 pt Helvetica body, 15 mm margins,
  ReportLab/PdfReader text extraction confirms all six sections and seven names.
  The Chromium PDF attempt stalled and was stopped; it is not a claimed PDF pass.
  No execution evidence is inserted into the specification.
- Public `/healthz` read attempt: proxy CONNECT 403. No login or paid request was
  attempted. The reported deployed URL and Railway build remain attributed to
  the owner; no fresh hosted success or build receipt is invented.

## Remaining acceptance and recommendation

**GO for independent source/PR review. NO-GO for an unconditional final submission
claim until actual hosted ticket, professor access and reviewed-commit acceptance
are completed.** See [FINAL_DEMO_GUIDE.md](FINAL_DEMO_GUIDE.md).

The model can still ignore instructions and return prose. The original immediate
live generic error cannot be conclusively diagnosed from public code alone.
Private safe task outcome/audit review should distinguish invalid_tool_arguments,
provider/usage/budget/expiry and confirmation errors, plus task-start counts for
rate denial before a new task exists without exposing
private state or resetting allowances. Do not deploy this candidate automatically.

Current UI screenshots/test counts do not authenticate old provider exchanges,
verify invoices, guarantee current gpt-6-luna access/pricing, or prove universal
prompt-injection resistance. Original trace validation scopes and cost sample
limitations remain unchanged. The one-page render is a documented formatting
profile, not a claim every Markdown viewer prints identically.


## Final checks and preservation

- `pytest` full accepted run: **283 passed / 0 failed / 0 skipped**, 95.99 seconds.
  Includes all original 258 cases and 25 final regressions. No security test was
  removed. Nine new factual-source cases and sixteen hosted/rendering/rate/malformed
  argument cases are explicitly fixture-based with actual MCP.
- One original 100-ms timeout fixture was unstable: the task entered the provider
  at 7 ms but cold SDK serialization/dispatch outlasted that artificial window, so
  zero requests reached the mock handler. The initial 283-pass run and subsequent
  282-pass/1-fail runs/isolated diagnostics are retained. This test now uses a
  1-second test allowance against a 2-second fixture delay, still requires one
  request, time_limit and unknown usage, and adds explicit handler cancellation
  and elapsed-time upper-bound assertions. Production 60-second/10-second limits
  and all spending/turn limits are unchanged. Stabilized isolated test: 1 passed.
- Four Railway SDK configuration tests passed; native configuration unchanged.
  Deployment-only npm audit: zero known vulnerabilities, not a Python CVE audit.
- Ruff check/format passed; 63 installed Python packages compatible, frozen uv
  lock check resolved 66 packages, source distribution and wheel built offline.
  Temporary PDF tooling was installed outside the runtime environment/lockfile.
- Standard Docker checker passed with no warnings. Full Docker build was attempted
  and **failed due to the cloud intercepting proxy CA** at pip uv installation
  (SSLCertVerificationError), matching the previously documented environment limit.
  TLS remains verified; Dockerfile and lockfiles unchanged. No fresh local image
  success is claimed. Railway operation/build remains attributed to the owner,
  without a newly obtained build log or access to deployed secrets.
- Actual local Chromium screenshots were inspected. The final mobile check used
  a real pointer click and confirmed Cancel is unobscured/responds at 390x844;
  desktop 1280x960 and mobile English/Arabic have no horizontal overflow. This
  does not prove real-phone, hosted, Google-login or live-provider correctness.
- GitHub repository HTML: HTTP 200 with Public label on November 4. This records
  GitHub's label, not a multi-network anonymous availability certification.
- File inventory, relative links, whitespace, credential-pattern review and exact
  baseline comparisons exclude databases, bundles, attempt locks, raw traces,
  screenshots, private IDs and generated artifacts from publication. All three
  official trace byte hashes and cost_analysis.md remain unchanged.

Trace SHA-256 values:

| Trace | SHA-256 |
| --- | --- |
| success_1.jsonl | 5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb |
| near_failure_recovery.jsonl | 55e903d6b3726a5d13d68091a77ac6cee92de0bc99a7a8c57f947de359e6a841 |
| explicit_failure.jsonl | a8bd7b17b4c7d2adb2810d28ba60622109b0b2be02a639e750713ea2abe0fbe6 |

The remaining operator/assessor steps are documented, not executed. Reviewing a
PR does not alter the approved USD 3, authorize deployment, or approve new paid
calls. Existing live data/configuration/keys/records were not accessed or modified.
