from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

AccountType = Literal["bank", "credit_card", "wallet"]


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    agency: str | None = None
    account: str | None = None
    card_number: str | None = None
    initial_balance: float | None = None
    available_limit: float | None = None
    closing_day: int | None = None
    due_day: int | None = None
    active: bool = True

    @field_validator("closing_day", "due_day")
    @classmethod
    def validate_day(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 31):
            raise ValueError("Day must be between 1 and 31")
        return v


class AccountUpdate(BaseModel):
    name: str | None = None
    type: AccountType | None = None
    agency: str | None = None
    account: str | None = None
    card_number: str | None = None
    initial_balance: float | None = None
    available_limit: float | None = None
    closing_day: int | None = None
    due_day: int | None = None
    active: bool | None = None

    @field_validator("closing_day", "due_day")
    @classmethod
    def validate_day(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 31):
            raise ValueError("Day must be between 1 and 31")
        return v


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: AccountType
    agency: str | None = None
    account: str | None = None
    card_number: str | None = None
    initial_balance: float | None = None
    available_limit: float | None = None
    closing_day: int | None = None
    due_day: int | None = None
    created_at: datetime
    updated_at: datetime
    active: bool

    @field_validator("card_number")
    @classmethod
    def mask_card_number(cls, v: str | None) -> str | None:
        if v and len(v) >= 4:
            return f"**** **** **** {v[-4:]}"
        return v
