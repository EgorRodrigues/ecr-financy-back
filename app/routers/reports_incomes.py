from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.reporting import IncomeByCustomer
from app.repositories.reports_incomes import get_incomes_by_customer

router = APIRouter()


@router.get("/incomes-by-customer", response_model=list[IncomeByCustomer])
def incomes_by_customer(
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_db),
):
    return get_incomes_by_customer(session, start_date, end_date)
