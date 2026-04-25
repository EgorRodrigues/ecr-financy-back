import sqlite3
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.dependencies import get_current_user_payload


@event.listens_for(Engine, "connect")
def _connect(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        def to_char(value, fmt):
            if value is None:
                return None
            try:
                # Handle potential formats
                if " " in value:
                    dt = datetime.strptime(value.split(".")[0], "%Y-%m-%d %H:%M:%S")
                else:
                    dt = datetime.strptime(value, "%Y-%m-%d")
            except (ValueError, TypeError):
                return value
            
            if fmt == 'Mon':
                return dt.strftime('%b')
            elif fmt == 'YYYY-MM':
                return dt.strftime('%Y-%m')
            return str(value)
            
        dbapi_connection.create_function("to_char", 2, to_char)



@pytest.fixture(scope="session")
def db_engine():
    # Use SQLite in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def session(db_engine):
    """
    Creates a new database session for a test.
    Rolls back any changes at the end of the test.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(session):
    """
    Fixture for FastAPI TestClient with overridden database session.
    """

    class MockSessionLocal:
        def __call__(self):
            return self

        def __enter__(self):
            return session

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    app.state.postgres_session = MockSessionLocal()

    # Override authentication
    def override_get_current_user_payload():
        return {"sub": "test-user-id"}

    app.dependency_overrides[get_current_user_payload] = override_get_current_user_payload

    with TestClient(app) as c:
        yield c
    
    # Clean up overrides
    app.dependency_overrides.clear()
