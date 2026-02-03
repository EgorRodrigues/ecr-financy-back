from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CostCenterCreate(BaseModel):
    name: str
    description: str | None = None
    active: bool = True


class CostCenterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class CostCenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    active: bool
