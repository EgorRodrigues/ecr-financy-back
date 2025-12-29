from typing import Literal
from pydantic import BaseModel


class ForecastItem(BaseModel):
    id: str
    month: str
    category: str
    amount: float
    status: Literal["projetado", "confirmado"]
    type: Literal["income", "expense"]
