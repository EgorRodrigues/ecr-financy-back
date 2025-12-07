from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.accounts import AccountCreate, AccountUpdate, AccountOut


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_account(session, data: AccountCreate) -> AccountOut:
    aid = uuid1()
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_account",
        "INSERT INTO accounts (id, name, type, agency, account, card_number, initial_balance, available_limit, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    )
    session.execute(
        stmt,
        (
            aid,
            data.name,
            data.type,
            data.agency,
            data.account,
            data.card_number,
            data.initial_balance,
            data.available_limit,
            now,
            now,
            data.active,
        ),
    )
    return AccountOut(
        id=aid,
        name=data.name,
        type=data.type,
        agency=data.agency,
        account=data.account,
        card_number=data.card_number,
        initial_balance=data.initial_balance,
        available_limit=data.available_limit,
        created_at=now,
        updated_at=now,
        active=data.active,
    )


def list_accounts(session, limit: int = 50) -> list[AccountOut]:
    stmt = _prepare(
        session,
        "list_accounts",
        "SELECT id, name, type, agency, account, card_number, initial_balance, available_limit, created_at, updated_at, active FROM accounts LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
    return [
        AccountOut(
            id=row.id,
            name=row.name,
            type=row.type,
            agency=row.agency,
            account=row.account,
            card_number=row.card_number,
            initial_balance=row.initial_balance,
            available_limit=row.available_limit,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in rows
    ]


def get_account(session, aid: UUID) -> AccountOut | None:
    stmt = _prepare(
        session,
        "get_account",
        "SELECT id, name, type, agency, account, card_number, initial_balance, available_limit, created_at, updated_at, active FROM accounts WHERE id = ?",
    )
    row = session.execute(stmt, (aid,)).one()
    if not row:
        return None
    return AccountOut(
        id=row.id,
        name=row.name,
        type=row.type,
        agency=row.agency,
        account=row.account,
        card_number=row.card_number,
        initial_balance=row.initial_balance,
        available_limit=row.available_limit,
        created_at=row.created_at,
        updated_at=row.updated_at,
        active=row.active,
    )


def update_account(session, aid: UUID, data: AccountUpdate) -> AccountOut | None:
    current = get_account(session, aid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_type = data.type if data.type is not None else current.type
    new_agency = data.agency if data.agency is not None else current.agency
    new_account = data.account if data.account is not None else current.account
    new_card = data.card_number if data.card_number is not None else current.card_number
    new_initial = data.initial_balance if data.initial_balance is not None else current.initial_balance
    new_limit = data.available_limit if data.available_limit is not None else current.available_limit
    new_active = data.active if data.active is not None else current.active
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_account",
        "UPDATE accounts SET name = ?, type = ?, agency = ?, account = ?, card_number = ?, initial_balance = ?, available_limit = ?, active = ?, updated_at = ? WHERE id = ?",
    )
    session.execute(
        stmt,
        (
            new_name,
            new_type,
            new_agency,
            new_account,
            new_card,
            new_initial,
            new_limit,
            new_active,
            now,
            aid,
        ),
    )
    return AccountOut(
        id=aid,
        name=new_name,
        type=new_type,
        agency=new_agency,
        account=new_account,
        card_number=new_card,
        initial_balance=new_initial,
        available_limit=new_limit,
        created_at=current.created_at,
        updated_at=now,
        active=new_active,
    )


def delete_account(session, aid: UUID) -> bool:
    stmt = _prepare(session, "delete_account", "DELETE FROM accounts WHERE id = ?")
    session.execute(stmt, (aid,))
    return True
