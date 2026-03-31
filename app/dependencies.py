from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import decode_token, verify_token
from app.db.postgres import ensure_tenant_schema, get_engine, sessionmaker


def get_current_user_payload(payload: dict = Depends(verify_token)) -> dict:
    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_db(
    request: Request, payload: dict = Depends(get_current_user_payload)
) -> Generator[Session, None, None]:
    app_state = getattr(request.app, "state", None)
    test_session_factory = getattr(app_state, "postgres_session", None) if app_state else None
    if test_session_factory:
        with test_session_factory() as s:
            yield s
        return

    user_id = payload.get("sub")
    schema_name = f"tenant_{user_id.replace('-', '')}"

    ensure_tenant_schema(schema_name)

    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        session.execute(text(f"SET search_path TO {schema_name}"))
        yield session
    finally:
        session.close()
