from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.transactions import TransactionCreate, TransactionOut
from app.repositories.transactions import create_transaction, list_transactions, get_transaction


router = APIRouter()


@router.post("/", response_model=TransactionOut)
def create_tx(request: Request, payload: TransactionCreate):
    session = request.app.state.cassandra_session
    return create_transaction(session, payload)


@router.get("/{user_id}", response_model=list[TransactionOut])
def list_tx(request: Request, user_id: UUID, limit: int = 50):
    session = request.app.state.cassandra_session
    return list_transactions(session, user_id, limit)


@router.get("/{user_id}/{tid}", response_model=TransactionOut)
def get_tx(request: Request, user_id: UUID, tid: UUID):
    session = request.app.state.cassandra_session
    tx = get_transaction(session, user_id, tid)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

