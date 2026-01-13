from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.credit_card_transactions import (
    CreditCardSummary,
    CreditCardTransactionCreate,
    CreditCardTransactionOut,
    CreditCardTransactionUpdate,
)
from app.repositories.credit_card_transactions import (
    create_credit_card_transaction,
    delete_credit_card_transaction,
    get_credit_card_summary,
    get_credit_card_transaction,
    list_credit_card_transactions,
    update_credit_card_transaction,
)

router = APIRouter()


@router.post("/", response_model=CreditCardTransactionOut)
def create(payload: CreditCardTransactionCreate, session: Session = Depends(get_db)):
    return create_credit_card_transaction(session, payload)


@router.get("/summary/{account_id}", response_model=CreditCardSummary)
def get_summary(account_id: UUID, session: Session = Depends(get_db)):
    summary = get_credit_card_summary(session, account_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Account not found")
    return summary


@router.get("/", response_model=list[CreditCardTransactionOut])
def list_(
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    session: Session = Depends(get_db),
):
    return list_credit_card_transactions(session, limit, account, account_type)


@router.get("/{transaction_id}", response_model=CreditCardTransactionOut)
def get(transaction_id: UUID, session: Session = Depends(get_db)):
    item = get_credit_card_transaction(session, transaction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Credit Card Transaction not found")
    return item


@router.put("/{transaction_id}", response_model=CreditCardTransactionOut)
def update(
    transaction_id: UUID, payload: CreditCardTransactionUpdate, session: Session = Depends(get_db)
):
    item = update_credit_card_transaction(session, transaction_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Credit Card Transaction not found")
    return item


@router.delete("/{transaction_id}")
def delete(transaction_id: UUID, session: Session = Depends(get_db)):
    delete_credit_card_transaction(session, transaction_id)
    return {"deleted": True}
