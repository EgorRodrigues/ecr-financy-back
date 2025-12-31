import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.postgres import metadata
from app.main import app


@pytest.fixture(scope="session")
def db_engine():
    # Use SQLite in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    metadata.create_all(bind=engine)

    yield engine

    metadata.drop_all(bind=engine)


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

    with TestClient(app) as c:
        yield c
