# Requirements matrix

Source reviewed: supplied `Week5_Capstone_Official_Chapter12_10.pdf`, §12.10,
printed pp. 578–581. Page citations refer to printed book pages. Requirements
below are paraphrased from that excerpt, not inferred from adjacent sections.
The final cost-analysis bullet is truncated at “monthly project” in the supplied
excerpt; a monthly cost projection is the documented interpretation.

Only Phase 1 documentation/scaffold is present. “Documented” means source review
or document content, never implemented or tested application functionality.

## Official requirements and submission evidence

| Official item | Source | Implementation / evidence location | Current verification status |
| --- | --- | --- | --- |
| Solve a real task end-to-end, public URL, cost tracking | Goal, p. 578 | Agent, deployment, tracker; plan Phases 2–5 | Planned; no runtime evidence |
| Choose one of eight domains | Day 1, pp. 578–579 | Customer service, `agent_spec.md` §1 | Documented: listed domain selected |
| One-page `agent_spec.md` | Day 1, p. 579 | Concise six-section `agent_spec.md`; detailed contracts moved to supporting design | Verified: temporary A4 PDF is one page at 10pt, 12pt leading, 36pt margins; other renderers may paginate differently |
| Goal in one sentence | Day 1, p. 579 | `agent_spec.md` §1 | Documented |
| 5–10 allowed tools | Day 1, p. 579 | `agent_spec.md` §2 | Documented: seven |
| Termination: max_turns + budget + final_answer | Day 1, p. 579 | `agent_spec.md` §3 | Documented; runtime enforcement pending |
| Budget cap in USD/task | Day 1, p. 579 | `agent_spec.md` §4 | Documented: USD 0.05/task; tracking pending |
| Policy mode: auto / ask_on_write / always_ask | Day 1, p. 579 | `agent_spec.md` §5 | Documented: ask_on_write; implementation pending |
| Three input/output success examples | Day 1, p. 579 | `agent_spec.md` §6 | Documented synthetic examples; unexecuted |
| Basic tool-calling loop; no multi-agent yet | Day 2, p. 579 | `agent/`; plan Phase 3 | Planned |
| Test on five inputs | Day 2, p. 579 | Five cases enumerated in plan Phase 3 | Planned; zero executed |
| Save JSONL traces | Day 2, p. 579 | Actual loop runs; plan Phase 3 and submission checklist | Planned; no traces generated |
| Bind at least one MCP server (own server allowed) | Day 3, p. 580 | `tool_server/`; plan Phase 2 | Planned; no protocol integration yet |
| SQLite memory; remembers after restart | Day 3, p. 580 | `storage/`, agent restart test; plan Phase 3 | Planned; no database or restart test yet |
| Permission layer and audit log | Day 4, p. 580 | Server and storage; plan Phases 2–3 | Planned |
| Cost tracker | Day 4, p. 580 | Agent and SQLite task/call costs; plan Phase 3 | Planned |
| Three hostile prompt-injection inputs; must not be deceived | Day 4, p. 580 | Three explicit cases in plan Phase 4 with outcome/side-effect checks | Planned; zero executed |
| Simple Streamlit UI | Day 5, p. 580 | `ui/`; plan Phase 4 | Planned |
| Deploy to Render or Railway | Day 5, p. 580 | Plan Phase 5 | Planned; no host selected or deployment |
| Write README and document average cost | Day 5, p. 580 | README; measured average added in Phase 5 | Phase 1 status README exists; cost reporting pending |
| Public GitHub repository | LMS item 1, p. 581 | Current project repository | Repository exists locally; public visibility unverified |
| Live demo URL | LMS item 2, p. 581 | Verified deployed service | Missing until Phase 5 |
| `traces/success_1.jsonl` | LMS item 3, p. 581 | Actual successful run, sanitized submission trace | Missing; future deliverable |
| `traces/near_failure_recovery.jsonl` | LMS item 3, p. 581 | Actual recovery run, sanitized submission trace | Missing; future deliverable |
| `traces/explicit_failure.jsonl` | LMS item 3, p. 581 | Actual failed run, sanitized submission trace | Missing; future deliverable |
| Submit `agent_spec.md` | LMS item 4, p. 581 | Root specification | Present; final submission not performed |
| `cost_analysis.md`: avg cost/task and monthly projection | LMS item 5, p. 581 | Measured sample and documented projection assumptions; plan Phase 5 | Missing; no costs measured |

The book's Day 1–5 time allocations are recorded in the implementation plan.
They are planning guidance, not measured execution evidence. The supplied excerpt
sets no coverage threshold, trace event schema, specific model, or exact seven
tool names. No claims are made about unseen portions of the book.

## Project requirements and additional quality checks

The following detail includes user requirements and project design choices.
Where it overlaps official items above, it adds verification detail rather than
new official obligations. Exactly seven customer-service tools, official SDK,
genuine integration, no dependency shadowing, and honest evidence are explicit
user requirements. The chosen authentication design, extra security cases,
lockfile, Arabic case, and optional coverage are quality improvements. Real
authentication and persistent hosting are project release gates, not claims
about extra official rubric requirements.

| Requirement | Planned implementation / current document | Verification evidence required | Phase / current status |
| --- | --- | --- | --- |
| Goal | `agent_spec.md` §1 | Inspect explicit scope and exclusions | 1: documented |
| 5–10 allowed tools | `agent_spec.md` §2; contracts in `docs/AGENT_DESIGN.md` §2 | Inspect tool names, inputs, outputs, and access rules | 1: documented |
| Termination: turns, budget, final answer | `agent_spec.md` §3 | Inspect explicit limits; runtime boundary tests planned | 1: documented; enforcement pending |
| USD budget per task | `agent_spec.md` §4 | Inspect USD 0.05 limit; reservation and usage tests planned | 1: documented; accounting pending |
| Permission policy | `agent_spec.md` §5; `docs/AGENT_DESIGN.md` §5 | Inspect ownership and confirmation rules; denial tests planned | 1: documented; enforcement pending |
| Three input/output success examples | `agent_spec.md` §6; detailed fixtures in `docs/AGENT_DESIGN.md` §6 | Inspect three fixture-based examples; acceptance runs planned | 1: documented; examples unexecuted |
| Minimal Python structure; no dependency shadowing | `pyproject.toml`, `src/yemen_customer_service/`, `tests/` | File presence, TOML parse; verify no top-level `mcp.py` or `mcp/` | 1: scaffold only |
| Safe configuration | `.gitignore`, `.env.example` | Inspect empty credential field and ignore rules; no real credentials added | 1: template only |
| Accurate documentation and roadmap | `README.md`, `docs/IMPLEMENTATION_PLAN.md`, this matrix | Inspect status language and phased acceptance criteria | 1: documented |
| Single-agent LLM loop | `agent/` | Controlled-response tests plus separately identified live LLM run | 3: planned |
| Genuine official MCP integration | `tool_server/`, agent MCP client | Official SDK dependency/version; actual stdio initialization, discovery, calls | 2–3: planned |
| `list_products` | `tool_server/` | MCP call verifies pagination, result limits, summaries | 2: planned |
| `search_products` | `tool_server/` | MCP call verifies matching, bounded query, safe SQL | 2: planned |
| `get_product_details` | `tool_server/` | MCP calls for known and missing product IDs | 2: planned |
| `get_store_policies` | `tool_server/` | MCP calls verify topic filtering and policy version | 2: planned |
| `verify_order_access` | `tool_server/` | Own-order success, foreign/missing denial, forged principal rejection | 2: planned |
| `get_order_status` | `tool_server/` | MCP calls verify scoped/expired references and minimal disclosure | 2: planned |
| `create_support_ticket` | `tool_server/` | MCP calls verify confirmation, edited drafts, ownership, idempotent retries | 2: planned |
| SQLite persistent memory | `storage/` | Close/reopen database and restart checks; cross-principal isolation | 2–3: planned |
| Server-side permissions | `tool_server/`, trusted session context | Unauthorized calls denied even when UI/agent is bypassed | 2: planned |
| Trusted security references and ticket confirmation | Client adapter, `tool_server/` | References hidden from model; forged/cross-session references denied; paired order fields; atomic consent; identical retry succeeds without duplicate and changed-payload retry fails | 2–3: planned |
| Audit logging | `storage/`, `tool_server/`, `agent/` | Assert allow/deny/error events, task correlation, redaction | 2–3: planned |
| Cost tracking and hard limit | `agent/`, `storage/` | Actual usage accounting; reservation, retry, unknown usage, limit tests | 3: planned |
| Limits across ticket confirmation/resumption | `agent/`, trusted task state | Same task retains usage/turns/active-time limits; deterministic limit response makes no LLM call | 3: planned |
| Prompt-injection defenses | `tests/security/` and permission boundary | Malicious catalog, policies, memory, messages, and results cannot authorize side effects or leak data | 4: planned |
| Streamlit UI | `ui/` | Executed chat, confirmation, cost-display, and session-isolation smoke checks | 4: planned |
| Public deployment | Render or Railway configuration to be selected | Actual public endpoint, authenticated functional checks, persistent-volume restart | 5: planned |
| Honest tests, traces, and coverage | Future test suite; ignored `artifacts/` | Actual runner outputs with commit/versions; no zero-test readiness claim | 2–5: no runtime evidence yet |
| No secrets committed | Ignore rules and secure configuration practices | Review staged changes before any future commit; inspect safe configuration | All phases; no commit performed in Phase 1 |

Phase 1 completion does not imply any runtime row has passed. File-presence and
diff checks are structural evidence only; no test suite exists yet.
