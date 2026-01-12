from fastapi import APIRouter
from sqlalchemy.orm import sessionmaker
from app.db.postgres import ping, get_engine


router = APIRouter()


@router.get("/")
def health():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        postgres_ok = ping(session)
    except Exception:
        postgres_ok = False
    finally:
        session.close()
    return {"status": "ok", "postgres": postgres_ok}
