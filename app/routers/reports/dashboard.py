from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.dashboard import DashboardResponse
from app.repositories.dashboard import get_dashboard_data

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
def get_dashboard(session: Session = Depends(get_db)):
    return get_dashboard_data(session)
