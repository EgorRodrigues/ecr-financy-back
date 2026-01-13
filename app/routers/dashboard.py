from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.dashboard import DashboardOut
from app.repositories.dashboard import get_dashboard_data


router = APIRouter()


@router.get("/", response_model=DashboardOut)
def get_dashboard(
    months: int = 6,
    recent_limit: int = 10,
    session: Session = Depends(get_db)
):
    return get_dashboard_data(session, months=months, recent_limit=recent_limit)
