from fastapi import APIRouter
from fastapi import Request
from app.db.postgres import ping


router = APIRouter()


@router.get("/")
def health(request: Request):
    SessionLocal = getattr(request.app.state, "postgres_session", None)
    if not SessionLocal:
        return {"status": "ok", "postgres": False}
    with SessionLocal() as session:
        postgres_ok = ping(session)
    return {"status": "ok", "postgres": postgres_ok}
