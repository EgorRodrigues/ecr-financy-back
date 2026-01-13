from typing import Generator
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt
from app.core.config import settings
from app.db.postgres import get_engine, ensure_tenant_schema, sessionmaker

def get_db(request: Request) -> Generator[Session, None, None]:
    app_state = getattr(request.app, "state", None)
    test_session_factory = getattr(app_state, "postgres_session", None) if app_state else None
    if test_session_factory:
        with test_session_factory() as s:
            yield s
        return

    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    schema_name = f"tenant_{user_id.replace('-', '')}"

    ensure_tenant_schema(schema_name)

    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        session.execute(text(f"SET search_path TO {schema_name}"))
        yield session
    finally:
        session.close()
