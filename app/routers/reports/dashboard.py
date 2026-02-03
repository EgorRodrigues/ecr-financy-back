from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.dashboard import DashboardResponse
from app.repositories.dashboard import DashboardRepository

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
def get_dashboard(session: Session = Depends(get_db)):
    repository = DashboardRepository(session)
    return repository.get_dashboard_data()
