from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator


def _digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def _cpf_valid(s: str) -> bool:
    d = _digits(s)
    if len(d) != 11:
        return False
    if d == d[0] * 11:
        return False
    nums = [int(c) for c in d]
    s1 = sum(nums[i] * (10 - i) for i in range(9))
    r1 = (s1 * 10) % 11
    if r1 == 10:
        r1 = 0
    if r1 != nums[9]:
        return False
    s2 = sum(nums[i] * (11 - i) for i in range(10))
    r2 = (s2 * 10) % 11
    if r2 == 10:
        r2 = 0
    return r2 == nums[10]


def _cnpj_valid(s: str) -> bool:
    d = _digits(s)
    if len(d) != 14:
        return False
    if d == d[0] * 14:
        return False
    nums = [int(c) for c in d]
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(nums[i] * w1[i] for i in range(12))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    if d1 != nums[12]:
        return False
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s2 = sum(nums[i] * w2[i] for i in range(13))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    return d2 == nums[13]


class ContactCreate(BaseModel):
    type: Literal["customer", "supplier"]
    person_type: Literal["individual", "company"] | str
    name: str
    document: str | None = None
    email: str | None = None
    phone_e164: str | None = None
    phone_local: str | None = None
    address: str | None = None
    notes: str | None = None
    active: bool = True

    @field_validator("person_type")
    def normalize_person_type(cls, v):
        if isinstance(v, str):
            lv = v.strip().lower()
            if lv in {"fisica", "pf"}:
                return "individual"
            if lv in {"juridica", "pj"}:
                return "company"
        return v

    @model_validator(mode="after")
    def validate_document(self):
        if self.document is None:
            return self
        if self.person_type == "individual":
            if not _cpf_valid(self.document):
                raise ValueError("invalid CPF for individual")
        elif self.person_type == "company":
            if not _cnpj_valid(self.document):
                raise ValueError("invalid CNPJ for company")
        return self


class ContactUpdate(BaseModel):
    type: Literal["customer", "supplier"] | None = None
    person_type: Literal["individual", "company"] | str | None = None
    name: str | None = None
    document: str | None = None
    email: str | None = None
    phone_e164: str | None = None
    phone_local: str | None = None
    address: str | None = None
    notes: str | None = None
    active: bool | None = None

    @field_validator("person_type")
    def normalize_person_type(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            lv = v.strip().lower()
            if lv in {"fisica", "pf"}:
                return "individual"
            if lv in {"juridica", "pj"}:
                return "company"
        return v

    @model_validator(mode="after")
    def validate_document(self):
        if self.document is None:
            return self
        pt = self.person_type
        if pt is None:
            return self
        if pt == "individual":
            if not _cpf_valid(self.document):
                raise ValueError("invalid CPF for individual")
        elif pt == "company":
            if not _cnpj_valid(self.document):
                raise ValueError("invalid CNPJ for company")
        return self


class ContactOut(BaseModel):
    id: UUID
    type: Literal["customer", "supplier"]
    person_type: Literal["individual", "company"]
    name: str
    document: str | None = None
    email: str | None = None
    phone_e164: str | None = None
    phone_local: str | None = None
    address: str | None = None
    notes: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime
