# Final submission acceptance checklist

Status as of 2026-11-03 (Asia/Aden). Unchecked means final acceptance is pending;
it does not imply the existing implementation is missing. Historical fixture
results are in the requirements matrix. This checklist introduces no new official
requirements. Evidence must identify its commit, environment and provenance.

## A. Mandatory Chapter 12.10 academic deliverables

| Gate | Source | Existing evidence / remaining objective acceptance |
| --- | --- | --- |
| [ ] Real task end-to-end, public URL, cost tracking | Goal p. 578 | Existing agent and tracker; verify actual hosted task and reachable demo |
| [x] Select one of eight domains | Day 1 pp. 578–579 | Customer service selected |
| [ ] One-page agent_spec.md | Day 1 p. 579 | Present; final render must fit one page and include all six elements below |
| [x] One-sentence goal | Day 1 p. 579 | agent_spec.md section 1 |
| [x] 5–10 allowed tools | Day 1 p. 579 | Exactly seven named tools |
| [x] max_turns, budget and final_answer termination | Day 1 p. 579 | Explicit limits in specification; runtime fixture coverage exists |
| [x] USD budget per task | Day 1 p. 579 | USD 0.05 estimated cap |
| [x] Permission mode | Day 1 p. 579 | ask_on_write and server-enforced private-read ownership |
| [x] Three I/O success examples | Day 1 p. 579 | All three specified; examples are not execution evidence |
| [ ] Basic single-agent tool loop, five inputs, JSONL | Day 2 p. 579 | Five fixture scenarios tested through MCP; one live-labeled product/policy success reviewed; full final acceptance remains pending; no multi-agent |
| [ ] At least one MCP server | Day 3 p. 580 | Existing real official SDK stdio tests; rerun regression for final candidate |
| [ ] SQLite memory remembers after restart | Day 3 p. 580 | Existing cross-process scoped fixture tests; rerun for final candidate |
| [ ] Permission layer, audit log, cost tracker | Day 4 p. 580 | Existing tested implementation; verify hosted access/spending gates and records |
| [ ] Three hostile prompt-injection inputs | Day 4 p. 580 | Three executed fixture attacks with real MCP passed; preserve actual outcomes and clearly state live robustness limits |
| [ ] Simple Streamlit UI | Day 5 p. 580 | Local bilingual UI exists; final candidate must pass UI regression and hosted workflow review |
| [ ] Deploy to Render or Railway | Day 5 p. 580 | Actual TLS URL, deployed commit, access checks, restart persistence and dated observations required |
| [ ] README and average cost | Day 5 p. 580 | Update actual setup/demo/limitations and measured average with sample size |
| [ ] Public GitHub repository | LMS item 1 p. 581 | Repository archive accessible during review; verify logged-out web visibility of final submission commit |
| [ ] Live demo URL | LMS item 2 p. 581 | Public landing/login URL plus privately supplied assessor access; do not publish credentials |
| [x] traces/success_1.jsonl | LMS item 3 p. 581 | Imported unchanged live-labeled success trace; report/SQLite/audits/usage cross-checked offline; billing unverified; see SUCCESS_EVIDENCE_VALIDATION.md |
| [x] traces/near_failure_recovery.jsonl | LMS item 3 p. 581 | Reviewed live-labeled recovery trace imported byte-identically; hash, same-task sequence, tokens/cost and supplied report checked; private DB checks attributed to prior reviewer; billing unverified; see RECOVERY_EVIDENCE_VALIDATION.md |
| [ ] traces/explicit_failure.jsonl | LMS item 3 p. 581 | One-turn fixture failure verified; separately gated live runner prepared, not executed; see LIVE_TRACE_RUNNER.md |
| [ ] agent_spec.md submitted | LMS item 4 p. 581 | Final six-element one-page file linked in submission |
| [ ] cost_analysis.md | LMS item 5 p. 581 | Measured average/task, sample size, dated rates and explicit monthly workload projection |

The excerpt's last cost bullet is incomplete (“monthly project”). Monthly
projection is an interpretation, not a quote of missing text. Day 1–5 durations
are schedule guidance. The source specifies no particular model, auth protocol,
coverage threshold, trace event schema, exact seven names, or unrestricted
anonymous access. Live-provider evidence and the particular security architecture
are explicit project quality requirements; do not attribute them to unseen text.

## B. Required project release safeguards (not extra official rubric items)

- [ ] One agent, exactly seven existing tools, genuine MCP, no SDK shadowing.
- [ ] Production database excludes development identities and their records.
- [ ] Invite-only login verified server-side; no public development auth or shared account.
- [ ] Principal-scoped sessions, memory, tasks and private data; logout/expiry tested.
- [ ] Exact draft approval; edits revoke consent; cancel makes no write/provider request.
- [ ] Resume preserves task, turns, budget and active time; duplicate writes prevented.
- [ ] Server-side ownership and consent enforced even if UI is bypassed.
- [ ] Keys only in secret settings; no secrets/private references in UI, logs or exports.
- [ ] Per-task and durable shared spending limits, bounded concurrency and kill switch.
- [ ] Live calls disabled without separately approved allowance; no model/tier fallback.
- [ ] Persistent SQLite storage with tested restart and private backup/restore procedure.
- [ ] Actual final test/static/build outcomes recorded; no reduced security suite.
- [x] Codespaces success evidence inspected against supplied report, SQLite and historical pricing; no independent provider receipt or invoice verification.
- [x] Received success originals/attempt.lock and reviewed recovery ZIP retained privately; exports match their stated original hashes without redactions. Recovery raw databases remain outside this workspace; explicit failure remains pending.
- [ ] English/Arabic, RTL, narrow screens and browser behavior reviewed honestly.
- [ ] Submission contains no real customer data; invitee login identifiers stay private.
- [ ] Limitations distinguish fixture, live, hosted, visual and billing verification.

## C. Optional production enhancements — defer unless separately requested

- Open self-registration, account recovery, administrative identity management,
  multi-tenant organizations and broad customer-account onboarding.
- Real commerce integration, real customer datasets, refunds/payments/order edits.
- Multi-region/high-availability services, horizontal replicas, PostgreSQL migration.
- Enterprise SSO lifecycle automation, SCIM and complex role hierarchies.
- General multi-device task restoration, distributed queues and advanced telemetry.
- Coverage percentage targets or exhaustive device certification.

These are not necessary for the narrowly scoped capstone. Deferring them does
not justify omitting authentication, authorization, secret handling, tested
persistence or spending controls for the hosted demo.
