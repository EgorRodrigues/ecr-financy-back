from fastapi import APIRouter
from fastapi import Request
from app.db.postgres import ping


router = APIRouter()


@router.get("/")
def health(request: Request):
    SessionLocal = getattr(request.app.state, "cassandra_session", None)
    if not SessionLocal:
        return {"status": "ok", "cassandra": False}
    with SessionLocal() as session:
        cassandra_ok = ping(session)
    return {"status": "ok", "cassandra": cassandra_ok}
