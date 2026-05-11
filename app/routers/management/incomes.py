from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.incomes import (
    IncomeCreate,
    IncomeInstallmentGroupOut,
    IncomeInstallmentGroupSummaryOut,
    IncomeInstallmentGroupUpdate,
    IncomeInstallmentGroupWithIncomesOut,
    IncomeInstallmentPlanCreate,
    IncomeOut,
    IncomeUpdate,
)
from app.repositories.incomes import (
    cancel_installment_group,
    create_income,
    create_installment_incomes,
    deactivate_installment_group,
    delete_income,
    get_installment_group,
    list_incomes,
    list_installment_groups,
    update_installment_group,
    update_income,
)

router = APIRouter()


@router.post("/", response_model=IncomeOut)
def create(payload: IncomeCreate, session: Session = Depends(get_db)):
    return create_income(session, payload)


@router.get("/", response_model=list[IncomeOut])
def list_(
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
    installment_group_id: str | None = None,
    session: Session = Depends(get_db),
):
    return list_incomes(
        session,
        limit,
        account,
        account_type,
        status,
        installment_group_id=installment_group_id,
    )


@router.post("/installments", response_model=IncomeInstallmentGroupWithIncomesOut)
def create_installments(payload: IncomeInstallmentPlanCreate, session: Session = Depends(get_db)):
    try:
        return create_installment_incomes(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/installment-groups/{group_id}", response_model=IncomeInstallmentGroupWithIncomesOut
)
def get_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = get_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.get("/installment-groups", response_model=list[IncomeInstallmentGroupSummaryOut])
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


@router.put("/installment-groups/{group_id}", response_model=IncomeInstallmentGroupOut)
def update_installment_group_(
    group_id: UUID, payload: IncomeInstallmentGroupUpdate, session: Session = Depends(get_db)
):
    item = update_installment_group(session, group_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.post(
    "/installment-groups/{group_id}/cancel", response_model=IncomeInstallmentGroupWithIncomesOut
)
def cancel_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = cancel_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.post(
    "/installment-groups/{group_id}/deactivate",
    response_model=IncomeInstallmentGroupWithIncomesOut,
)
def deactivate_installment_group_(group_id: UUID, session: Session = Depends(get_db)):
    item = deactivate_installment_group(session, group_id)
    if not item:
        raise HTTPException(status_code=404, detail="Installment group not found")
    return item


@router.put("/{income_id}", response_model=IncomeOut)
def update(income_id: UUID, payload: IncomeUpdate, session: Session = Depends(get_db)):
    item = update_income(session, income_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Income not found")
    return item


@router.delete("/{income_id}")
def delete(income_id: UUID, session: Session = Depends(get_db)):
    delete_income(session, income_id)
    return {"deleted": True}
