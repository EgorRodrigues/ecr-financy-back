from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.expenses import (
    ExpenseCreate,
    ExpenseInstallmentGroupWithExpensesOut,
    ExpenseInstallmentGroupOut,
    ExpenseInstallmentGroupSummaryOut,
    ExpenseInstallmentGroupUpdate,
    ExpenseInstallmentPlanCreate,
    ExpenseOut,
    ExpenseUpdate,
)
from app.repositories.expenses import (
    cancel_installment_group,
    create_expense,
    create_installment_expenses,
    deactivate_installment_group,
    delete_expense,
    get_installment_group,
    list_expenses,
    list_installment_groups,
    update_installment_group,
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
    installment_group_id: str | None = None,
    session: Session = Depends(get_db),
):
    return list_expenses(
        session,
        limit,
        account,
        account_type,
        status,
        installment_group_id=installment_group_id,
    )


@router.post("/installments", response_model=ExpenseInstallmentGroupWithExpensesOut)
def create_installments(payload: ExpenseInstallmentPlanCreate, session: Session = Depends(get_db)):
    try:
        return create_installment_expenses(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/installment-groups/{group_id}", response_model=ExpenseInstallmentGroupWithExpensesOut
)
def get_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = get_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.get("/installment-groups", response_model=list[ExpenseInstallmentGroupSummaryOut])
def list_installment_groups_(
    limit: int = 200,
    account_id: str | None = None,
    contact_id: str | None = None,
    active: bool | None = None,
    session: Session = Depends(get_db),
):
    return list_installment_groups(
        session, limit=limit, account_id=account_id, contact_id=contact_id, active=active
    )


@router.put("/installment-groups/{group_id}", response_model=ExpenseInstallmentGroupOut)
def update_installment_group_(
    group_id: UUID, payload: ExpenseInstallmentGroupUpdate, session: Session = Depends(get_db)
):
    item = update_installment_group(session, group_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.post(
    "/installment-groups/{group_id}/cancel", response_model=ExpenseInstallmentGroupWithExpensesOut
)
def cancel_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = cancel_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.post(
    "/installment-groups/{group_id}/deactivate",
    response_model=ExpenseInstallmentGroupWithExpensesOut,
)
def deactivate_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = deactivate_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.put("/{expense_id}", response_model=ExpenseOut)
def update(expense_id: UUID, payload: ExpenseUpdate, session: Session = Depends(get_db)):
    try:
        item = update_expense(session, expense_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Expense not found")
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{expense_id}")
def delete(expense_id: UUID, session: Session = Depends(get_db)):
    try:
        delete_expense(session, expense_id)
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
