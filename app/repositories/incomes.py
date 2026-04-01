from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incomes import Income
from app.schemas.incomes import IncomeCreate, IncomeOut, IncomeUpdate


def create_income(session: Session, data: IncomeCreate) -> IncomeOut:
    income_data = data.model_dump()
    
    # Calculate total_received if status is "recebido"
    if income_data.get("status") == "recebido":
        amount = income_data.get("amount") or 0
        interest = income_data.get("interest") or 0
        fine = income_data.get("fine") or 0
        discount = income_data.get("discount") or 0
        income_data["total_received"] = amount + interest + fine - discount

    db_income = Income(
        **income_data,
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_income)
    session.commit()
    return IncomeOut.model_validate(db_income)


def list_incomes(
    session: Session,
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
) -> list[IncomeOut]:
    query = select(Income)
    if account:
        query = query.where(Income.account_id == account)

    if status:
        query = query.where(Income.status == status)

    query = query.order_by(Income.issue_date.desc()).limit(limit)
    rows = session.scalars(query).all()
    return [IncomeOut.model_validate(row) for row in rows]


def get_income(session: Session, iid: UUID) -> IncomeOut | None:
    db_income = session.get(Income, iid)
    if not db_income:
        return None
    return IncomeOut.model_validate(db_income)


def update_income(session: Session, iid: UUID, data: IncomeUpdate) -> IncomeOut | None:
    db_income = session.get(Income, iid)
    if not db_income:
        return None

    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_income, key, value)

    # Calculate total_received if status is "recebido"
    if db_income.status == "recebido":
        amount = db_income.amount or 0
        interest = db_income.interest or 0
        fine = db_income.fine or 0
        discount = db_income.discount or 0
        db_income.total_received = amount + interest + fine - discount

    db_income.updated_at = datetime.now(UTC)
    session.commit()
    return IncomeOut.model_validate(db_income)


def delete_income(session: Session, iid: UUID):
    db_income = session.get(Income, iid)
    if db_income:
        session.delete(db_income)
        session.commit()
