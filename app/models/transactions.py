from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TransactionCreate(BaseModel):
    amount: int
    description: Optional[str] = None
    active: bool = True


class TransactionOut(BaseModel):
    id: UUID
    amount: int
    description: Optional[str] = None
    created_at: datetime
    active: bool
