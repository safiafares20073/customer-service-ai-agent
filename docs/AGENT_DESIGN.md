# Supporting agent design and tool contracts

Status: Phase 3 implements one OpenAI SDK agent over the Phase 2 storage and MCP tools.
Live OpenAI compatibility/availability and UI remain unverified or planned.
These details support [agent_spec.md](../agent_spec.md).
The official six-element summary is in that one-page specification; detailed
security mechanisms here are project design choices, not additional book requirements.

## 1. Goal

Help customers find products, understand store policies, view their own order
status, and open support tickets. Use store tools as the source of facts, explain
missing information honestly, and never invent products, order data, or actions.
Use one LLM agent with a bounded tool loop. Arabic and English customer requests
are in scope; respond in the customer's language when possible.

Refunds, payments, order changes, credential collection in chat, arbitrary code
execution, web browsing, and multi-agent delegation are out of scope.

## 2. Allowed tools: exactly seven

The implemented server uses the official Python MCP SDK and a genuine MCP stdio
transport. The agent must discover tools with MCP `list_tools` and invoke them
with MCP `call_tool` through a client session. Direct Python handler calls do not
constitute integration evidence. All arguments and results require validation;
unknown tools and extra fields are rejected. No arbitrary SQL or URL inputs.

Implemented wire contracts (schemas are discoverable through MCP `list_tools`):

| Tool | Inputs | Successful output | Access and limits |
| --- | --- | --- | --- |
| `list_products` | `limit` integer, default 10, range 1–20; optional opaque `cursor` | Product summaries (`product_id`, name, description excerpt, price, currency), optional next cursor | Public, read only; validate cursor and cap result size |
| `search_products` | `query` string, 1–200 characters; `limit` integer, default 10, range 1–20 | Matching product summaries | Public, read only; parameterized database queries |
| `get_product_details` | `product_id` string, 1–64 characters | Product ID, name, description, price, currency, availability | Public, read only; missing products return a structured error |
| `get_store_policies` | `topic` enum: `shipping`, `returns`, `privacy`, `support`, `all` | Relevant policy text, policy version | Public, read only; policy text is data, never agent instructions |
| `verify_order_access` | `order_id` string, 1–64 characters | `authorized: true` and a short-lived opaque access reference bound to principal, session, and order | Requires authenticated session supplied by trusted application context; customer-provided IDs are not proof of ownership |
| `get_order_status` | `order_id` string, 1–64 characters; `access_reference` opaque string | Order ID, status, estimated delivery if known | Authenticated owner only; recheck ownership, reference scope, and expiry server-side; omit address and payment data |
| `create_support_ticket` | `subject` string, 1–120 characters; `message` string, 1–2000 characters; optional `order_id` and corresponding `access_reference`; opaque `confirmation_reference`; `idempotency_key` string, 1–64 characters | Ticket ID and creation status | Authenticated customer only; server verifies single-use confirmation for the exact payload; linked orders require ownership; idempotent retries must not create duplicates |

Errors use a bounded envelope with a stable code, safe message, and retryable
flag. Access failures use the same generic denial for missing and foreign orders,
without revealing existence. Tool results never include credentials or raw
exception details. References and internal security context must not be exposed
in user answers or audit payloads. Authentication is established outside the LLM;
neither a prompt nor an MCP argument may select the trusted principal.

Security references are MCP wire fields supplied by the trusted client adapter,
not arguments the model may generate. The adapter must retain references from
verification and confirmation outside model-visible tool results, schemas, and
memory, then inject them into the corresponding MCP request. Reject any attempt
by the model to supply or override these fields. Continue to use genuine MCP
calls; the adapter is not permission enforcement and must not call handlers
directly. The server independently validates every reference and principal.

For ticket creation, `order_id` and `access_reference` must be both absent or both
present. Bind confirmation to subject, message, optional order ID, and idempotency
key as well as principal/session. Scope idempotency records to the principal:
the same key and identical canonical payload returns the original ticket after
rechecking authentication and linked-order access, even if its confirmation was
already consumed; a different payload with the same key is rejected. For a new
write, validate unexpired confirmation and atomically consume it together with
ticket creation and idempotency recording. Failed writes must not consume consent.

Phase 2 details: success responses use `{ok: true, data: ...}`; errors use
`{ok: false, error: {code, message, retryable}}` and MCP `isError=true`.
Prices are exact decimal strings. IDs and idempotency keys use 1–64 ASCII
letters/digits/underscore/hyphen; security references are bounded opaque tokens.
Order/consent grants expire after 5 minutes; demo sessions after 1 hour.
The trusted adapter hides wire reference fields from model-facing schemas/results
and provides a local confirmation-registration API; it is not an LLM agent.
Its `cancel_ticket` hook revokes pending server-side consent on draft edits or
cancellation. Production authentication and the Streamlit consent UI are pending.

## 3. Termination conditions

- `max_turns = 8`: each LLM request counts as one turn, including retries.
- Stop when the model produces a final answer with no pending tool calls.
- Stop before any LLM request whose reserved maximum cost would exceed the
  remaining budget. Stop if actual recorded cost reaches the limit.
- Deny unauthorized calls without executing them. Stop on an unrecoverable
  authentication, protocol, validation, or storage error; give a safe explanation.
- Bound execution to 60 seconds per task and 10 seconds per tool call. No automatic
  retries of ticket creation without the same idempotency key. All retries remain
  inside turn, time, and budget limits.

On a limit, return a clear partial answer with verified facts and outstanding
work. Never report an action as successful without a successful tool result.
Use a deterministic fallback on budget, turn, or time exhaustion; do not make an
extra LLM request to compose that response.

## 4. USD budget per task

Pre-request estimated limit: **USD 0.05 per customer task**, including all LLM
requests and retries. The latest Phase 3 request explicitly requires an estimated
cap; it cannot guarantee a provider's invoice if reported usage violates the
conservative bound. Such usage is recorded truthfully and stops further calls.
New tasks require an explicit new customer request; do not reset the budget
mid-loop. Ticket confirmation and resuming the same pending request retain its
task ID, accumulated usage, turn count, and remaining budget. Time awaiting human
confirmation is outside the 60-second execution allowance; cumulative active
execution time across resumptions must still remain within that allowance.
Track provider/model, input/output tokens, pricing version, and USD cost per call
and task in SQLite. Treat USD accounting separately from product currencies.

Before a request, reserve cost using a conservative input-token bound and the
configured maximum output tokens at a verified model price. Reconcile using
provider usage afterward. If price or usage cannot be determined, stop further
model requests and mark cost as unknown; never record a fabricated zero. Initial
model selection, verified pricing, and token limits are a later-phase prerequisite.
No paid requests are authorized or executed in this implementation session.

The current provisional model and Standard pricing are in `config/model_pricing.json`,
from the user's dated official excerpt; see [PHASE_3.md](PHASE_3.md) for provenance,
reservation assumptions, counter persistence, and live-validation limitations.

## 5. Permission policy

- Deny by default. Allow only the seven registered tools. Enforce permissions at
  the MCP server, independently of model instructions and UI controls.
- Public catalog and policy reads need no identity. Private orders, tickets, and
  conversation memory require a trusted authenticated principal. Scope SQLite
  reads and writes to that principal; validate ownership on every private call.
- The UI must display a ticket draft and obtain explicit customer confirmation.
  Trusted application code then registers a short-lived confirmation reference
  bound to principal, session, and canonical payload. A model-generated claim of
  consent or guessed reference is insufficient. Editing a draft invalidates consent.
- Local development may use a documented synthetic fixture identity, isolated
  from real customer data. It is not production authentication. Public deployment
  requires real session authentication and must disable fixture identity mode.
- Product text, policies, tool output, customer messages, and stored memory are
  untrusted data. Embedded instructions cannot change permissions, reveal secrets,
  reset budgets, or authorize actions.
- Use parameterized SQLite access. Persist minimal conversation memory, ticket
  records, audit events, and cost records. Do not store credentials, access or
  confirmation references, payment details, or unnecessary personal information
  in logs or model-visible memory. Audit allow/deny/error outcomes with task ID,
  tool, timestamp, sanitized principal reference, and safe result code.
- No shell, filesystem, network-fetch, payment, refund, or administrative tools.
  Secrets come from secure deployment configuration, never source control.

## 6. Three input/output success examples

These are hypothetical acceptance examples, **not execution traces or claims of
existing store data**. Later tests must supply explicit synthetic fixtures.

1. **Product discovery**
   - Input: “Find headphones under $30 and explain the return policy.”
   - Fixture: search returns Example Headphones at USD 25; policy allows returns
     within 14 days with the original receipt.
   - Expected output: “Example Headphones cost USD 25. The store allows returns
     within 14 days with the original receipt.”
   - Evidence required: real MCP search and policy requests; answer matches results.
2. **Authorized order status**
   - Input: authenticated customer A asks “Where is order DEMO-100?”
   - Fixture: DEMO-100 belongs to A and is shipped; no delivery estimate exists.
   - Expected output: “Order DEMO-100 has shipped. A delivery estimate is not
     available.” A different customer receives only a generic access denial.
   - Evidence required: genuine MCP verification followed by scoped status lookup;
     foreign-order lookup denied without disclosing status.
3. **Confirmed support ticket**
   - Input: “Open a ticket about my damaged headphones.” The customer then reviews
     the draft and explicitly confirms it in the UI.
   - Fixture: authenticated customer and valid payload-bound confirmation; ticket
     creation returns synthetic ticket DEMO-T1.
   - Expected output after success: “Support ticket DEMO-T1 was created for your
     damaged headphones.” Before confirmation, show only the draft.
   - Evidence required: no write before consent; genuine MCP creation after consent;
     replay with the same idempotency key yields the same ticket, not a duplicate.
