from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.transactions import TransactionCreate, TransactionOut


_prepared = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_transaction(session, data: TransactionCreate) -> TransactionOut:
    tid = uuid1()
    created_at = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_tx",
        "INSERT INTO transactions (id, amount, description, created_at, active) VALUES (?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (tid, data.amount, data.description, created_at, data.active))
    return TransactionOut(id=tid, amount=data.amount, description=data.description, created_at=created_at, active=data.active)


def list_transactions(session, limit: int = 50) -> list[TransactionOut]:
    stmt = _prepare(
        session,
        "list_tx",
        "SELECT id, amount, description, created_at, active FROM transactions LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
    return [
        TransactionOut(
            id=row.id,
            amount=row.amount,
            description=row.description,
            created_at=row.created_at,
            active=row.active,
        )
        for row in rows
    ]


def get_transaction(session, tid: UUID) -> TransactionOut | None:
    stmt = _prepare(
        session,
        "get_tx",
        "SELECT id, amount, description, created_at, active FROM transactions WHERE id = ?",
    )
    row = session.execute(stmt, (tid,)).one()
    if not row:
        return None
    return TransactionOut(id=row.id, amount=row.amount, description=row.description, created_at=row.created_at, active=row.active)
