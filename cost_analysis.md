# Recorded usage and estimated cost analysis

Analysis date: **November 4, 2026 (Asia/Aden)**. Evidence baseline: merged main
`ff2c32f5b8c95d25c66d4212ec41a69b96dd2029`.
Sample size: **n=3 attempted customer tasks**, including the explicit-failure task.
No model requests were made to produce this analysis. Original traces are unchanged.

**Total recorded usage-derived cost: USD 0.0006260. Observed three-task average:
approximately USD 0.000208666667 per task. Provider billing is unverified.**

## Evidence and pricing

The three reviewed JSONL files contain execution records labeled `live_openai`.
They provide usage counts, reservations, task counters and terminal outcomes.
This analysis independently parses all six `usage` events and recomputes their
costs, then checks them against the recorded per-call and terminal totals.
No provider-fixture tests contribute to this sample or its token/cost totals.

Model: **gpt-6-luna**. Processing mode: **Standard**, requested `service_tier=default`
through Chat Completions with `reasoning_effort=none`, as documented by the
reviewed execution reports and [compatibility audit](docs/OPENAI_COMPATIBILITY_AUDIT.md).
The metadata-only traces do not themselves record every request parameter.

Historical pricing date: **November 3, 2026 (Asia/Aden)**. Rates are taken from the
dated user-verified official excerpt recorded in
[config/model_pricing.json](config/model_pricing.json), and agree with the reviewed
evidence reports. Price source: <https://developers.openai.com/api/docs/pricing>;
model source: <https://developers.openai.com/api/docs/models/gpt-6-luna>.
The analysis does not independently retrieve current prices or verify an account.
These rates apply only to the documented model/Standard mode, not other models,
Flex, Batch, Priority or hypothetical future prices.

| Token category | Historical USD per 1 million tokens |
| --- | ---: |
| Uncached input | 0.10 |
| Cached input | 0.01 |
| Output | 0.50 |

## Formula and counting rules

For each model request, let I be total input tokens, C the reported cached subset
of input, and O total output tokens. All six records explicitly report C=0.

```text
estimated_USD_per_request = ((I - C) * 0.10 + C * 0.01 + O * 0.50) / 1,000,000
estimated_USD_per_task = sum(estimated_USD_per_request for that task)
observed_average_USD_per_task = sum(task costs) / 3
projected_monthly_USD = monthly_task_count * observed_average_USD_per_task
```

Cached tokens are already included in I. Any reasoning-token subset is already
included in O and must not be added again. Missing usage/cache data would need
explicit uncertainty handling; no missing field was silently treated as zero here.
All calculations use Decimal arithmetic, with exact finite per-request/task
totals. The exact average is the fraction **313/1,500,000 USD/task**; its decimal
expansion repeats. The displayed mean is rounded to 12 decimal places. Monthly
projections use the unrounded fraction and are rounded to 8 decimal places with
round-half-up. Rounding is presentation only, not a provider billing rule.

Count model requests using the `usage` events, corroborated by `reserved` events
and final `turns`. Do not add reservation estimates or `finished.cost_usd` to the
usage sums: those are pre-call allowances and task totals, respectively. A MCP
retry control event is not another model request. MCP runs locally; no separate
provider tool fee is recorded for these Python tools. Infrastructure is excluded.

## Per-scenario results

| Scenario / trace | Recorded outcome | Model requests | Input tokens | Output tokens | Cached input tokens | Estimated USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| [success_1](traces/success_1.jsonl) | completed | 3 | 2,789 | 82 | 0 | 0.0003199 |
| [near_failure_recovery](traces/near_failure_recovery.jsonl) | completed | 2 | 1,861 | 53 | 0 | 0.0002126 |
| [explicit_failure](traces/explicit_failure.jsonl) | turn_limit | 1 | 850 | 17 | 0 | 0.0000935 |
| **Total (n=3 tasks)** | 2 completed; 1 terminal incomplete | **6** | **5,500** | **152** | **0** | **0.0006260** |

Request-level cross-checks:

| Trace | Request | Input | Output | Cached input | Recomputed USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| success_1 | 1 | 845 | 22 | 0 | 0.0000955 |
| success_1 | 2 | 935 | 19 | 0 | 0.0001030 |
| success_1 | 3 | 1,009 | 41 | 0 | 0.0001214 |
| near_failure_recovery | 1 | 850 | 17 | 0 | 0.0000935 |
| near_failure_recovery | 2 | 1,011 | 36 | 0 | 0.0001191 |
| explicit_failure | 1 | 850 | 17 | 0 | 0.0000935 |

The recovery case uses a disclosed SQLite read fault and one bounded adapter
retry within the same task. It demonstrates controlled harness recovery, not
model-led repair. The explicit-failure case deliberately permits one model
request: a catalog read succeeds, then `turn_limit` stops the task without another
model request for a final answer. Its recorded usage still has a nonzero estimated
cost. **That USD 0.0000935 and that attempted task are included in the n=3 average.**
The denominator is all three attempted tasks, not just the two completed outcomes.

## Explicit monthly projection

Assume unchanged historical rates and exactly the same average usage/task and
scenario mix: one-third product/policy successes, one-third controlled recoveries,
one-third deliberately limited failures. With two observed model requests/task
on average, the projections are:

| Tasks per month | Expected model requests | Projected model-token cost (USD/month) |
| ---: | ---: | ---: |
| 100 | 200 | 0.02086667 |
| 1,000 | 2,000 | 0.20866667 |
| 10,000 | 20,000 | 2.08666667 |

These are linear expectations; 100 and 1,000 tasks cannot divide exactly into
three integer scenario counts. No extra billable requests, unknown-cost failures,
unrecorded attempts or longer conversations are assumed. This observed average
is well below the USD 0.05 estimated task cap, but neither a cap nor the USD 0.10
two-scenario run allowance is an average or a predicted invoice. As a separate
capacity comparison, N tasks each consuming the entire USD 0.05 estimated cap
would imply USD 5, 50 or 500 at the three volumes, before infrastructure and
possible provider usage outside conservative bounds. Those are cap-based planning
figures, not the observed-workload projection above or a guaranteed billing ceiling.

## Assumptions and limitations

- Three selected synthetic-store demonstrations are a very small, nonrandom
  sample. Two cases were controlled exercises. The one-third failure frequency
  is a sample design choice, not an observed production failure rate. Do not
  interpret the projection as a statistically reliable traffic forecast.
- Short English catalog/policy tasks do not establish costs for Arabic requests,
  private order workflows, ticket approvals/resumption, larger catalogs, longer
  histories or other output lengths. Growing persistent memory can increase input
  tokens. Different traffic mix, model behavior, cache hits or prices change cost.
- SDK retries are disabled, and the controlled read retry itself incurs no extra
  LLM call. Other paid attempts outside these three trace records are not counted.
  Incomplete/missing usage in other runs cannot be inferred from this sample.
- **Recorded API usage estimates are not independently verified provider billing.**
  The records and reports are user-supplied, reviewed execution evidence. Hashes
  establish byte integrity, not authenticity of the provider exchange. No invoice,
  provider-side usage export, independently authenticated request receipt or billed
  amount was reconciled in this analysis. No current model availability is claimed.
- The success bundle had private SQLite checks in this workspace. Private SQLite,
  audit, plan and no-write checks for recovery/failure are attributed to their
  independent reviewers; this analysis rereads public traces and reports only.
  Their historical pricing rates agree with the documented snapshot, but absent
  original private snapshots/request parameters are not newly authenticated.
- Hosting, persistent disks, backups, OIDC/authentication, bandwidth, monitoring,
  taxes, credits, currency conversion, minimum charges and provider invoice-rounding
  rules are excluded. No Render/Railway infrastructure price is invented. A final
  hosted total needs actual plan selection and measured infrastructure costs.
- A USD 0.05 conservative estimated/task gate helps bound requests. Reported
  provider usage outside the engineering reservation can already have incurred
  charges; further calls stop, but charges cannot be undone. This is not an
  assurance about a provider's invoice ceiling.

## Evidence integrity and reproducibility

| Official trace | Original/reviewed SHA-256 |
| --- | --- |
| success_1.jsonl | `5be36011fe156260ec967cdcd221f0a8c0f4e8786321f9ca257e4902bd9e19cb` |
| near_failure_recovery.jsonl | `55e903d6b3726a5d13d68091a77ac6cee92de0bc99a7a8c57f947de359e6a841` |
| explicit_failure.jsonl | `a8bd7b17b4c7d2adb2810d28ba60622109b0b2be02a639e750713ea2abe0fbe6` |

See the [success](docs/SUCCESS_EVIDENCE_VALIDATION.md),
[recovery](docs/RECOVERY_EVIDENCE_VALIDATION.md) and
[explicit-failure](docs/EXPLICIT_FAILURE_EVIDENCE_VALIDATION.md) validation reports.
The following standalone Python command is offline, uses no application/provider
code, and independently recomputes the usage costs from the frozen trace files:

```sh
python - <<'PY'
import json
from decimal import Decimal, getcontext, ROUND_HALF_UP
from pathlib import Path

getcontext().prec = 50
prices = json.loads(Path("config/model_pricing.json").read_text())
rates = [Decimal(prices[k]) for k in (
    "input_usd_per_million", "cached_input_usd_per_million", "output_usd_per_million")]
total = Decimal(0)
tasks = requests = input_tokens = output_tokens = cached_tokens = 0
for path in sorted(Path("traces").glob("*.jsonl")):
    events = [json.loads(line) for line in path.read_text().splitlines()]
    usage = [e for e in events if e["event"] == "usage"]
    subtotal = Decimal(0)
    for u in usage:
        i, o, c = (u[k] for k in ("input_tokens", "output_tokens", "cached_input_tokens"))
        cost = ((i - c) * rates[0] + c * rates[1] + o * rates[2]) / Decimal(1_000_000)
        assert cost == Decimal(u["cost_usd"])
        subtotal += cost
        input_tokens += i
        output_tokens += o
        cached_tokens += c
    assert subtotal == Decimal(events[-1]["cost_usd"])
    assert len(usage) == events[-1]["turns"]
    print(path.name, len(usage), subtotal)
    tasks += 1
    requests += len(usage)
    total += subtotal
assert (tasks, requests, input_tokens, output_tokens, cached_tokens) == (3, 6, 5500, 152, 0)
print("tasks, requests, input, output, cached:", tasks, requests, input_tokens, output_tokens, cached_tokens)
print("total:", total, "average:", total / tasks)
for n in (100, 1000, 10000):
    projected = (total * n / tasks).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    print(n, projected)
PY
```

If rates or traces are intentionally changed in future work, this document must
be recomputed and versioned rather than silently presenting changed numbers as
the original sample. The current three reviewed traces have not been modified.


## Executed offline verification

- `.venv/bin/python /tmp/validate_cost_analysis.py`: **10 passed, 0 failed,
  0 skipped**. Independent Fraction arithmetic checks Decimal results, all
  scenario/request rows, the failure-inclusive n=3 denominator, rounding,
  monthly projections, trace hashes, README values and the reproduction command.
- `.venv/bin/python /tmp/validate_explicit_failure_import.py`: **11 passed,
  0 failed, 0 skipped**, including all three original hashes and recorded totals.
- `PHASE4_EVIDENCE_DIR=artifacts/cost-analysis-validation/security TRACE_SCENARIO_EVIDENCE=artifacts/cost-analysis-validation/scenarios LIVE_RUNNER_TEST_EVIDENCE=artifacts/cost-analysis-validation/cases .venv/bin/pytest -q --tb=short --junitxml=artifacts/cost-analysis-validation/full-suite.xml`:
  **187 passed, 0 failed, 0 skipped**, 84.33 seconds. These regressions use
  provider fixtures and genuine MCP; their synthetic usage is excluded above.
- `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`: passed.
- `uv pip check --python .venv/bin/python --cache-dir /tmp/cost-analysis-uv-cache`:
  61 installed packages compatible.
- `uv lock --check --offline --cache-dir /tmp/cost-analysis-uv-cache`: passed,
  64 resolved packages.
- `uv build --offline --cache-dir /tmp/phase4-uv-cache`: source distribution and
  wheel built successfully. Generated artifacts remain ignored.
- `git diff --check`, Markdown links, new-file whitespace, credential-pattern and
  exact file-inventory checks passed. Only this document, README, requirements
  matrix and final checklist change. All production code, tests, dependencies,
  configuration and original three traces remain byte-identical to the baseline.

Private validation scripts/results are retained in ignored
artifacts/cost-analysis-validation/. No new provider execution, credential request,
deployment or automatic merge occurs. This document is ready for GitHub review;
public hosting and final submission still require their separate acceptance gates.
