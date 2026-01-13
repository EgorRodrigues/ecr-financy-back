from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    amount: int
    description: str | None = None
    active: bool = True


class TransactionOut(BaseModel):
    id: UUID
    amount: int
    description: str | None = None
    created_at: datetime
    active: bool
