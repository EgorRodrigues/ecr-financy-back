from urllib.parse import quote_plus
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import JSON, TypeDecorator

from app.core.config import settings


class CustomArray(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        return dialect.type_descriptor(JSON())


def UUID(as_uuid=True):
    return Uuid(as_uuid=as_uuid)


def ARRAY(item_type):
    return CustomArray(item_type)


_engine = None
metadata = MetaData()


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

            # Create tables in the new schema
            # We need to reflect the metadata to the new schema or just create all
            # Since metadata is bound to 'public' by default (None), we can try passing
            # schema to create_all but create_all usually uses the schema defined in Table args.
            # However, if we change search_path, create_all might work if we don't specify
            # schema in Table.
            # Our Tables don't have schema specified, so they default to default schema.

            # Set search path for this connection to create tables
            connection.execute(text(f"SET search_path TO {schema_name}"))
            metadata.create_all(connection)
            connection.commit()


def connect_postgres(settings_obj):
    # Backward compatibility if needed, or just initialize engine
    get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=_engine)


categories = Table(
    "categories",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("active", Boolean, nullable=False, server_default="true"),
)

subcategories = Table(
    "subcategories",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("category_id", UUID(as_uuid=True), nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("active", Boolean, nullable=False, server_default="true"),
)

cost_centers = Table(
    "cost_centers",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("active", Boolean, nullable=False, server_default="true"),
)

contacts = Table(
    "contacts",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("type", Text, nullable=False),
    Column("person_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("document", Text, nullable=True),
    Column("email", Text, nullable=True),
    Column("phone_e164", Text, nullable=True),
    Column("phone_local", Text, nullable=True),
    Column("address", Text, nullable=True),
    Column("notes", Text, nullable=True),
    Column("active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

accounts = Table(
    "accounts",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("agency", Text, nullable=True),
    Column("account", Text, nullable=True),
    Column("card_number", Text, nullable=True),
    Column("initial_balance", Numeric(18, 2), nullable=True),
    Column("available_limit", Numeric(18, 2), nullable=True),
    Column("closing_day", Integer, nullable=True),
    Column("due_day", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("active", Boolean, nullable=False, server_default="true"),
)

expenses = Table(
    "expenses",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("amount", Numeric(18, 2), nullable=False),
    Column("status", Text, nullable=False),
    Column("issue_date", Date, nullable=True),
    Column("due_date", Date, nullable=True),
    Column("payment_date", Date, nullable=True),
    Column("original_amount", Numeric(18, 2), nullable=True),
    Column("interest", Numeric(18, 2), nullable=True),
    Column("fine", Numeric(18, 2), nullable=True),
    Column("discount", Numeric(18, 2), nullable=True),
    Column("total_paid", Numeric(18, 2), nullable=True),
    Column("category_id", Text, nullable=True),
    Column("subcategory_id", Text, nullable=True),
    Column("cost_center_id", Text, nullable=True),
    Column("contact_id", Text, nullable=True),
    Column("description", Text, nullable=True),
    Column("document", Text, nullable=True),
    Column("payment_method", Text, nullable=True),
    Column("account", Text, nullable=True),
    Column("recurrence", Boolean, nullable=True),
    Column("competence", Text, nullable=True),
    Column("project", Text, nullable=True),
    Column("tags", ARRAY(Text), nullable=True),
    Column("notes", Text, nullable=True),
    Column("active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

incomes = Table(
    "incomes",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("amount", Numeric(18, 2), nullable=False),
    Column("status", Text, nullable=False),
    Column("issue_date", Date, nullable=True),
    Column("due_date", Date, nullable=True),
    Column("receipt_date", Date, nullable=True),
    Column("original_amount", Numeric(18, 2), nullable=True),
    Column("interest", Numeric(18, 2), nullable=True),
    Column("fine", Numeric(18, 2), nullable=True),
    Column("discount", Numeric(18, 2), nullable=True),
    Column("total_received", Numeric(18, 2), nullable=True),
    Column("category_id", Text, nullable=True),
    Column("subcategory_id", Text, nullable=True),
    Column("cost_center_id", Text, nullable=True),
    Column("contact_id", Text, nullable=True),
    Column("description", Text, nullable=True),
    Column("document", Text, nullable=True),
    Column("receiving_method", Text, nullable=True),
    Column("account", Text, nullable=True),
    Column("recurrence", Boolean, nullable=True),
    Column("competence", Text, nullable=True),
    Column("project", Text, nullable=True),
    Column("tags", ARRAY(Text), nullable=True),
    Column("notes", Text, nullable=True),
    Column("active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


credit_card_invoices = Table(
    "credit_card_invoices",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("account_id", UUID(as_uuid=True), nullable=False),
    Column("period_start", Date, nullable=False),
    Column("period_end", Date, nullable=False),
    Column("due_date", Date, nullable=False),
    Column("amount", Numeric(18, 2), nullable=False, default=0),
    Column("status", Text, nullable=False, default="open"),  # open, closed, paid
    Column("payment_date", Date, nullable=True),
    Column("interest", Numeric(18, 2), nullable=True),
    Column("fine", Numeric(18, 2), nullable=True),
    Column("discount", Numeric(18, 2), nullable=True),
    Column("total_paid", Numeric(18, 2), nullable=True),
    Column("expense_id", UUID(as_uuid=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "account_id", "period_start", "period_end", name="uq_credit_card_invoices_period"
    ),
)


credit_card_transactions = Table(
    "credit_card_transactions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("invoice_id", UUID(as_uuid=True), nullable=True),
    Column("amount", Numeric(18, 2), nullable=False),
    Column("status", Text, nullable=False),
    Column("issue_date", Date, nullable=True),
    Column("due_date", Date, nullable=True),
    Column("payment_date", Date, nullable=True),
    Column("original_amount", Numeric(18, 2), nullable=True),
    Column("interest", Numeric(18, 2), nullable=True),
    Column("fine", Numeric(18, 2), nullable=True),
    Column("discount", Numeric(18, 2), nullable=True),
    Column("total_paid", Numeric(18, 2), nullable=True),
    Column("category_id", Text, nullable=True),
    Column("subcategory_id", Text, nullable=True),
    Column("cost_center_id", Text, nullable=True),
    Column("contact_id", Text, nullable=True),
    Column("description", Text, nullable=True),
    Column("document", Text, nullable=True),
    Column("payment_method", Text, nullable=True),
    Column("account", Text, nullable=True),
    Column("recurrence", Boolean, nullable=True),
    Column("competence", Text, nullable=True),
    Column("project", Text, nullable=True),
    Column("tags", ARRAY(Text), nullable=True),
    Column("notes", Text, nullable=True),
    Column("active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


def close_postgres(session) -> None:
    if session:
        session.close()


def ping(session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
