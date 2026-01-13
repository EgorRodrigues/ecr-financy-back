from datetime import date
from fastapi import APIRouter, Query, Depends
from typing import List
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.financial_forecast import ForecastItem
from app.repositories.financial_forecast import get_financial_forecast

router = APIRouter()


@router.get("/", response_model=List[ForecastItem])
def get_forecast(
    startDate: date = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: date = Query(..., description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_db)
):
    return get_financial_forecast(session, startDate, endDate)
