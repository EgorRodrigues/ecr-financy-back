from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CostCenterCreate(BaseModel):
    user_id: UUID
    name: str
    description: Optional[str] = None


class CostCenterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CostCenterOut(BaseModel):
    user_id: UUID
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

