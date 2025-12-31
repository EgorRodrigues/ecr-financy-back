from fastapi import APIRouter
from fastapi import Request
from app.models.dashboard import DashboardOut
from app.repositories.dashboard import get_dashboard_data


router = APIRouter()


@router.get("/", response_model=DashboardOut)
def get_dashboard(request: Request, months: int = 6, recent_limit: int = 10):
    SessionLocal = request.app.state.postgres_session
    with SessionLocal() as session:
        return get_dashboard_data(session, months=months, recent_limit=recent_limit)
