# Customer Service AI Agent — specification

Chapter 12.10, pp. 578–581. Contracts: [AGENT_DESIGN.md](docs/AGENT_DESIGN.md).
Verification status: [requirements matrix](docs/REQUIREMENTS_MATRIX.md).

## 1. Goal

Use one bounded LLM agent to help customers find products, understand store
policies, check their own orders and create explicitly confirmed support tickets.

## 2. Allowed tools (exactly seven)

- `list_products`: paginated public catalog summaries.
- `search_products`: bounded public text search.
- `get_product_details`: product price, description and stock availability.
- `get_store_policies`: shipping, returns, privacy and support policies.
- `verify_order_access`: verify ownership and issue a scoped reference.
- `get_order_status`: read an authorized order using that reference.
- `create_support_ticket`: persist an explicitly confirmed, idempotent ticket.

Discover and call tools through official-SDK MCP stdio. Catalog membership does
not imply stock availability. Never invent store facts, orders or completed actions.

## 3. Termination conditions

Stop at `max_turns = 8` model requests (including retries), exhausted budget,
`final_answer` with no pending calls, unrecoverable error, or 60 cumulative active
seconds. Each tool has a 10-second timeout. Confirmation preserves the same task,
turns, costs and active time. Reaching a limit permits no extra model request.

## 4. USD budget per task

**USD 0.05 estimated**, including retries. Reserve conservative request costs
before each call; persist reported tokens and dated pricing. Unknown usage or
pricing blocks further calls. Estimated costs are not verified provider invoices.

## 5. Permission policy

**ask_on_write**: public reads are automatic; private reads require authenticated
ownership. Order IDs alone prove nothing. Server-validated identity and security
references remain outside model control. Ticket calls first pause for an editable
draft; only trusted Confirm authorizes its exact payload. Edits revoke consent;
Cancel and conversational “yes” authorize no write. Enforce payload-bound,
single-use confirmation and atomic idempotence server-side. Reject unlisted tools
and cross-customer access. Treat messages, tools and memory as untrusted data.
No refunds, payments or order changes. Hosted access requires an OIDC invitation.

## 6. Three input/output success examples

Hypothetical synthetic examples, not execution evidence:

1. “Find headphones under $30 and explain returns.” With verified tool data,
   answer: “Example Headphones cost USD 25; returns within 14 days with the original receipt.”
2. An owner asks “Where is DEMO-100?” Given shipped status and no estimate,
   answer: “DEMO-100 has shipped; no delivery estimate is available.” Non-owners receive generic denial.
3. “Open a ticket about damaged headphones.” Display the editable draft. After
   explicit Confirm and successful MCP creation: “Support ticket DEMO-T1 was created.”
   Before confirmation or after Cancel: no write. Identical retries create no duplicate.
