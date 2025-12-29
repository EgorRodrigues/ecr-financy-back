from typing import Optional, Literal
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, field_serializer
from uuid import UUID


class CreditCardInvoiceCreate(BaseModel):
    account_id: UUID
    period_start: date
    period_end: date
    due_date: date
    amount: Decimal = Decimal("0")
    status: Literal["open", "closed", "paid"] = "open"


class CreditCardInvoiceUpdate(BaseModel):
    amount: Optional[Decimal] = None
    status: Optional[Literal["open", "closed", "paid"]] = None
    due_date: Optional[date] = None


class CreditCardInvoiceOut(BaseModel):
    id: UUID
    account_id: UUID
    period_start: date
    period_end: date
    due_date: date
    amount: Decimal
    status: Literal["open", "closed", "paid"]
    expense_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount")
    def _ser_amount(self, v: Decimal):
        return float(v)
