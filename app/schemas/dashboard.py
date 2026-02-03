from datetime import date
from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class DashboardAccount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    balance: float
    bank: str | None = None

class MonthlySummary(BaseModel):
    month: str
    income: float
    expense: float

class RecentTransaction(BaseModel):
    id: UUID
    description: str | None
    amount: float
    date: date | None
    type: Literal["income", "expense"]

class DashboardResponse(BaseModel):
    accounts: List[DashboardAccount]
    monthlySummary: List[MonthlySummary]
    recentTransactions: List[RecentTransaction]
