from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.expenses import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.repositories.expenses import (
    create_expense,
    delete_expense,
    get_expense,
    list_expenses,
    update_expense,
)

router = APIRouter()


@router.post("/", response_model=ExpenseOut)
def create(payload: ExpenseCreate, session: Session = Depends(get_db)):
    return create_expense(session, payload)


@router.get("/", response_model=list[ExpenseOut])
def list_(
    limit: int = 1000,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_db),
):
    return list_expenses(session, limit, account, account_type, status)


@router.get("/{expense_id}", response_model=ExpenseOut)
def get(expense_id: UUID, session: Session = Depends(get_db)):
    item = get_expense(session, expense_id)
    if not item:
        raise HTTPException(status_code=404, detail="Expense not found")
    return item


@router.put("/{expense_id}", response_model=ExpenseOut)
def update(expense_id: UUID, payload: ExpenseUpdate, session: Session = Depends(get_db)):
    item = update_expense(session, expense_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Expense not found")
    return item


@router.delete("/{expense_id}")
def delete(expense_id: UUID, session: Session = Depends(get_db)):
    delete_expense(session, expense_id)
    return {"deleted": True}
