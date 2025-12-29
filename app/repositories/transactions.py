from uuid import UUID, uuid4
from sqlalchemy import select, insert
from app.models.transactions import TransactionCreate, TransactionOut
from app.db.postgres import transactions


def create_transaction(session, data: TransactionCreate) -> TransactionOut:
    tid = uuid4()
    session.execute(
        insert(transactions).values(
            id=tid, amount=data.amount, description=data.description, active=data.active
        )
    )
    session.commit()
    row = session.execute(
        select(
            transactions.c.id,
            transactions.c.amount,
            transactions.c.description,
            transactions.c.created_at,
            transactions.c.active,
        ).where(transactions.c.id == tid)
    ).one()
    return TransactionOut(
        id=row.id,
        amount=int(row.amount),
        description=row.description,
        created_at=row.created_at,
        active=row.active,
    )


def list_transactions(session, limit: int = 50) -> list[TransactionOut]:
    rows = session.execute(
        select(
            transactions.c.id,
            transactions.c.amount,
            transactions.c.description,
            transactions.c.created_at,
            transactions.c.active,
        ).limit(limit)
    ).all()
    return [
        TransactionOut(
            id=row.id,
            amount=int(row.amount),
            description=row.description,
            created_at=row.created_at,
            active=row.active,
        )
        for row in rows
    ]


def get_transaction(session, tid: UUID) -> TransactionOut | None:
    row = session.execute(
        select(
            transactions.c.id,
            transactions.c.amount,
            transactions.c.description,
            transactions.c.created_at,
            transactions.c.active,
        ).where(transactions.c.id == tid)
    ).one_or_none()
    if not row:
        return None
    return TransactionOut(
        id=row.id,
        amount=int(row.amount),
        description=row.description,
        created_at=row.created_at,
        active=row.active,
    )
