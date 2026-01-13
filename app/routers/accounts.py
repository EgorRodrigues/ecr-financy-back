from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.accounts import AccountCreate, AccountUpdate, AccountOut
from app.dependencies import get_db
from app.repositories.accounts import (
    create_account,
    list_accounts,
    get_account,
    update_account,
    delete_account,
)


router = APIRouter()


@router.post("/", response_model=AccountOut)
def create(payload: AccountCreate, session: Session = Depends(get_db)):
    return create_account(session, payload)


@router.get("/", response_model=list[AccountOut])
def list_(
    limit: int = 50, 
    account: str | None = None, 
    account_type: str | None = None,
    session: Session = Depends(get_db)
):
    return list_accounts(session, limit, account, account_type)


@router.get("/{account_id}", response_model=AccountOut)
def get(account_id: UUID, session: Session = Depends(get_db)):
    item = get_account(session, account_id)
    if not item:
        raise HTTPException(status_code=404, detail="Account not found")
    return item


@router.put("/{account_id}", response_model=AccountOut)
def update(account_id: UUID, payload: AccountUpdate, session: Session = Depends(get_db)):
    item = update_account(session, account_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Account not found")
    return item


@router.delete("/{account_id}")
def delete(account_id: UUID, session: Session = Depends(get_db)):
    delete_account(session, account_id)
    return {"deleted": True}
