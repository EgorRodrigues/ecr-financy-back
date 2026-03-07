from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class OFXTransaction(BaseModel):
    id: str
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
    transactions: list[OFXTransaction]
    account_id: str | None = None
    currency: str | None = None
    balance: float | None = None
    balance_date: date | None = None


class ReconciliationMatch(BaseModel):
    ofx_transaction_id: str
    matched_transaction_id: UUID | None = None
    match_type: Literal["exact", "partial", "none"] = "none"
    score: float = 0.0

class Income(BaseModel):
    id: UUID
    amount: float
    description: str
    due_date: date | None = None
    reconciled: bool = False

    class Config:
        orm_mode = True

class ReconciliationMatchInput(BaseModel):
    ofx_transaction_id: int
    transaction_id: UUID
    transaction_type: Literal["income", "expense"]

class Expense(BaseModel):
    id: UUID
    amount: float
    description: str
    due_date: date | None = None
    reconciled: bool = False

    class Config:
        orm_mode = True
