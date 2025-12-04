from typing import Optional, Literal, List
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel
from uuid import UUID


class IncomeCreate(BaseModel):
    amount: Decimal
    status: Literal["pendente", "recebido", "cancelado"]
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    receipt_date: Optional[date] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    contact_id: Optional[str] = None
    description: Optional[str] = None
    document: Optional[str] = None
    receiving_method: Optional[Literal["pix", "boleto", "cartao", "transferencia", "dinheiro"]] = None
    account: Optional[str] = None
    recurrence: Optional[bool] = None
    competence: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    active: bool = True


class IncomeUpdate(BaseModel):
    amount: Optional[Decimal] = None
    status: Optional[Literal["pendente", "recebido", "cancelado"]] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    receipt_date: Optional[date] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    contact_id: Optional[str] = None
    description: Optional[str] = None
    document: Optional[str] = None
    receiving_method: Optional[Literal["pix", "boleto", "cartao", "transferencia", "dinheiro"]] = None
    account: Optional[str] = None
    recurrence: Optional[bool] = None
    competence: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class IncomeOut(BaseModel):
    id: UUID
    amount: Decimal
    status: Literal["pendente", "recebido", "cancelado"]
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    receipt_date: Optional[date] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    contact_id: Optional[str] = None
    description: Optional[str] = None
    document: Optional[str] = None
    receiving_method: Optional[Literal["pix", "boleto", "cartao", "transferencia", "dinheiro"]] = None
    account: Optional[str] = None
    recurrence: Optional[bool] = None
    competence: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime
