from typing import Optional, Literal, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, field_serializer
from uuid import UUID


class ExpenseCreate(BaseModel):
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"]
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    original_amount: Optional[Decimal] = None
    interest: Optional[Decimal] = None
    fine: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    contact_id: Optional[str] = None
    description: Optional[str] = None
    document: Optional[str] = None
    payment_method: Optional[Literal["pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"]] = None
    account: Optional[str] = None
    recurrence: Optional[bool] = None
    competence: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    active: bool = True


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = None
    status: Optional[Literal["pendente", "pago", "cancelado"]] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    original_amount: Optional[Decimal] = None
    interest: Optional[Decimal] = None
    fine: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    contact_id: Optional[str] = None
    description: Optional[str] = None
    document: Optional[str] = None
    payment_method: Optional[Literal["pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"]] = None
    account: Optional[str] = None
    recurrence: Optional[bool] = None
    competence: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class ExpenseOut(BaseModel):
    id: UUID
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"]
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    original_amount: Optional[Decimal] = None
    interest: Optional[Decimal] = None
    fine: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    contact_id: Optional[str] = None
    description: Optional[str] = None
    document: Optional[str] = None
    payment_method: Optional[Literal["pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"]] = None
    account: Optional[str] = None
    recurrence: Optional[bool] = None
    competence: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer('amount', 'original_amount', 'interest', 'fine', 'discount', 'total_paid')
    def _ser_amounts(self, v: Decimal | None):
        from decimal import Decimal as _D
        return float(v if v is not None else _D('0'))
