from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

_engine = None


def get_engine():
    global _engine
    if _engine:
        return _engine

    user = quote_plus(settings.postgres_username or "postgres")
    password = quote_plus(settings.postgres_password or "postgres")
    db = quote_plus(settings.postgres_database or "ecr_financy")
    host = settings.postgres_host or "127.0.0.1"

    if host.startswith("/"):
        dsn = f"postgresql+psycopg://{user}:{password}@/{db}?host={host}"
    else:
        host = quote_plus(host)
        port = settings.postgres_port or 5432
        dsn = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    _engine = create_engine(dsn, pool_pre_ping=True)
    return _engine


def ensure_tenant_schema(schema_name: str):
    """
    Ensures that the tenant schema exists and all tables are created within it.
    """
    engine = get_engine()

    with engine.connect() as connection:
        # Check if schema exists
        schema_exists = connection.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                f"WHERE schema_name = '{schema_name}'"
            )
        ).scalar()

        if not schema_exists:
            # Create schema
            connection.execute(text(f"CREATE SCHEMA {schema_name}"))
            connection.commit()

            # Set search path for this connection to create tables
            connection.execute(text(f"SET search_path TO {schema_name}"))
            Base.metadata.create_all(connection)
            connection.commit()


def connect_postgres(settings_obj=None):
    # Backward compatibility if needed, or just initialize engine
    get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def close_postgres(session) -> None:
    if session:
        session.close()


def ping(session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
