from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_serializer


class IncomeCreate(BaseModel):
    amount: Decimal
    status: Literal["pendente", "recebido", "cancelado"]
    issue_date: date | None = None
    due_date: date | None = None
    receipt_date: date | None = None
    original_amount: Decimal | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_received: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    contact_id: UUID | None = None
    description: str | None = None
    document: str | None = None
    receiving_method: Literal["pix", "boleto", "cartao", "transferencia", "dinheiro"] | None = None
    account: UUID | None = None
    recurrence: bool | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool = True


class IncomeUpdate(BaseModel):
    amount: Decimal | None = None
    status: Literal["pendente", "recebido", "cancelado"] | None = None
    issue_date: date | None = None
    due_date: date | None = None
    receipt_date: date | None = None
    original_amount: Decimal | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_received: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    contact_id: UUID | None = None
    description: str | None = None
    document: str | None = None
    receiving_method: Literal["pix", "boleto", "cartao", "transferencia", "dinheiro"] | None = None
    account: UUID | None = None
    recurrence: bool | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool | None = None


class IncomeOut(BaseModel):
    id: UUID
    amount: Decimal
    status: Literal["pendente", "recebido", "cancelado"]
    issue_date: date | None = None
    due_date: date | None = None
    receipt_date: date | None = None
    original_amount: Decimal | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_received: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    contact_id: UUID | None = None
    description: str | None = None
    document: str | None = None
    receiving_method: Literal["pix", "boleto", "cartao", "transferencia", "dinheiro"] | None = None
    account: UUID | None = None
    recurrence: bool | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "original_amount", "interest", "fine", "discount", "total_received")
    def _ser_amounts(self, v: Decimal | None):
        from decimal import Decimal as _D

        return float(v if v is not None else _D("0"))
