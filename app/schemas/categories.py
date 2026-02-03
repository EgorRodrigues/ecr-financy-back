from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    active: bool
