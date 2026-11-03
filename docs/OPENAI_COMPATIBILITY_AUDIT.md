# Focused OpenAI compatibility and pricing audit

Audit date: **2026-11-03 (Asia/Aden)**. Scope: Phase 3 only.
Status: confirmed request/pricing errors corrected; SDK-fixture verification
completed as recorded below. **Actual live account/inference/billing remain unverified.**

## Sources and provenance

Authoritative URLs supplied by the user:

- <https://developers.openai.com/api/docs/models/gpt-6-luna>
- <https://developers.openai.com/api/docs/pricing>
- <https://developers.openai.com/api/docs/guides/latest-model>

Read-only requests to the first two URLs were blocked by the environment proxy
with `CONNECT tunnel failed, response 403` (no origin HTTP response; curl HTTP 000).
No alternate route was used to bypass policy. The user subsequently provided an
explicitly verified official excerpt dated November 3, 2026. Model support and
prices below rely on that excerpt, not a claim of independent web retrieval.
The installed official OpenAI SDK 2.54.0 independently establishes generic request
serialization and usage-field semantics, not account/model availability.

## Findings and corrections

| Requested check | Audited result | Evidence / remaining limit |
| --- | --- | --- |
| Endpoint and function calling | gpt-6-luna supports both Responses and Chat Completions and supports function calling, per the user-verified excerpt. Retained the existing `/v1/chat/completions` path with seven MCP-discovered function tools, `strict=False`, `parallel_tool_calls=False`, and `n=1`. | Official SDK fixture asserts the exact path and parameters; actual model/account availability remains untested. |
| Reasoning effort | Confirmed error: the code omitted the setting, while the documented default is medium and Chat Completions function calling requires **none**. Production requests now explicitly send `reasoning_effort="none"`. Model-supported values from the excerpt are none, low, medium, high, xhigh, max; generic SDK support for minimal does not make it model-supported. | Every fixture request asserts none. Responses is recommended for reasoning with tools; this non-reasoning tool workflow needs no architectural rewrite. No Responses implementation or reasoning-with-tools capability is claimed. |
| Processing tier and prices | Confirmed error: the original 0.05 input / 0.25 output / 0.005 cached rates were Flex/Batch, mislabeled Standard. Requests already correctly selected `service_tier="default"`, which SDK documentation defines as Standard. Corrected snapshot: **0.10 input / 0.50 output / 0.01 cached input USD per million tokens**, dated November 3. | Decimal tests and durable pricing/cache records use the corrected rates. No Flex, Batch, Priority, or other-model price substitution occurs. |
| Reservations and token limits | Reservations use uncached input at 0.10/million and the entire <=512 completion-token allowance at 0.50/million, including any reasoning tokens. Reservations now double the previous incorrect rate calculation for the same token bounds. The USD 0.05 estimated task cap remains unchanged. | SDK docs define max_completion_tokens as including visible output and reasoning. A fixture verifies that 20 total completion tokens including 15 reasoning are charged as 20, not 35; this defensive synthetic response does not claim reasoning generation under none. Live tokenizer bounds/context behavior/billing remain unverified. |
| Fixture provenance | Fixtures assert `fixture.invalid`, exact Chat Completions path, none effort, Standard tier, no storage, no parallel calls, and the <=512 limit. Their tokens and calculated costs are explicitly synthetic. | Traces/records remain fixture/provider_fixture. Passing fixtures are not successful live OpenAI calls or billing verification. No official submission traces were generated. |

## Budget, time, and resumption integrity

Cached discounts apply only to reported cached input; absent cache details remain
null. Reservations do not assume a cache hit. Token-based computed costs are not
provider invoices. If reported usage violates a conservative bound, it is recorded
truthfully and further requests stop; already-incurred charges cannot be undone.
The input-token bound remains an engineering estimate awaiting live verification.

The updated pricing date uses its explicitly recorded **Asia/Aden** verification
timezone. This fixes a confirmed calendar-boundary issue: on this machine UTC
still read November 2 while Asia/Aden read November 3. The loader checks age in
the declared zone without disabling future-date or 30-day freshness validation.
A deterministic timezone test verifies both the valid local date and rejection
of an actually future date in the declared zone.

Changing the dated pricing snapshot changes its version hash. A pending task
bound to the old price version fails closed on resumption: no silent repricing,
new budget, extra model call, or ticket write. A regression test verifies that
behavior. Existing fixture histories were not rewritten, and there is no real
paid history to repair. Start a fresh explicitly requested task under the corrected
snapshot; do not relabel an old fixture record as live or current pricing.

The model remains configurable, with no fallback. Any alternative model requires
its own verified prices and request compatibility review. The fixed none setting
is the documented gpt-6-luna Chat Completions tool mode, not a claim that every
other model accepts it.

## Files changed by this focused audit

- `agent/provider.py`: explicit reasoning_effort none.
- `agent/pricing.py`: verification-date timezone handling.
- `config/model_pricing.json`: corrected Standard rates/date, source URLs,
  verification timezone, and documented-compatibility provenance.
- Shared provider fixture and affected price/cache tests: request assertions,
  corrected arithmetic/date expectations, reasoning-total accounting, conservative
  Standard reservations, timezone boundaries, and safe old-price resumption.
- README, Phase 3 documentation, and requirements matrix: corrected assumptions,
  evidence, and live-validation limits. No MCP tool/schema or database-schema change.

## Verification and limits

Completed against the corrected configuration:

- `.venv/bin/pytest tests/agent/test_pricing_and_guards.py tests/agent/test_workflows.py tests/agent/test_limits.py -q`: **57 passed, 0 failed, 0 skipped**, 17.70 seconds.
- `.venv/bin/pytest -q --junitxml=/tmp/phase3-audit-full.xml`: **106 passed, 0 failed, 0 skipped**, 52.45 seconds; 60 Phase 3 tests plus all 46 original Phase 2 tests.
- Ruff lint/format, dependency compatibility, frozen lock consistency, Git whitespace checks, and the safe CLI preflight passed.

A preliminary 103-test pass before the corrections is not the final corrected-configuration result. All original Phase 2 tests remain intact. Fixture tests use genuine MCP
stdio sessions and the official OpenAI SDK with a local HTTP fixture transport.

No paid API request was made. Credentials are not configured. No live capability,
account access, tokenizer measurement, invoice, billed average cost, public URL,
Responses migration, or deployment is claimed. No commit, push, merge, publication,
or Phase 4 work was performed. Stop for review.
