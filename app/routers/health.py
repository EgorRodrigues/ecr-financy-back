from fastapi import APIRouter
from fastapi import Request
from app.db.postgres import ping


router = APIRouter()


@router.get("/")
def health(request: Request):
    session = getattr(request.app.state, "cassandra_session", None)
    cassandra_ok = bool(session) and ping(session)
    return {"status": "ok", "cassandra": cassandra_ok}
