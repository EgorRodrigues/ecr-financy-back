from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.accounts import AccountCreate, AccountUpdate, AccountOut
from app.repositories.accounts import (
    create_account,
    list_accounts,
    get_account,
    update_account,
    delete_account,
)


router = APIRouter()


@router.post("/", response_model=AccountOut)
def create(request: Request, payload: AccountCreate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return create_account(session, payload)


@router.get("/", response_model=list[AccountOut])
def list_(
    request: Request, limit: int = 50, account: str | None = None, account_type: str | None = None
):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_accounts(session, limit, account, account_type)


@router.get("/{account_id}", response_model=AccountOut)
def get(request: Request, account_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = get_account(session, account_id)
        if not item:
            raise HTTPException(status_code=404, detail="Account not found")
        return item


@router.put("/{account_id}", response_model=AccountOut)
def update(request: Request, account_id: UUID, payload: AccountUpdate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = update_account(session, account_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Account not found")
        return item


@router.delete("/{account_id}")
def delete(request: Request, account_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        delete_account(session, account_id)
    return {"deleted": True}
