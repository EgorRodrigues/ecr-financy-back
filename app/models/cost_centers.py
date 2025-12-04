from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CostCenterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True


class CostCenterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class CostCenterOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    active: bool
