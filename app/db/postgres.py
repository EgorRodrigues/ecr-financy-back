from sqlalchemy import create_engine, MetaData, Table, Column, Text, Boolean, Date, DateTime, Numeric, BigInteger, Integer, func, text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import sessionmaker, Session
from uuid import uuid4
from app.core.config import settings

class CustomArray(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        return dialect.type_descriptor(JSON())

def UUID(as_uuid=True):
    return Uuid(as_uuid=as_uuid)

def ARRAY(item_type):
    return CustomArray(item_type)

_engine = None
_SessionLocal = None
metadata = MetaData()

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
    Column("invoice_id", UUID(as_uuid=True), nullable=True),
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

transactions = Table(
    "transactions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("amount", BigInteger, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("active", Boolean, nullable=False, server_default="true"),
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
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("account_id", "period_start", "period_end", name="uq_credit_card_invoices_period"),
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


def _build_dsn() -> str:
    user = settings.postgres_username or "postgres"
    password = settings.postgres_password or "postgres"
    host = settings.postgres_host or "127.0.0.1"
    port = settings.postgres_port or 5432
    db = settings.postgres_database or "ecr_financy"
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


def connect_postgres(_settings) -> sessionmaker:
    global _engine, _SessionLocal
    if _engine is None:
        dsn = _build_dsn()
        _engine = create_engine(dsn, echo=False, future=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _SessionLocal


def close_postgres(session) -> None:
    if session:
        session.close()


def ping(session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
