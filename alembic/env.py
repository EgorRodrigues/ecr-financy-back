from urllib.parse import quote_plus

from sqlalchemy import create_engine, pool

from alembic import context
from app.core.config import settings
from app.db.postgres import metadata

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
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool, future=True
    )
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
