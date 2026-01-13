from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.transactions import TransactionCreate, TransactionOut
from app.repositories.transactions import create_transaction, list_transactions, get_transaction


router = APIRouter()


@router.post("/", response_model=TransactionOut)
def create_tx(payload: TransactionCreate, session: Session = Depends(get_db)):
    return create_transaction(session, payload)


@router.get("/", response_model=list[TransactionOut])
def list_tx(limit: int = 50, session: Session = Depends(get_db)):
    return list_transactions(session, limit)


@router.get("/{tid}", response_model=TransactionOut)
def get_tx(tid: UUID, session: Session = Depends(get_db)):
    tx = get_transaction(session, tid)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx
