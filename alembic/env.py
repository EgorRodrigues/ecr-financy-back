import os
from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from app.db.postgres import metadata
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def _build_dsn() -> str:
    user = settings.postgres_username or "postgres"
    password = settings.postgres_password or "postgres"
    host = settings.postgres_host or "127.0.0.1"
    port = settings.postgres_port or 5432
    db = settings.postgres_database or "ecr_financy"
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


# set SQLAlchemy URL dynamically from app settings
config.set_main_option("sqlalchemy.url", _build_dsn())

# target metadata for 'autogenerate'
target_metadata = metadata


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
    connectable = create_engine(config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

