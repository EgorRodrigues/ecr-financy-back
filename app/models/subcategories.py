from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class SubcategoryCreate(BaseModel):
    user_id: UUID
    category_id: UUID
    name: str
    description: Optional[str] = None


class SubcategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SubcategoryOut(BaseModel):
    user_id: UUID
    category_id: UUID
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

