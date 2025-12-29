from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.credit_card_transactions import (
    CreditCardTransactionCreate,
    CreditCardTransactionUpdate,
    CreditCardTransactionOut,
    CreditCardSummary,
)
from app.repositories.credit_card_transactions import (
    create_credit_card_transaction,
    list_credit_card_transactions,
    get_credit_card_transaction,
    update_credit_card_transaction,
    delete_credit_card_transaction,
    get_credit_card_summary,
)


router = APIRouter()


@router.post("/", response_model=CreditCardTransactionOut)
def create(request: Request, payload: CreditCardTransactionCreate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return create_credit_card_transaction(session, payload)


@router.get("/summary/{account_id}", response_model=CreditCardSummary)
def get_summary(request: Request, account_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        summary = get_credit_card_summary(session, account_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Account not found")
        return summary


@router.get("/", response_model=list[CreditCardTransactionOut])
def list_(
    request: Request, limit: int = 50, account: str | None = None, account_type: str | None = None
):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_credit_card_transactions(session, limit, account, account_type)


@router.get("/{transaction_id}", response_model=CreditCardTransactionOut)
def get(request: Request, transaction_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = get_credit_card_transaction(session, transaction_id)
        if not item:
            raise HTTPException(status_code=404, detail="Credit Card Transaction not found")
        return item


@router.put("/{transaction_id}", response_model=CreditCardTransactionOut)
def update(request: Request, transaction_id: UUID, payload: CreditCardTransactionUpdate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = update_credit_card_transaction(session, transaction_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Credit Card Transaction not found")
        return item


@router.delete("/{transaction_id}")
def delete(request: Request, transaction_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        delete_credit_card_transaction(session, transaction_id)
    return {"deleted": True}
