from typing import Optional, Literal
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime


AccountType = Literal["bank", "credit_card", "wallet"]


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    agency: Optional[str] = None
    account: Optional[str] = None
    card_number: Optional[str] = None
    initial_balance: Optional[float] = None
    available_limit: Optional[float] = None
    active: bool = True


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[AccountType] = None
    agency: Optional[str] = None
    account: Optional[str] = None
    card_number: Optional[str] = None
    initial_balance: Optional[float] = None
    available_limit: Optional[float] = None
    active: Optional[bool] = None


class AccountOut(BaseModel):
    id: UUID
    name: str
    type: AccountType
    agency: Optional[str] = None
    account: Optional[str] = None
    card_number: Optional[str] = None
    initial_balance: Optional[float] = None
    available_limit: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    active: bool

    @field_validator("card_number")
    @classmethod
    def mask_card_number(cls, v: str | None) -> str | None:
        if v and len(v) >= 4:
            return f"**** **** **** {v[-4:]}"
        return v
