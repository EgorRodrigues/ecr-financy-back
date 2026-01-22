from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, field_serializer


class TransactionItem(BaseModel):
    date: date
    description: str | None
    amount: Decimal
    status: str
    type: str  # "income" or "expense" - useful for frontend but maybe not requested explicitly? User asked for "status". I'll add "type" just in case or stick to strict requirements.
    # Strict requirement: "data da tarnsação, descrição da transação, valor da transação, e o status"
    # "todos os campos do cotrato deverão seguir a mesma nomenclatura em ingles"
    # So: date, description, amount, status.

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal, _info):
        return float(v)


class PeriodSummary(BaseModel):
    total_income: float
    total_expense: float
    net_result: float

class BankStatementResponse(BaseModel):
    account_balance: float
    period_summary: PeriodSummary
    transactions: List[TransactionItem]
