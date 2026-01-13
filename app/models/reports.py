from pydantic import BaseModel


class ExpenseByCategory(BaseModel):
    category_id: str
    category_name: str
    total_amount: float

