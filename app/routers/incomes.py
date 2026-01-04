from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.incomes import IncomeCreate, IncomeUpdate, IncomeOut
from app.repositories.incomes import (
    create_income,
    list_incomes,
    get_income,
    update_income,
    delete_income,
)


router = APIRouter()


@router.post("/", response_model=IncomeOut)
def create(request: Request, payload: IncomeCreate):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        return create_income(session, payload)


@router.get("/", response_model=list[IncomeOut])
def list_(
    request: Request,
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        return list_incomes(session, limit, account, account_type, status)


@router.get("/{income_id}", response_model=IncomeOut)
def get(request: Request, income_id: UUID):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        item = get_income(session, income_id)
        if not item:
            raise HTTPException(status_code=404, detail="Income not found")
        return item


@router.put("/{income_id}", response_model=IncomeOut)
def update(request: Request, income_id: UUID, payload: IncomeUpdate):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        item = update_income(session, income_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Income not found")
        return item


@router.delete("/{income_id}")
def delete(request: Request, income_id: UUID):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        delete_income(session, income_id)
    return {"deleted": True}
