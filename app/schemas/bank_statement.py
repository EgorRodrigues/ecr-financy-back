from typing import Literal

from pydantic import BaseModel

from app.models.expenses import ExpenseOut
from app.models.incomes import IncomeOut


class IncomeStatementItem(IncomeOut):
    type: Literal["income"] = "income"
    category_name: str | None = None


class ExpenseStatementItem(ExpenseOut):
    type: Literal["expense"] = "expense"
    category_name: str | None = None


class PeriodSummary(BaseModel):
    total_income: float
    total_expense: float
    net_result: float


class BankStatementResponse(BaseModel):
    account_balance: float
    period_summary: PeriodSummary
    transactions: list[IncomeStatementItem | ExpenseStatementItem]
