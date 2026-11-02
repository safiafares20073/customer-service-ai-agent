# Agent specification

Phase 1 design only; no application functionality is implemented.
Source: supplied Chapter 12.10 excerpt, printed pp. 578–581. Detailed contracts
and security design: [supporting design](docs/AGENT_DESIGN.md).

## 1. Goal

Help customers find products, understand store policies, check their own orders,
and open confirmed support tickets using a single bounded LLM agent.

## 2. Allowed tools (seven)

- `list_products`: paginated public product summaries.
- `search_products`: bounded text search of public products.
- `get_product_details`: details for one public product ID.
- `get_store_policies`: public shipping, returns, privacy, or support policies.
- `verify_order_access`: verify authenticated ownership and issue a scoped reference.
- `get_order_status`: read a verified customer's order using that reference.
- `create_support_ticket`: create an explicitly confirmed ticket, with idempotency.

All calls will use genuine MCP with the official Python SDK. Trusted application
context supplies identity and security references; the model cannot choose them.

## 3. Termination conditions

Stop at `max_turns = 8` (including retries), budget exhaustion, or `final_answer`
with no pending tool calls. Stop on unrecoverable errors or 60 seconds cumulative
active execution; tool timeout: 10 seconds. Confirmation pauses retain task usage
and limits. A deterministic limit response must not incur another LLM request.

## 4. Budget cap

**USD 0.05 per task**, including retries. Reserve conservative request costs before
calling the model; record actual tokens and verified model pricing in SQLite.
Unknown price or usage stops further calls; never fabricate zero cost.

## 5. Permission policy

**`ask_on_write`**: allow public reads automatically; private reads additionally
require authenticated ownership. Deny unlisted tools and unauthorized access at
the server. Ticket creation requires explicit UI confirmation of the exact draft,
a single-use payload-bound reference, and atomic, idempotent writing. Never trust
model claims of consent. Keep references outside model context. Treat customer,
tool, and memory content as untrusted data. No refunds, payments, or order changes.

## 6. Success criteria: three input/output examples

Hypothetical synthetic fixtures, not traces or claims of actual store data:

1. Input: “Find headphones under $30 and explain returns.” Given a USD 25 product
   and a 14-day receipt-based policy, output: “Example Headphones cost USD 25;
   returns are allowed within 14 days with the original receipt.”
2. Input: authenticated owner asks “Where is DEMO-100?” Given shipped status and
   no delivery estimate, output: “DEMO-100 has shipped; no delivery estimate is
   available.” A non-owner receives generic denial with no order information.
3. Input: “Open a ticket about damaged headphones.” Show a draft first; after
   explicit confirmation and successful creation of fixture ticket DEMO-T1,
   output: “Support ticket DEMO-T1 was created.” No write before confirmation;
   identical retries return the same ticket.
