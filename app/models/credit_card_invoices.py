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


class CreditCardInvoiceOut(BaseModel):
    id: UUID
    account_id: UUID
    period_start: date
    period_end: date
    due_date: date
    amount: Decimal
    status: Literal["open", "closed", "paid"]
    expense_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount")
    def _ser_amount(self, v: Decimal):
        return float(v)
