from typing import Literal

from pydantic import BaseModel, ConfigDict


class ForecastItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    month: str
    category: str
    description: str
    amount: float
    status: Literal["projetado", "confirmado"]
    type: Literal["income", "expense"]
