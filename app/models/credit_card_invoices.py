from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_serializer


class CreditCardInvoiceCreate(BaseModel):
    account_id: UUID
    period_start: date
    period_end: date
    due_date: date
    amount: Decimal = Decimal("0")
    status: Literal["open", "closed", "paid"] = "open"


class CreditCardInvoiceUpdate(BaseModel):
    amount: Decimal | None = None
    status: Literal["open", "closed", "paid"] | None = None
    due_date: date | None = None
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None


class CreditCardInvoiceOut(BaseModel):
    id: UUID
    account_id: UUID
    period_start: date
    period_end: date
    due_date: date
    amount: Decimal
    status: Literal["open", "closed", "paid"]
    payment_date: date | None = None
    interest: Decimal | None = None
    fine: Decimal | None = None
    discount: Decimal | None = None
    total_paid: Decimal | None = None
    expense_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "interest", "fine", "discount", "total_paid")
    def _ser_amount(self, v: Decimal | None):
        if v is None:
            return None
        return float(v)
