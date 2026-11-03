# Phase 3: one OpenAI SDK agent over genuine MCP

Status: implementation and deterministic-provider validation; **live OpenAI
validation is pending**. No paid API request, Streamlit UI, deployment, multi-agent
work, Phase 4 hostile-input exercise, or Git publication was performed.

## Reproduce without paid requests

From the repository root, Python 3.12.14 and uv 0.12.23:

```sh
uv sync --frozen
.venv/bin/customer-service-agent --preflight
.venv/bin/pytest -q --junitxml=/tmp/phase3-all-results.xml
.venv/bin/ruff check .
.venv/bin/ruff format --check .
uv pip check --python .venv/bin/python
uv lock --check --offline
uv build --offline
git diff --check
```

In this cloud environment, uv needs `--cache-dir /tmp/phase3-uv-cache` because
the default cache is read-only. Offline build/lock checks require a populated
cache. Tests use official OpenAI SDK 2.54.0 with `httpx.MockTransport`, a dummy
non-credential SDK fixture key, and `fixture.invalid` endpoints. MCP uses official
SDK 1.30.0 stdio subprocesses throughout. No fixture response or usage count is
represented as an actual OpenAI inference, tokenizer measurement, or billed cost.
Other Python versions are declared supported but have not been validated here.

## Model and pricing provenance

Provisional configurable model: **gpt-6-luna**. The user supplied the following
corrected official Standard pricing excerpt dated **2026-11-03 (Asia/Aden)**, citing
<https://developers.openai.com/api/docs/pricing>:

| Standard category | USD per million tokens |
| --- | --- |
| Input | 0.10 |
| Output | 0.50 |
| Cached input | 0.01 |

Independent retrieval returned HTTP 403 under the environment policy. The JSON
snapshot explicitly records `user_supplied_official_excerpt`, its date and tier,
and documented compatibility via the corrected user excerpt; actual live
compatibility/account availability remain unverified. This is not a claim of
independent price verification. No price applies to a different model or tier.
There is no fallback model. Requests specify `service_tier="default"`, `store=False`,
one completion, no parallel tool calling, at most 512 completion tokens, and
explicit `reasoning_effort="none"`. The user-verified model excerpt documents
Chat Completions and function-calling support with that setting; live execution
and account availability remain untested. Responses is recommended for reasoning
with tools, but no reasoning-with-tools migration is required for this workflow.

The [focused compatibility audit](OPENAI_COMPATIBILITY_AUDIT.md) corrected the
original Flex/Batch rates that had been mislabeled as Standard and the omitted
reasoning_effort (the documented medium default is unsuitable for this Chat
Completions function-calling mode). Independent source retrieval remains blocked;
the user verified the model/pricing/latest-model sources on November 3. The SDK
defines the completion cap as including reasoning tokens; reported reasoning
counts are not added a second time to completion-token costs.

`OPENAI_MODEL` configures the model; `MODEL_PRICING_FILE` selects its dated snapshot.
Missing/mismatched/invalid pricing, a non-Standard tier, or a date outside the
30-day review window fails closed. Calendar age uses the snapshot
verification timezone (Asia/Aden), retaining future-date rejection. After that window, a trusted operator must
reverify pricing. Different models require their own verified snapshot. Unexpected
response model IDs or non-default tiers stop accounting as unknown, rather than
silently applying the configured model's prices. Snapshot-style model IDs may
therefore require explicit matching configuration and reverified pricing.

Live credentials are read from `OPENAI_API_KEY` or `LLM_API_KEY`, never source code
or model arguments. No credentials are currently configured. They must be entered
through secure environment settings, not chat. The CLI requires deliberate
`--allow-paid` use after separate operator approval. That flag was not used here.
Neither the agent nor the MCP server automatically loads `.env`.

## Single-agent execution and limits

`agent/provider.py` uses the official `AsyncOpenAI.chat.completions.create` API.
`agent/loop.py` discovers the seven safe schemas with the existing MCP adapter,
passes them to that one model, validates returned function arguments, and routes
every tool invocation through `TrustedClient.invoke`. No agent code calls a
customer-service store handler directly. No identity or confirmation tool exists.

At most eight SDK requests are allowed per task; each reservation consumes a
turn before the request. `max_retries=0` prevents uncounted SDK retries. This
implementation intentionally performs no automatic provider retries: errors can
leave usage/billing uncertain, and the approved policy stops on unknown usage.
Final text with no pending calls ends the loop. Empty, malformed, truncated,
unauthorized, or otherwise unrecoverable responses stop safely. Deterministic
limit/error replies require no extra LLM call. Limit replies include the last
verified result where available, after checking the session is still authorized.

The per-task USD 0.05 cap is enforced on conservative pre-request reservations.
Input reservation uses twice the UTF-8 bytes of serialized messages/tools plus
4096 framing tokens; output reservation uses the configured maximum (<=512).
Requests over 64 KB of serialized input are refused. Reservations assume uncached
input. This is an engineering upper estimate, not a live-validated tokenizer
bound or a provider-enforced invoice cap. The latest Phase 3 request explicitly
specifies an estimated cap; the original specification's unconditional “hard
limit” wording was clarified accordingly, rather than claiming impossible control
over already-incurred external charges.

Responses reconcile reservations against actual reported input/output tokens
and reported cached tokens where available. Missing cached details remain null
and receive no discount. Decimal arithmetic avoids float rounding. Input/output
usage and computed USD go into `cost_records`; namespaced metadata retains each
pricing snapshot, original reservation, cache count, and usage provenance. These
are token-based computed costs, not invoices. Provider fixtures are recorded as
`provider=fixture`, including their deliberately synthetic usage counts.

If usage is absent/invalid, transport fails, or a request times out, cost becomes
unknown (`cost_usd=NULL`), the reservation remains held, and no further request
is made. Unknown pricing causes no request and no invented zero-usage row.
If reported usage exceeds its bound, record the actual reported usage/cost and
stop; do not hide the overrun by clamping records. This limit check is tested with
an intentionally oversized fixture response, not a paid over-budget execution.

Active work has a 60-second cumulative deadline. Every tool operation has a
10-second deadline (tests can lower but cannot increase limits). Human confirmation
waits are excluded; subsequent active work accumulates on the same saved counter.
Cancellation stops new work, but an already-running MCP write may still finish;
timeouts never claim that a ticket definitely was or was not created. Transport
teardown can follow the active-work deadline. Idempotency prevents duplicate
writes; the loop does not retry an ambiguous write automatically.

## Persistence and trusted confirmation

The Phase 2 database schema remains version 2 without ALTER statements, extra
tables, or changed tool contracts. `agent/state.py` uses existing `tasks`,
`cost_records`, `memory`, and `audits`, plus `metadata` keys `agent_task:<id>` and
`agent_cost:<record-id>`. SQLite transactions persist counters/reservations before
external requests. A persisted running flag prevents concurrent task execution.
A process crash mid-request remains locked/incomplete rather than automatically
retrying with a fresh budget; automatic crash recovery is not implemented.

Agent tasks require the existing trusted synthetic session capability. One
explicit customer request is bound to each provisioned session/task; a new
conversation uses a new trusted session for the same synthetic customer. The
model cannot create sessions or select identities. Memory is loaded by authenticated
principal and labeled untrusted context. Completed request/answer snippets are
bounded and redacted before storage; no cross-customer lookup is exposed. This
phase does not implement a general semantic memory extractor or retention policy.

When the model proposes `create_support_ticket`, the agent pauses **before**
registering consent or writing. The exact validated draft is returned to trusted
console/UI code. `Agent.resume(task_id, confirmed=True)` is a trusted human-input
API, never a tool or an interpretation of model text. CLI confirmation displays
subject, message, and optional order ID before requiring `CONFIRM`. Declining
revokes consent and ends the task. Future UI code must still revoke consent on edits.

Resumption loads the same task ID, session binding, transcript, pending calls,
turns, cost, elapsed time, and original limits/pricing. A fresh controller cannot
raise those limits. On process restart, raw access/confirmation references are
not restored from disk: linked-order access is reverified through MCP and consent
is registered through the existing trusted local API. For external process
resumption, a trusted launcher must retain the original session capability and
inject `CS_SESSION_TOKEN` on the initial launch and resumption, omitting
`--customer` because identity is already bound. The CLI reuses that binding and
rejects an attempt to select a different customer. It never prints or writes the
capability to a file. A CLI-minted capability is held only in that process; external
recovery requires a launcher that retained the binding before the initial run.
An expired/foreign session is denied. Accounting and cleanup for a request already
issued may finish after expiry, without enabling another request or private answer.

## Tracing, audit, and timeout cleanup

JSONL defaults to ignored `artifacts/phase3/<task-id>.<provider>.jsonl` with private
file permissions. Events contain only allowlisted generated IDs, UTC timestamps,
provider/evidence labels, tool names, outcomes, counters, reported tokens, and
costs/reservations. Raw prompts, answers, tool arguments/results, customer identity,
SDK error text, keys, and security references are excluded. Missing cache usage
is omitted rather than recorded as a fake zero. This trades transcript detail for
safe evidence; private bounded conversation state remains in the local database.

Fixture files say `provider_fixture` explicitly and cannot be written under a
submission `traces/` directory. No official LMS trace was generated. Live evidence
and the three named submission traces remain pending actual approved executions.
Completed status means the model supplied a final answer; fixture tests establish
orchestration, not independent proof that a live model's answer is factually sound.

The first Phase 3 agent-suite run found a late-response shutdown race in SDK 1.30
after a genuine delayed MCP call timed out. `tool_server/client.py` now gives the
session cloned streams and drains late transport messages only during shutdown,
before closing the subprocess. This neither fabricates a tool result nor changes
authorization. The original timeout test passed after the fix. All Phase 2 tests
remain unchanged. The delayed-server fixture uses the same FastMCP server and
real catalog handler, with an explicit delay; no mock MCP transport is involved.

## Verification and remaining work

The five official functional scenarios execute against deterministic SDK-provider
fixtures: product listing; search plus policy; product details; authorized order
status; and a support ticket confirmed by trusted test code. Process tests exit
and restart actual agent and MCP processes, proving scoped memory recall and
confirmation-state persistence. Live validation of those five scenarios remains
pending; fixture outputs/usage do not prove model capability or availability.

Actual final commands/counts are recorded in the requirements matrix. No coverage
percentage, live trace, model-quality score, billed average cost, public URL, or
deployment result is claimed. Phase 4's three hostile prompt-injection exercises,
Streamlit UI, production authentication, deployment, and final cost analysis remain
outside this phase. Stop for review; no commit/push/publish/merge is authorized.
