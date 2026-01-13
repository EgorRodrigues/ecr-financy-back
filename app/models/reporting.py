from pydantic import BaseModel


class ExpenseByCategoryAndAccount(BaseModel):
    category_id: str
    category_name: str
    account_id: str
    account_name: str
    total_amount: float


class IncomeByCustomer(BaseModel):
    contact_id: str
    contact_name: str
    total_amount: float
