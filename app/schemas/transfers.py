from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class TransferCreate(BaseModel):
    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal
    date: date
    description: str | None = None
    category_id: str | None = None
    subcategory_id: str | None = None
    cost_center_id: str | None = None
    project: str | None = None
    competence: str | None = None
    tags: list[str] | None = None
