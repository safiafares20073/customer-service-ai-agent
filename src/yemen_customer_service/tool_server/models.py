"""Bounded wire types and validated server outputs."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Identifier = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]
Reference = Annotated[str, Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")]
Subject = Annotated[str, Field(min_length=1, max_length=120, pattern=r"\S")]
Message = Annotated[str, Field(min_length=1, max_length=2000, pattern=r"\S")]
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=20)]
Topic = Literal["shipping", "returns", "privacy", "support", "all"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class Product(StrictModel):
    product_id: Identifier
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=2000)]
    price: Annotated[str, Field(pattern=r"^\d+\.\d{2}$")]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class ProductDetails(Product):
    availability: Literal["in_stock", "out_of_stock"]


class ProductList(StrictModel):
    products: Annotated[list[Product], Field(max_length=20)]
    next_cursor: Annotated[str, Field(max_length=128)] | None = None


class Policy(StrictModel):
    topic: Literal["shipping", "returns", "privacy", "support"]
    text: Annotated[str, Field(min_length=1, max_length=4000)]
    version: Annotated[str, Field(min_length=1, max_length=64)]


class Policies(StrictModel):
    policies: Annotated[list[Policy], Field(max_length=4)]


class Access(StrictModel):
    authorized: Literal[True]
    access_reference: Reference


class OrderStatus(StrictModel):
    order_id: Identifier
    status: Literal["processing", "shipped", "delivered", "cancelled"]
    estimated_delivery: Annotated[str, Field(max_length=32)] | None


class Ticket(StrictModel):
    ticket_id: Identifier
    status: Literal["created"]


OUTPUT_MODELS = {
    "list_products": ProductList,
    "search_products": ProductList,
    "get_product_details": ProductDetails,
    "get_store_policies": Policies,
    "verify_order_access": Access,
    "get_order_status": OrderStatus,
    "create_support_ticket": Ticket,
}


class TicketDraft(StrictModel):
    subject: Subject
    message: Message
    idempotency_key: Identifier
    order_id: Identifier | None = None


class SafeError(Exception):
    """Only fixed public messages/codes may cross the MCP boundary."""

    MESSAGES = {
        "ACCESS_DENIED": "Access denied.",
        "INVALID_INPUT": "Invalid tool arguments.",
        "NOT_FOUND": "Product not found.",
        "CONFIRMATION_REQUIRED": "Valid confirmation of this exact draft is required.",
        "IDEMPOTENCY_CONFLICT": "Idempotency key was already used for a different draft.",
        "UNKNOWN_TOOL": "Tool is not allowed.",
        "INTERNAL_ERROR": "The operation could not be completed.",
    }

    def __init__(self, code: str):
        self.code = code
        super().__init__(self.MESSAGES[code])
