# One prepared live smoke test — NOT EXECUTED

Status: prepared only. Fixture rehearsals are not live OpenAI runs. Do not run
the paid command below until the user explicitly approves this specific test.
Preparation is not approval, and adding credentials is not approval.

## Exact task and controls

Question: **Find headphones under $30 and explain the return policy.**

The dedicated runner calls the existing `Agent.start` once, with a fresh synthetic
SQLite database, synthetic demo-a session, real initialized MCP subprocess, and
the existing seven tools. It does not replace the loop or call product/policy
handlers directly. It never grants ticket consent or resumes a proposed write.

OpenAI configuration: gpt-6-luna, `/v1/chat/completions`, explicit
`reasoning_effort="none"`, `service_tier="default"` (Standard), no storage, no
parallel tool calls, SDK retries disabled, maximum 512 completion tokens/request.
Current verified-by-user snapshot: November 3, 2026 Asia/Aden; USD/million input
0.10, output 0.50, cached input 0.01. No fallback model/rates/tier.

This is **one agent task**, not one HTTP request. Genuine tool calling typically
needs two or three LLM requests, and the agent may use up to eight. Existing
limits remain: USD 0.05 conservative estimated task cost, 60 cumulative active
seconds, 10 seconds/tool. No additional paid LLM judge or verification request.
Actual billed cost and the tokenizer reservation bound remain unverified.

## Preparation and safe preflight (no paid calls)

From the repository root:

```sh
uv sync --frozen
.venv/bin/python -m yemen_customer_service.agent.smoke --preflight
```

The preflight loads the dated pricing configuration, prints only credential
presence, and creates no database, trace, attempt marker, or API client/request.
The pricing freshness window still applies; re-review prices if it expires.

For this cloud environment, `api.openai.com` must be allowed through the supported
network settings, and an appropriate project key must be securely configured.
Do not bypass the proxy. Existing network policy did not allow that hostname at
preparation time; model/account access is not verified. Package downloads for
`uv sync` are separate from paid model execution. Use the documented writable
uv cache if needed (`--cache-dir /tmp/phase3-uv-cache`).

## Secure key setup and exact future execution command

Never send the key in chat, place its value in a command/history, print the process
environment, use shell tracing, or add a key to tracked files.

**Managed environment option:** configure `LLM_API_KEY` securely in environment
settings, scoped to `api.openai.com` if proxy credential injection is used. The
SDK also accepts `OPENAI_API_KEY` in environments that support that name. Reuse an
existing valid binding rather than extracting or printing it. Ensure
`OPENAI_MODEL=gpt-6-luna`, `APP_ENV=development`, and
`MODEL_PRICING_FILE=config/model_pricing.json`. Do not run the command yet.

Exact command, **only after explicit paid-run approval**:

```sh
.venv/bin/python -m yemen_customer_service.agent.smoke --allow-paid --enable-demo-auth
```

**Local Bash option:** if no secure injected binding exists, after approval only,
use a subshell and hidden prompt so the value is not in shell history or echoed:

```bash
(
  set +x
  unset OPENAI_API_KEY OPENAI_LOG
  IFS= read -r -s -p 'OpenAI project API key (hidden): ' LLM_API_KEY
  printf '\n'
  test -n "$LLM_API_KEY" || exit 1
  export LLM_API_KEY
  export OPENAI_MODEL=gpt-6-luna APP_ENV=development
  export MODEL_PRICING_FILE=config/model_pricing.json
  trap 'unset LLM_API_KEY OPENAI_API_KEY' EXIT
  .venv/bin/python -m yemen_customer_service.agent.smoke --allow-paid --enable-demo-auth
)
```

This block has **not** been executed. Do not use it to copy a proxy placeholder
or extract an existing injected secret. The runner disables standard SDK/HTTP
logging and removes key variables from its own environment after constructing
the SDK client, without printing the values. The client closes on exit. The key
is never part of the model question, MCP arguments, report, or JSONL events.

## Offline checks and review after the single attempt

The runner writes private, ignored artifacts under `artifacts/live_smoke/`:

- `attempt.lock`: atomic persistent one-shot interlock, claimed before execution.
- `synthetic.sqlite3`: fresh synthetic fixtures and the agent's task/usage records.
- `events/<task-id>.openai.jsonl`: existing redacted metadata trace.
- `report.openai.json`: task status, safe synthetic answer, successful audited MCP
  tool names, facts returned by MCP, usage, recalculated USD, and check outcomes.

The verifier checks successful MCP audit records against the saved tool-result
transcript, confirms a returned headphones product under USD 30 and a returns
policy, checks product/price/14-day/original-receipt answer anchors, recomputes USD
from recorded input/output/cached tokens and the Standard snapshot, and checks
turn/time/cost limits. Missing usage remains unknown/null, never a fabricated zero.
Any non-completed task, missing evidence, unexpected private tool, or failed
check results in a nonzero CLI exit. Unexpected ticket proposals are not confirmed.

**Human review is still required:** compare the complete answer with the returned
product and policy facts in the report. Lexical anchors cannot prove every claim
is supported or catch every contradiction; valid paraphrases can also miss a
lexical anchor and require review. `automated_checks_passed=true` is not
a certificate of complete factual grounding or a verified provider invoice.
If the answer is wrong, mark the smoke test failed; do not automatically rerun it.

## Disable further calls

- Keep `attempt.lock`: the dedicated runner refuses a second attempt even after
  failure. It never deletes that marker or retries a paid task automatically.
- Do not run another command with `--allow-paid`. That flag applies only to the
  current process; no daemon or recurring paid job is started.
- For a shell-exported key, run `unset OPENAI_API_KEY LLM_API_KEY` in the parent
  shell too if it already held those variables. Subshell-local setup disappears
  at exit. Unsetting variables does not cancel a request already sent.
- For a managed injected secret, remove/disable its binding in environment settings
  to stop future processes from receiving it. For provider-side enforcement,
  revoke the dedicated test key in the OpenAI project. A local marker does not
  revoke a key or prevent different programs/accounts from using it.
- Do not delete/reset the interlock or repeat the test without a new explicit
  review/approval. Retain the report and unknown-cost records for diagnosis.

No live success, actual provider token counts, or billed USD are claimed during
preparation. Fixture rehearsals are labeled provider_fixture and use real MCP.


## Preparation verification

The seven harness tests passed using provider fixtures and real MCP: safe
preflight, persistent interlock, existing-file preservation, correct/incorrect
answer checks, missing usage, and refusal to confirm an unexpected ticket.
No live command, actual OpenAI usage, or billed amount is included in those results.
The first rehearsal exposed a price-anchor punctuation bug (USD 25 followed by a
sentence period); it was corrected without weakening the incorrect-price test.
Full regression: **113 passed, 0 failed, 0 skipped** in 55.28 seconds. Targeted
harness rehearsal: **7 passed, 0 failed, 0 skipped** in 2.68 seconds. All OpenAI
responses in these counts are fixtures; no live command was run. Lint, formatting,
and whitespace checks passed.
