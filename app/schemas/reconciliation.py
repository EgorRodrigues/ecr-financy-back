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
