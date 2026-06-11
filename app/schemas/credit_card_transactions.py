from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.credit_card_invoices import CreditCardInvoiceOut

PaymentMethod: TypeAlias = Literal[
    "pix", "boleto", "cartao", "transferencia", "dinheiro", "credit_card"
]


class CreditCardTransactionCreate(BaseModel):
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"] = "pago"
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
    payment_method: PaymentMethod | None = "credit_card"
    account_id: UUID | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    installment_group_id: UUID | None = None
    installment_number: int | None = None
    installments_total: int | None = None
    active: bool = True


class CreditCardTransactionUpdate(BaseModel):
    amount: Decimal | None = None
    status: Literal["pendente", "pago", "cancelado"] | None = "pago"
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
    payment_method: PaymentMethod | None = "credit_card"
    account_id: UUID | None = None
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    installment_group_id: UUID | None = None
    installment_number: int | None = None
    installments_total: int | None = None
    active: bool | None = None


class CreditCardTransactionTransfer(BaseModel):
    new_invoice_id: UUID


class CreditCardTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    status: Literal["pendente", "pago", "cancelado"]
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
    installment_group_id: UUID | None = None
    installment_number: int | None = None
    installments_total: int | None = None
    active: bool
    invoice_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "interest", "fine", "discount", "total_paid")
    def _ser_amounts(self, v: Decimal | None):
        from decimal import Decimal as _D

        return float(v if v is not None else _D("0"))


class CreditCardTransactionInstallmentPlanCreate(BaseModel):
    amount_total: Decimal
    installments_total: int
    issue_date: date
    first_due_date: date | None = None
    account_id: UUID
    status: Literal["pendente", "pago", "cancelado"] = "pendente"
    contact_id: UUID | None = None
    description: str | None = None
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    category_id: UUID | None = None
    subcategory_id: UUID | None = None
    cost_center_id: UUID | None = None
    document: str | None = None
    payment_method: PaymentMethod | None = "credit_card"
    competence: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    active: bool = True


class CreditCardTransactionInstallmentGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount_total: Decimal
    installments_total: int
    issue_date: date
    first_due_date: date
    account_id: UUID
    contact_id: UUID | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount_total")
    def _ser_amount_total(self, v: Decimal):
        return float(v)


class CreditCardTransactionInstallmentGroupWithTransactionsOut(BaseModel):
    group: CreditCardTransactionInstallmentGroupOut
    transactions: list[CreditCardTransactionOut]


class CreditCardTransactionInstallmentGroupSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount_total: Decimal
    installments_total: int
    issue_date: date
    first_due_date: date
    account_id: UUID
    contact_id: UUID | None = None
    active: bool

    transactions_count: int
    pending_count: int
    paid_count: int
    canceled_count: int
    total_invoiced: Decimal
    next_due_date: date | None = None

    created_at: datetime
    updated_at: datetime

    @field_serializer("amount_total", "total_invoiced")
    def _ser_amounts(self, v: Decimal):
        return float(v)


class CreditCardTransactionInstallmentGroupUpdate(BaseModel):
    description: str | None = None
    active: bool | None = None


class CreditCardSummary(BaseModel):
    total_limit: Decimal
    available_limit: Decimal
    transactions: list[CreditCardTransactionOut]
    current_invoice: CreditCardInvoiceOut | None = None
    next_invoices: list[CreditCardInvoiceOut] = []

    @field_serializer("total_limit", "available_limit")
    def _ser_limits(self, v: Decimal):
        return float(v)
