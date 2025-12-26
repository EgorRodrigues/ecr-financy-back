import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.postgres import connect_postgres, _engine
from app.core.config import settings

@pytest.fixture(scope="session")
def db_engine():
    # Initialize the global engine
    connect_postgres(settings)
    # Import the initialized engine
    from app.db.postgres import _engine
    yield _engine

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
