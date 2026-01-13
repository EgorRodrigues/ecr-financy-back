from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, field_serializer

from app.models.credit_card_invoices import CreditCardInvoiceOut

PaymentMethod: TypeAlias = Literal[
    "pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"
]


class CreditCardTransactionCreate(BaseModel):
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"] = "pago"
    issue_date: date | None = None
    due_date: date | None = None
    payment_date: date | None = None
    original_amount: Decimal | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    category_id: str | None = None
    subcategory_id: str | None = None
    cost_center_id: str | None = None
    contact_id: str | None = None
    description: str | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = "credit_card"
    account: str | None = None
    recurrence: bool | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool = True


class CreditCardTransactionUpdate(BaseModel):
    amount: Decimal | None = None
    status: Literal["pendente", "pago", "cancelado"] | None = "pago"
    issue_date: date | None = None
    due_date: date | None = None
    payment_date: date | None = None
    original_amount: Decimal | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    category_id: str | None = None
    subcategory_id: str | None = None
    cost_center_id: str | None = None
    contact_id: str | None = None
    description: str | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = "credit_card"
    account: str | None = None
    recurrence: bool | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool | None = None


class CreditCardTransactionOut(BaseModel):
    id: UUID
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"]
    issue_date: date | None = None
    due_date: date | None = None
    payment_date: date | None = None
    original_amount: Decimal | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    category_id: str | None = None
    subcategory_id: str | None = None
    cost_center_id: str | None = None
    contact_id: str | None = None
    description: str | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = None
    account: str | None = None
    recurrence: bool | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool
    invoice_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "original_amount", "interest", "fine", "discount", "total_paid")
    def _ser_amounts(self, v: Decimal | None):
        from decimal import Decimal as _D

        return float(v if v is not None else _D("0"))


class CreditCardSummary(BaseModel):
    total_limit: Decimal
    available_limit: Decimal
    transactions: list[CreditCardTransactionOut]
    current_invoice: CreditCardInvoiceOut | None = None
    next_invoices: list[CreditCardInvoiceOut] = []

    @field_serializer("total_limit", "available_limit")
    def _ser_limits(self, v: Decimal):
        return float(v)
