# Final submission acceptance checklist

Status as of 2026-11-04 (Asia/Aden). The owner reports Railway/Google/live chat and
hosted tickets are working. The latest dark/RTL/email-invitation candidate still
needs review and actual first-login/browser acceptance. See
PROFESSOR_ACCESS_AND_DARK_RTL.md; earlier validation notes are historical.
Unchecked means final acceptance is pending;
it does not imply the existing implementation is missing. Historical fixture
results are in the requirements matrix. This checklist introduces no new official
requirements. Evidence must identify its commit, environment and provenance.

## A. Mandatory Chapter 12.10 academic deliverables

| Gate | Source | Existing evidence / remaining objective acceptance |
| --- | --- | --- |
| [ ] Real task end-to-end, public URL, cost tracking | Goal p. 578 | Existing agent and tracker; verify actual hosted task and reachable demo |
| [x] Select one of eight domains | Day 1 pp. 578–579 | Customer service selected |
| [x] One-page agent_spec.md | Day 1 p. 579 | All six elements retained; one A4 page at 11 pt body/15 mm margins, verified local PDF text extraction; other viewers can paginate differently |
| [x] One-sentence goal | Day 1 p. 579 | agent_spec.md section 1 |
| [x] 5–10 allowed tools | Day 1 p. 579 | Exactly seven named tools |
| [x] max_turns, budget and final_answer termination | Day 1 p. 579 | Explicit limits in specification; runtime fixture coverage exists |
| [x] USD budget per task | Day 1 p. 579 | USD 0.05 estimated cap |
| [x] Permission mode | Day 1 p. 579 | ask_on_write and server-enforced private-read ownership |
| [x] Three I/O success examples | Day 1 p. 579 | All three specified; examples are not execution evidence |
| [ ] Basic single-agent tool loop, five inputs, JSONL | Day 2 p. 579 | Five fixture scenarios tested through MCP; one live-labeled product/policy success reviewed; full final acceptance remains pending; no multi-agent |
| [x] At least one MCP server | Day 3 p. 580 | Official SDK stdio discovery/calls and seven tool contracts exercised in retained/final tests |
| [x] SQLite memory remembers after restart | Day 3 p. 580 | Real process restart/scoping tests retained; does not certify the current hosted disk |
| [ ] Permission layer, audit log, cost tracker | Day 4 p. 580 | Existing tested implementation; verify hosted access/spending gates and records |
| [x] Three hostile prompt-injection inputs | Day 4 p. 580 | Product, forged-consent and persistent-memory attacks executed with real MCP/provider fixtures; no universal live-model safety claim |
| [ ] Simple Streamlit UI | Day 5 p. 580 | Local bilingual UI exists; offline production UI regression is recorded in SECURE_HOSTING.md; real hosted workflow review remains pending |
| [ ] Deploy to Render or Railway | Day 5 p. 580 | Owner reports deployed Railway/Google/live chat; final commit, access/confirmation/restart observations still required |
| [x] README and average cost | Day 5 p. 580 | README reflects reviewed traces and n=3 recorded-usage estimated mean USD 0.000208666667/task; cost_analysis.md states rates, scope and billing limits; final hosted instructions remain pending |
| [x] Public GitHub repository | LMS item 1 p. 581 | GitHub HTML returned HTTP 200 and Public label; final submission commit/merge still pending |
| [ ] Live demo URL | LMS item 2 p. 581 | Owner supplies Railway URL in README; workspace health blocked by proxy; actual professor/current reviewed-commit acceptance pending |
| [x] traces/success_1.jsonl | LMS item 3 p. 581 | Imported unchanged live-labeled success trace; report/SQLite/audits/usage cross-checked offline; billing unverified; see SUCCESS_EVIDENCE_VALIDATION.md |
| [x] traces/near_failure_recovery.jsonl | LMS item 3 p. 581 | Reviewed live-labeled recovery trace imported byte-identically; hash, same-task sequence, tokens/cost and supplied report checked; private DB checks attributed to prior reviewer; billing unverified; see RECOVERY_EVIDENCE_VALIDATION.md |
| [x] traces/explicit_failure.jsonl | LMS item 3 p. 581 | Reviewed live-labeled terminal turn_limit trace imported byte-identically; one read/request, usage/cost and report verified; private DB checks attributed to original reviewer; billing unverified; see EXPLICIT_FAILURE_EVIDENCE_VALIDATION.md |
| [ ] agent_spec.md submitted | LMS item 4 p. 581 | Final six-element one-page file linked in submission |
| [x] cost_analysis.md | LMS item 5 p. 581 | Independent usage/cost arithmetic; n=3 includes terminal failure; total/average, historical rates, formula and 100/1,000/10,000-task monthly projections; billing unverified |

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
- [x] Received success originals/attempt.lock and reviewed recovery/failure ZIPs retained privately; all three exports match their stated original hashes without redactions. Recovery/failure raw databases remain outside this workspace; private checks are attributed to their reviewers.
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


## Trace artifact readiness — November 4, 2026

All three official trace files are present and reviewed with unchanged original
bytes: success_1 (completed), near_failure_recovery (completed after the disclosed
harness-controlled read retry), and explicit_failure (terminal turn_limit).
This completes the trace-file preparation gate, not final LMS submission or
independent provider/billing verification. Private database/plan checks remain
attributed to the scope of each validation report. No new model execution occurred.


## Cost-document readiness — November 4, 2026

cost_analysis.md and the README now report six requests, 5,500 input / 152 output /
0 cached tokens, USD 0.0006260 total and the n=3 observed mean including failure.
The monthly projections assume unchanged historical rates and the observed
three-scenario mix; small-sample and infrastructure/billing limits are explicit.
This prepares the cost artifact; final submission and hosted-demo gates remain open.


## Hosted-demo preparation — November 4, 2026

Prepared Render container, private mounted SQLite, native OIDC invitation gate,
logout/expiry, durable shared spending limits, concurrency and kill controls.
See [SECURE_HOSTING.md](SECURE_HOSTING.md) for offline test evidence and
[DEPLOYMENT.md](DEPLOYMENT.md) for exact release steps. This does not check off the
mandatory public URL or deployment item above. All three trace artifacts and
cost_analysis.md remain unchanged.

- [x] Offline OIDC cryptography/code-flow, invitation, expiry/logout/replay and
  principal-isolation tests with clearly labeled issuer/provider fixtures.
- [x] No-demo/no-order production initialization and real private MCP checks.
- [x] Paid-disabled defaults, durable lifetime allowances/reservations and sticky
  unknown-usage block; real cross-process tests and retained accounting.
- [x] Container/proxy preparation and automated bilingual/RTL UI checks.
- [ ] Independently review and merge the hosting PR.
- [ ] Approve infrastructure cost quote, configure private OIDC secrets/invitations
  and persistent disk, then separately approve actual deployment.
- [ ] Validate real HTTPS login/logout/expiry, rejected and isolated users,
  WebSockets, private disk restart and safe unavailable-chat state without paid calls.
- [ ] Record desktop/mobile Arabic/English visual and keyboard review.
- [ ] Separately authorize bounded OpenAI spending before any live hosted chat;
  fresh pricing, restricted key, expiry, positive budgets and private enable required.
- [ ] Privately arrange assessor access and publish the verified login URL only.


## Railway Free preparation update — November 4, 2026

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md). Railway is now preferred over
the preserved Render alternative, conditional on Free entitlements, credit and
network access. No paid-plan upgrade or infrastructure provisioning is authorized.

- [x] Official Railway source limits and native IaC format reviewed with source revision.
- [x] Native configuration locked and evaluated offline (4 passing checks).
- [x] Local 500 MB/1-vCPU/no-swap fixture workload, real MCP, bilingual UI, consent
  and restart checks pass; observed peak 225.3 MiB, no OOM.
- [x] Full regression: 258 passed, 0 failed, 0 skipped; previous tests unmodified.
- [x] Real hosted OpenAI path preserved and ready for private approved activation;
  no fixture fallback, paid execution or deployment performed here.
- [ ] Actual Free account/region/volume/credit/egress confirmed without upgrading.
- [ ] Explicitly approved deployment, real OIDC/TLS/WebSocket and mobile acceptance.
- [ ] Current model/pricing/account recheck, bounded spending approval and private enable.
- [ ] Separately approved live hosted OpenAI task, assessor access and public login URL.

Original trace and measured-cost completion gates remain intact. These preparation
checks do not complete the official deployment/live-URL deliverable.


## Final review candidate: mandatory completion vs verified scope

[FINAL_DEMO_GUIDE.md](FINAL_DEMO_GUIDE.md) provides the professor's five-task
walkthrough and private access prerequisites. [FINAL_VALIDATION.md](FINAL_VALIDATION.md)
records exact tests/visuals and honest remaining limitations.

- [x] Local hosted-form tests cover both reported request phrasings, null/invalid
  order handling, editing, explicit Confirm/Cancel, replay and SQLite create audit.
- [x] Chat yes cannot authorize a write; prose alone creates no ticket/form.
- [x] Current-source factual samples and safe Markdown/English/Arabic rendering tested.
- [x] Real local Chromium desktop/mobile-emulation checks and one-page spec profile.
- [x] Existing global/per-principal/per-task/rate/time/kill controls preserved;
  owner-reported live USD 3 and all live settings/data remain untouched.
- [ ] Independently review the PR and approve deployment of its exact commit separately.
- [ ] Obtain professor's verified Google issuer/subject privately, Google Test User
  access when required and approved application invitation; do not guess values.
- [ ] Actually retest both ticket requests on the reviewed deployed commit; verify
  form, edit/cancel/confirm, actual MCP audit and one persisted ticket privately.
- [ ] Complete hosted Google/HTTPS/WebSocket/expiry/isolation and real browser/mobile checks.
- [ ] Confirm allowance/expiry remains within existing approval before any hosted
  evaluation. This development workflow authorizes no paid test or new allowance.
- [ ] Submit the final repository/URL/spec/three unchanged traces/cost document to LMS.

Recommendation: GO for independent review, NO-GO for claiming final hosted ticket
resolution or unconditional submission readiness before these outstanding checks.


## Latest three-fix review gate

- [x] Pre-polish reference identified: a9bae01 native colors; dark base restored.
- [x] Computed local assistant Arabic paragraph/list/item/marker/heading RTL and
  English-on-Arabic-page LTR checked in actual Chromium desktop/mobile emulation.
- [x] Safe Markdown, mixed Latin product names/IDs/USD, native controls and ticket
  flow preserved; contrast and no-overflow/pointer checks recorded.
- [x] Optional exact Google-email invitation securely enrolls only verified native
  identities; legacy subject list retained. No professor token or manual sub needed.
- [x] Additive invitation extension tested for race/replay, idempotent migration,
  restart and preservation of sessions/memory/ledger/limits.
- [ ] Independently review/merge this branch; no automatic deployment authorized.
- [ ] Privately add the professor's primary email to Google Test Users if required
  and HOSTED_REVIEWER_EMAILS_JSON, preserving existing lists, budget and expiry.
- [ ] Separately deploy the reviewed candidate on the same volume after pending
  drafts are completed; verify real Google first login, legacy user access and
  actual Arabic bot paragraphs/bullets on desktop/mobile.
- [ ] Complete assessor access and final academic submission after those checks.

The owner reports the existing live business flows passed. Local fixture/browser
checks do not newly certify this candidate's hosted behavior or provider billing.
