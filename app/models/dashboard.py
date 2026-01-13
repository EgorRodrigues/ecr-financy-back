from typing import Literal

from pydantic import BaseModel


class BigNumbers(BaseModel):
    balance: float
    approved: int
    pending: int
    failed: int


class MonthlyItem(BaseModel):
    month: str
    inflows: float
    outflows: float


class RecentTransaction(BaseModel):
    id: str
    date: str
    description: str
    amount: float
    status: Literal["pending", "paid", "received", "failed"]
    type: Literal["income", "expense"]


class DashboardOut(BaseModel):
    big_numbers: BigNumbers
    monthly: list[MonthlyItem]
    recent_transactions: list[RecentTransaction]
