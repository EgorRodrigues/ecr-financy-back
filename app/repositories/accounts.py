from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import select, insert, update, delete
from app.models.accounts import AccountCreate, AccountUpdate, AccountOut
from app.db.postgres import accounts


def create_account(session, data: AccountCreate) -> AccountOut:
    aid = uuid4()
    now = datetime.now(timezone.utc)
    session.execute(
        insert(accounts).values(
            id=aid,
            name=data.name,
            type=data.type,
            agency=data.agency,
            account=data.account,
            card_number=data.card_number,
            initial_balance=data.initial_balance,
            available_limit=data.available_limit,
            closing_day=data.closing_day,
            due_day=data.due_day,
            created_at=now,
            updated_at=now,
            active=data.active,
        )
    )
    session.commit()
    return AccountOut(
        id=aid,
        name=data.name,
        type=data.type,
        agency=data.agency,
        account=data.account,
        card_number=data.card_number,
        initial_balance=data.initial_balance,
        available_limit=data.available_limit,
        closing_day=data.closing_day,
        due_day=data.due_day,
        created_at=now,
        updated_at=now,
        active=data.active,
    )


def list_accounts(session, limit: int = 50, account: str | None = None, account_type: str | None = None) -> list[AccountOut]:
    query = select(
        accounts.c.id,
        accounts.c.name,
        accounts.c.type,
        accounts.c.agency,
        accounts.c.account,
        accounts.c.card_number,
        accounts.c.initial_balance,
        accounts.c.available_limit,
        accounts.c.closing_day,
        accounts.c.due_day,
        accounts.c.created_at,
        accounts.c.updated_at,
        accounts.c.active,
    )
    if account:
        query = query.where(accounts.c.account == account)
    
    if account_type:
        query = query.where(accounts.c.type == account_type)
    
    rows = session.execute(query.limit(limit)).all()
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
            closing_day=row.closing_day,
            due_day=row.due_day,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in rows
    ]


def get_account(session, aid: UUID) -> AccountOut | None:
    row = session.execute(
        select(
            accounts.c.id,
            accounts.c.name,
            accounts.c.type,
            accounts.c.agency,
            accounts.c.account,
            accounts.c.card_number,
            accounts.c.initial_balance,
            accounts.c.available_limit,
            accounts.c.closing_day,
            accounts.c.due_day,
            accounts.c.created_at,
            accounts.c.updated_at,
            accounts.c.active,
        ).where(accounts.c.id == aid)
    ).one_or_none()
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
        closing_day=row.closing_day,
        due_day=row.due_day,
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
    new_closing_day = data.closing_day if data.closing_day is not None else current.closing_day
    new_due_day = data.due_day if data.due_day is not None else current.due_day
    new_active = data.active if data.active is not None else current.active
    now = datetime.now(timezone.utc)
    session.execute(
        update(accounts)
        .where(accounts.c.id == aid)
        .values(
            name=new_name,
            type=new_type,
            agency=new_agency,
            account=new_account,
            card_number=new_card,
            initial_balance=new_initial,
            available_limit=new_limit,
            closing_day=new_closing_day,
            due_day=new_due_day,
            active=new_active,
            updated_at=now,
        )
    )
    session.commit()
    return AccountOut(
        id=aid,
        name=new_name,
        type=new_type,
        agency=new_agency,
        account=new_account,
        card_number=new_card,
        initial_balance=new_initial,
        available_limit=new_limit,
        closing_day=new_closing_day,
        due_day=new_due_day,
        created_at=current.created_at,
        updated_at=now,
        active=new_active,
    )


def delete_account(session, aid: UUID) -> bool:
    session.execute(delete(accounts).where(accounts.c.id == aid))
    session.commit()
    return True
