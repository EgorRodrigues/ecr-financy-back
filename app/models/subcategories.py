from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SubcategoryCreate(BaseModel):
    category_id: UUID
    name: str
    description: str | None = None
    active: bool = True


class SubcategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class SubcategoryOut(BaseModel):
    category_id: UUID
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    active: bool


class SubcategoryMove(BaseModel):
    new_category_id: UUID
