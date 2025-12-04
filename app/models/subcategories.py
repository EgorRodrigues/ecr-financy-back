from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class SubcategoryCreate(BaseModel):
    category_id: UUID
    name: str
    description: Optional[str] = None
    active: bool = True


class SubcategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class SubcategoryOut(BaseModel):
    category_id: UUID
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    active: bool
