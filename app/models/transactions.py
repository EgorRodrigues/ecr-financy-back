from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TransactionCreate(BaseModel):
    user_id: UUID
    amount: int
    description: Optional[str] = None


class TransactionOut(BaseModel):
    user_id: UUID
    id: UUID
    amount: int
    description: Optional[str] = None
    created_at: datetime

