from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.expenses import ExpenseCreate, ExpenseUpdate, ExpenseOut
from app.repositories.expenses import (
    create_expense,
    list_expenses,
    get_expense,
    update_expense,
    delete_expense,
)


router = APIRouter()


@router.post("/", response_model=ExpenseOut)
def create(request: Request, payload: ExpenseCreate):
    session = request.app.state.cassandra_session
    return create_expense(session, payload)


@router.get("/", response_model=list[ExpenseOut])
def list_(request: Request, limit: int = 50):
    session = request.app.state.cassandra_session
    return list_expenses(session, limit)


@router.get("/{expense_id}", response_model=ExpenseOut)
def get(request: Request, expense_id: UUID):
    session = request.app.state.cassandra_session
    item = get_expense(session, expense_id)
    if not item:
        raise HTTPException(status_code=404, detail="Expense not found")
    return item


@router.put("/{expense_id}", response_model=ExpenseOut)
def update(request: Request, expense_id: UUID, payload: ExpenseUpdate):
    session = request.app.state.cassandra_session
    item = update_expense(session, expense_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Expense not found")
    return item


@router.delete("/{expense_id}")
def delete(request: Request, expense_id: UUID):
    session = request.app.state.cassandra_session
    delete_expense(session, expense_id)
    return {"deleted": True}
