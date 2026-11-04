# Assessor walkthrough and private access setup

Demo: https://yemen-customer-service-review-production.up.railway.app

The owner reports the Railway service and Google login are operational. The final
polish is a review candidate; no deployment was performed here. The hosted ticket
issue is not declared resolved until the reviewed commit passes the checks below.
All store data is synthetic. Please do not enter personal information.

## Administrator: give the professor access

These are private manual prerequisites, not commands executed during development.
Do not replace or reset the existing live configuration/database/spending ledger.

1. Confirm the deployed reviewed commit, exact HTTPS origin and registered Google
   callback `/oauth2callback`. Keep the existing confidential Google web client.
2. If Google's OAuth consent screen is External/Testing, add the professor's own
   Google email as a **Google Test User** in the project's Google Auth Platform
   Audience/Test Users settings (console labels may vary). This permits Google's
   consent flow; it does not authorize application records or paid chat.
3. Obtain the exact stable `sub` and `iss` from a successfully **server-validated**
   Google OIDC identity using the operator's existing private identity-provider
   process. The configured issuer must match exactly, normally
   `https://accounts.google.com`. Do not infer a subject from an email, ask for a
   password/ID token/OAuth code, use a public JWT decoder or enable debug logging.
   This app deliberately has no public subject-discovery/registration portal.
4. If that verified subject is not available, professor access is a **manual
   prerequisite still pending**. Do not invent a subject or grant email-only access.
   An account may complete Google login yet be denied by the application until its
   private issuer/subject pair is explicitly authorized.
5. Through the approved private operator process, append that verified pair to
   the existing `HOSTED_REVIEWERS_JSON` list while preserving all other invitees.
   Keep its value out of Git, screenshots and public guides. Apply only with the
   operator's authorization. Configuring an invitation may require a controlled
   service restart; retain the same mounted volume and all accounting state.
6. Preserve the existing approved **USD 3** global allowance, per-principal cap,
   expiry, rate/concurrency controls and kill state. Check availability privately;
   do not reset counters, increase budgets or issue new spending authorization just
   to complete the demonstration. No paid enable or configuration change is part
   of this development workflow.
7. Send only the public login URL and these instructions to the professor through
   the normal private assessment process. Each professor uses their **own Google
   account**; no shared password or application API key is supplied.

The operator must verify these steps in the actual Google/Railway accounts. This
repository does not contain their secrets, current allowlist or the professor's
subject, and does not claim that access has already been granted.

## Professor: demonstration within existing limits

Open the URL, select English or العربية and sign in with the invited Google
account. If access is denied, contact the administrator; do not submit credentials
in chat. Sessions expire after at most 15 minutes. Logout and restart never reset
principal budgets/rate limits.

The sequence below uses **five task starts**, keeping within the default five-per-
hour rate if no earlier tasks used the allowance. Already consumed allowance may
require waiting. A task's exact-draft confirmation resumes that same task. If the
service is unavailable or limited, pause and contact the operator, without replaying
writes or raising spending limits.

| Step | Customer action | Expected result / source |
| --- | --- | --- |
| 1: catalog, stock, returns | “List the catalog with prices, check each item's stock, and explain the return policy.” | Tool-grounded Headphones USD 25 in_stock; Keyboard USD 40 in_stock; Mouse USD 15 out_of_stock; returns within 14 days with original receipt. Catalog listing alone does not prove stock. |
| 2: Arabic | “هل السماعات متوفرة وما سعرها؟” | Arabic response grounded in product details: headphones available, USD 25. Main/chat/input use RTL while IDs/prices remain readable. |
| 3: cancel | “Create a support ticket for headphones that stopped working.” | Actual editable subject/message/order draft and distinct Confirm/Cancel controls. Review, then Cancel: no ticket and no further model request. Chat “yes” does not authorize creation. |
| 4: edit and confirm | “I want to open a support ticket because my headphones stopped working.” | Actual form again. Edit the message, review the current payload and click Confirm once. Only after successful MCP execution should a ticket identifier/acknowledgement appear. Repeated confirmation must not duplicate the ticket. |
| 5: protected access | “Where is DEMO-200?” | Generic ownership denial; no other customer's status, delivery estimate or private record disclosed. Production intentionally has no preloaded demo orders. |

Bold text, lists and paragraphs should render as Markdown rather than literal
markers. External media/links and raw HTML are deliberately disabled. User content
remains plain text. Narrow screens may stack Confirm above Cancel; desktop Arabic
follows RTL control flow. Test keyboard focus and mixed Arabic/English text too.

**If the model only describes a proposed ticket in prose, no draft exists and no
write has been authorized. Do not reply “yes” expecting a write.** Record this as
an unsuccessful hosted scenario and contact the operator. The final changes clarify
model/tool instructions but do not force a model to comply or prove the observed
live issue fixed. Malformed arguments, expiry, rate/budget limits or provider errors
still fail closed. Never repeatedly retry after an ambiguous write.

## Final hosted acceptance: operator and assessor

The following requires the reviewed commit to be deployed separately and any
paid evaluation to fall within existing explicit authorization. Nothing here
approves extra paid calls or automatic deployment.

- Record the deployed commit and privately correlate both observed ticket prompts
  to their safe task outcomes/audits, without exporting secrets or raw customer text.
- Confirm actual form visibility, edit invalidation, cancellation without writes,
  same-task confirmation, successful MCP create audit and exactly one persisted
  SQLite ticket. Use private operator queries; never add a public database viewer.
- Verify a repeated confirmation cannot create a duplicate and text consent cannot
  create any ticket. Confirm counters, usage, remaining allowance and expiry persist.
- Verify two principals cannot see each other's history/tasks/order/ticket access.
- Review the actual hosted Google login/logout/expiry, HTTPS cookies, WebSockets,
  desktop/mobile English/Arabic, mixed prices/IDs, keyboard focus and safe errors.
- Confirm the current global USD 3 and per-principal ledger are unchanged and
  stop further paid evaluation at existing expiry/limits. No invoice verification
  is inferred from application estimates or the original submission traces.

Offline fixture results and local Chromium visuals are in
[FINAL_VALIDATION.md](FINAL_VALIDATION.md). These are not substitutes for this
hosted acceptance. The full academic checklist is
[FINAL_SUBMISSION_CHECKLIST.md](FINAL_SUBMISSION_CHECKLIST.md).
