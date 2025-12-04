from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CategoryCreate(BaseModel):
    user_id: UUID
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryOut(BaseModel):
    user_id: UUID
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

