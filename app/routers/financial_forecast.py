from datetime import date
from fastapi import APIRouter, Request, Query
from typing import List
from app.models.financial_forecast import ForecastItem
from app.repositories.financial_forecast import get_financial_forecast

router = APIRouter()


@router.get("/", response_model=List[ForecastItem])
def get_forecast(
    request: Request,
    startDate: date = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: date = Query(..., description="End date (YYYY-MM-DD)"),
):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        return get_financial_forecast(session, startDate, endDate)
