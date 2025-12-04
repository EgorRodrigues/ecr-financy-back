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
        "INSERT INTO transactions (user_id, id, amount, description, created_at) VALUES (?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (data.user_id, tid, data.amount, data.description, created_at))
    return TransactionOut(user_id=data.user_id, id=tid, amount=data.amount, description=data.description, created_at=created_at)


def list_transactions(session, user_id: UUID, limit: int = 50) -> list[TransactionOut]:
    stmt = _prepare(
        session,
        "list_tx",
        "SELECT user_id, id, amount, description, created_at FROM transactions WHERE user_id = ? LIMIT ?",
    )
    rows = session.execute(stmt, (user_id, limit))
    return [
        TransactionOut(
            user_id=row.user_id,
            id=row.id,
            amount=row.amount,
            description=row.description,
            created_at=row.created_at,
        )
        for row in rows
    ]


def get_transaction(session, user_id: UUID, tid: UUID) -> TransactionOut | None:
    stmt = _prepare(
        session,
        "get_tx",
        "SELECT user_id, id, amount, description, created_at FROM transactions WHERE user_id = ? AND id = ?",
    )
    row = session.execute(stmt, (user_id, tid)).one()
    if not row:
        return None
    return TransactionOut(user_id=row.user_id, id=row.id, amount=row.amount, description=row.description, created_at=row.created_at)

