from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.reports import ExpenseByCategory
from app.repositories.reports import get_expenses_by_category

router = APIRouter()


@router.get("/expenses-by-category", response_model=list[ExpenseByCategory])
def expenses_by_category(
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_db),
):
    return get_expenses_by_category(session, start_date, end_date)
