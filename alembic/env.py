from urllib.parse import quote_plus
import os

from sqlalchemy import create_engine, pool, text

from alembic import context
from app.core.config import settings
from app.db.base import Base

# Import all models to ensure they are attached to Base.metadata
import app.models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def _build_dsn() -> str:
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

    return dsn.replace("%", "%%")


# set SQLAlchemy URL dynamically from app settings
config.set_main_option("sqlalchemy.url", _build_dsn())

# target metadata for 'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool, future=True
    )

    target_schema = os.environ.get("TARGET_SCHEMA")

    with connectable.connect() as connection:
        if target_schema:
            connection.execute(text(f"SET search_path TO {target_schema}"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table_schema=target_schema,
        )

        with context.begin_transaction():
            context.run_migrations()
        
        # Explicitly commit the connection
        connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
