from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.incomes import IncomeCreate, IncomeOut, IncomeUpdate
from app.repositories.incomes import (
    create_income,
    delete_income,
    list_incomes,
    update_income,
)

router = APIRouter()


@router.post("/", response_model=IncomeOut)
def create(payload: IncomeCreate, session: Session = Depends(get_db)):
    return create_income(session, payload)


@router.get("/", response_model=list[IncomeOut])
def list_(
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_db),
):
    return list_incomes(session, limit, account, account_type, status)


@router.put("/{income_id}", response_model=IncomeOut)
def update(income_id: UUID, payload: IncomeUpdate, session: Session = Depends(get_db)):
    item = update_income(session, income_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Income not found")
    return item


@router.delete("/{income_id}")
def delete(income_id: UUID, session: Session = Depends(get_db)):
    delete_income(session, income_id)
    return {"deleted": True}
