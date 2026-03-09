from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OFXTransaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    fitid: str | None = None
    amount: float
    date: date
    memo: str
    type: str  # e.g., DEBIT, CREDIT
    bank_id: str | None = None
    account_id: str | None = None
    reconciled: bool = False
    reconciliation_date: date | None = None
    reconciled_by: str | None = None


class OFXImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transactions: list[OFXTransaction]
    account_id: str | None = None
    currency: str | None = None
    balance: float | None = None
    balance_date: date | None = None


class ReconciliationMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ofx_transaction_id: int
    matched_transaction_id: UUID | None = None
    match_type: Literal["exact", "partial", "none"] = "none"
    score: float = 0.0

class Income(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    total_received: float | None = None
    description: str
    due_date: date | None = None
    receipt_date: date | None = None
    reconciled: bool = False

class ReconciliationMatchInput(BaseModel):
    ofx_transaction_ids: list[int]
    transaction_ids: list[UUID]
    transaction_type: Literal["income", "expense"]

class Expense(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    total_paid: float | None = None
    description: str
    due_date: date | None = None
    payment_date: date | None = None
    reconciled: bool = False
