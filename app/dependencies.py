from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.security import verify_token
from app.db.postgres import get_engine, ensure_tenant_schema, sessionmaker

def get_db(token_payload: dict = Depends(verify_token)) -> Generator[Session, None, None]:
    """
    Dependency that yields a database session configured for the authenticated user's tenant.
    """
    # Extract user ID from token
    # Assuming 'sub' contains the user ID
    user_id = token_payload.get("sub")
    if not user_id:
        # Fallback or error if no user ID
        # For now, let's assume we might have a public schema or just fail
        raise ValueError("Token does not contain 'sub' claim")

    # Sanitize user_id to be safe for schema name
    # If user_id is UUID, replace hyphens. 
    # Example: tenant_1234567890
    schema_name = f"tenant_{user_id.replace('-', '')}"

    # Ensure schema exists (this might be cached in production)
    ensure_tenant_schema(schema_name)

    # Create session
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Set search path to the tenant's schema
        session.execute(text(f"SET search_path TO {schema_name}"))
        yield session
    finally:
        session.close()
