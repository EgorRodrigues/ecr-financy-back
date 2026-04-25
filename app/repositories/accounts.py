from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounts import Account
from app.schemas.accounts import AccountCreate, AccountOut, AccountUpdate


def create_account(session: Session, data: AccountCreate) -> AccountOut:
    db_account = Account(
        **data.model_dump(),
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_account)
    session.commit()
    return AccountOut.model_validate(db_account)


def list_accounts(
    session: Session, limit: int = 50, account: str | None = None, account_type: str | None = None
) -> list[AccountOut]:
    query = select(Account)
    if account:
        query = query.where(Account.account == account)

    if account_type:
        query = query.where(Account.type == account_type)

    query = query.order_by(Account.name.asc())

    rows = session.scalars(query.limit(limit)).all()
    return [AccountOut.model_validate(row) for row in rows]


def get_account(session: Session, aid: UUID) -> AccountOut | None:
    db_account = session.get(Account, aid)
    if not db_account:
        return None
    return AccountOut.model_validate(db_account)


def update_account(session: Session, aid: UUID, payload: AccountUpdate) -> AccountOut | None:
    db_account = session.get(Account, aid)
    if not db_account:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)

    db_account.updated_at = datetime.now(UTC)
    session.commit()
    return AccountOut.model_validate(db_account)


def delete_account(session: Session, aid: UUID):
    db_account = session.get(Account, aid)
    if db_account:
        session.delete(db_account)
        session.commit()
