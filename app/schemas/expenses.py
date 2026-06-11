from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

PaymentMethod: TypeAlias = Literal[
    "pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"
]


class ExpenseCreate(BaseModel):
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"]
    issue_date: date
    contact_id: UUID
    description: str
    account_id: UUID
    due_date: date | None = None
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    transfer_id: UUID | None = None
    installment_group_id: UUID | None = None
    installment_number: int | None = None
    installments_total: int | None = None
    active: bool = True


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = None
    status: Literal["pendente", "pago", "cancelado"] | None = None
    issue_date: date | None = None
    due_date: date | None = None
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    contact_id: UUID | None = None
    description: str | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = None
    account_id: UUID | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    transfer_id: UUID | None = None
    installment_group_id: UUID | None = None
    installment_number: int | None = None
    installments_total: int | None = None
    active: bool | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"]
    issue_date: date
    contact_id: UUID
    description: str
    account_id: UUID
    due_date: date | None = None
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    transfer_id: UUID | None = None
    installment_group_id: UUID | None = None
    installment_number: int | None = None
    installments_total: int | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "interest", "fine", "discount", "total_paid")
    def _ser_amounts(self, v: Decimal | None):
        from decimal import Decimal as _D

        return float(v if v is not None else _D("0"))


class ExpenseInstallmentPlanCreate(BaseModel):
    amount_total: Decimal
    installments_total: int
    issue_date: date
    first_due_date: date | None = None
    contact_id: UUID
    description: str
    account_id: UUID
    status: Literal["pendente", "pago", "cancelado"] = "pendente"
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool = True


class ExpenseInstallmentGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount_total: Decimal
    installments_total: int
    issue_date: date
    first_due_date: date
    account_id: UUID
    contact_id: UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount_total")
    def _ser_amount_total(self, v: Decimal):
        return float(v)


class ExpenseInstallmentGroupWithExpensesOut(BaseModel):
    group: ExpenseInstallmentGroupOut
    expenses: list[ExpenseOut]


class ExpenseInstallmentGroupSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount_total: Decimal
    installments_total: int
    issue_date: date
    first_due_date: date
    account_id: UUID
    contact_id: UUID
    active: bool

    expenses_count: int
    pending_count: int
    paid_count: int
    canceled_count: int
    total_paid: Decimal
    next_due_date: date | None = None

    created_at: datetime
    updated_at: datetime

    @field_serializer("amount_total", "total_paid")
    def _ser_amounts(self, v: Decimal):
        return float(v)


class ExpenseInstallmentGroupUpdate(BaseModel):
    description: str | None = None
    active: bool | None = None
