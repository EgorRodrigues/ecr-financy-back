from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, field_serializer

PaymentMethod: TypeAlias = Literal[
    "pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"
]


class ExpenseCreate(BaseModel):
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
    active: bool = True


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = None
    status: Literal["pendente", "pago", "cancelado"] | None = None
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
    active: bool | None = None


class ExpenseOut(BaseModel):
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
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "original_amount", "interest", "fine", "discount", "total_paid")
    def _ser_amounts(self, v: Decimal | None):
        from decimal import Decimal as _D

        return float(v if v is not None else _D("0"))
