from datetime import date
from typing import List
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.reporting import ExpenseByCategoryAndAccount
from app.repositories.reports_accounts import get_expenses_by_category_account

router = APIRouter()


@router.get("/expenses-by-category-account", response_model=List[ExpenseByCategoryAndAccount])
def expenses_by_category_account(
    start_date: date | None = Query(None, description='Start date (YYYY-MM-DD)'),
    end_date: date | None = Query(None, description='End date (YYYY-MM-DD)'),
    session: Session = Depends(get_db),
):
    return get_expenses_by_category_account(session, start_date, end_date)

