from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.credit_card_transactions import (
    CreditCardSummary,
    CreditCardTransactionCreate,
    CreditCardTransactionInstallmentGroupOut,
    CreditCardTransactionInstallmentGroupSummaryOut,
    CreditCardTransactionInstallmentGroupUpdate,
    CreditCardTransactionInstallmentGroupWithTransactionsOut,
    CreditCardTransactionInstallmentPlanCreate,
    CreditCardTransactionOut,
    CreditCardTransactionUpdate,
    CreditCardTransactionTransfer,
)
from app.repositories.credit_card_transactions import (
    cancel_installment_group,
    create_credit_card_transaction,
    create_installment_transactions,
    deactivate_installment_group,
    delete_credit_card_transaction,
    get_credit_card_summary,
    get_credit_card_transaction,
    get_installment_group,
    list_credit_card_transactions,
    list_installment_groups,
    update_credit_card_transaction,
    transfer_transaction_invoice,
    update_installment_group,
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
    account_id: UUID | None = None,
    account_type: str | None = None,
    installment_group_id: str | None = None,
    session: Session = Depends(get_db),
):
    return list_credit_card_transactions(
        session,
        limit,
        account_id,
        account_type,
        installment_group_id=installment_group_id,
    )


@router.post("/installments", response_model=CreditCardTransactionInstallmentGroupWithTransactionsOut)
def create_installments(
    payload: CreditCardTransactionInstallmentPlanCreate, session: Session = Depends(get_db)
):
    try:
        return create_installment_transactions(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/installment-groups/{group_id}",
    response_model=CreditCardTransactionInstallmentGroupWithTransactionsOut,
)
def get_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = get_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.get(
    "/installment-groups", response_model=list[CreditCardTransactionInstallmentGroupSummaryOut]
)
def list_installment_groups_(
    limit: int = 200,
    account_id: UUID | None = None,
    active: bool | None = None,
    session: Session = Depends(get_db),
):
    return list_installment_groups(session, limit=limit, account_id=account_id, active=active)


@router.put(
    "/installment-groups/{group_id}", response_model=CreditCardTransactionInstallmentGroupOut
)
def update_installment_group_(
    group_id: UUID,
    payload: CreditCardTransactionInstallmentGroupUpdate,
    session: Session = Depends(get_db),
):
    item = update_installment_group(session, group_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.post(
    "/installment-groups/{group_id}/cancel",
    response_model=CreditCardTransactionInstallmentGroupWithTransactionsOut,
)
def cancel_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = cancel_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.post(
    "/installment-groups/{group_id}/deactivate",
    response_model=CreditCardTransactionInstallmentGroupWithTransactionsOut,
)
def deactivate_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = deactivate_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


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


@router.post("/{transaction_id}/transfer", response_model=CreditCardTransactionOut)
def transfer(
    transaction_id: UUID, payload: CreditCardTransactionTransfer, session: Session = Depends(get_db)
):
    try:
        item = transfer_transaction_invoice(session, transaction_id, payload.new_invoice_id)
        if not item:
            raise HTTPException(status_code=404, detail="Credit Card Transaction not found")
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{transaction_id}")
def delete(transaction_id: UUID, session: Session = Depends(get_db)):
    delete_credit_card_transaction(session, transaction_id)
    return {"deleted": True}
