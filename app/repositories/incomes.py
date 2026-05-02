import calendar
from datetime import datetime, UTC
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.incomes import Income, IncomeInstallmentGroup
from app.schemas.incomes import (
    IncomeCreate,
    IncomeInstallmentGroupOut,
    IncomeInstallmentGroupSummaryOut,
    IncomeInstallmentGroupUpdate,
    IncomeInstallmentGroupWithIncomesOut,
    IncomeInstallmentPlanCreate,
    IncomeOut,
    IncomeUpdate,
)


def _add_months(d, months: int):
    month_index = (d.month - 1) + months
    year = d.year + (month_index // 12)
    month = (month_index % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return d.replace(year=year, month=month, day=day)


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
    installment_group_id: str | None = None,
) -> list[IncomeOut]:
    query = select(Income).where(Income.transfer_id.is_(None))
    if account:
        query = query.where(Income.account_id == account)

    if status:
        query = query.where(Income.status == status)

    if installment_group_id:
        query = query.where(Income.installment_group_id == installment_group_id)

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


def create_installment_incomes(
    session: Session, payload: IncomeInstallmentPlanCreate
) -> IncomeInstallmentGroupWithIncomesOut:
    if payload.installments_total < 2:
        raise ValueError("installments_total must be >= 2")

    amount_total = payload.amount_total
    installments_total = payload.installments_total
    first_due_date = payload.first_due_date or payload.issue_date

    group = IncomeInstallmentGroup(
        id=uuid4(),
        description=payload.description,
        amount_total=amount_total,
        installments_total=installments_total,
        issue_date=payload.issue_date,
        first_due_date=first_due_date,
        account_id=payload.account_id,
        contact_id=payload.contact_id,
        active=payload.active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(group)

    per_installment = (amount_total / Decimal(installments_total)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    incomes: list[Income] = []
    for installment_number in range(1, installments_total + 1):
        due_date = _add_months(first_due_date, installment_number - 1)

        if installment_number < installments_total:
            installment_amount = per_installment
        else:
            installment_amount = amount_total - (per_installment * Decimal(installments_total - 1))

        income_data = {
            "amount": installment_amount,
            "status": payload.status,
            "issue_date": payload.issue_date,
            "due_date": due_date,
            "receipt_date": payload.receipt_date,
            "interest": payload.interest,
            "fine": payload.fine,
            "discount": payload.discount,
            "total_received": None,
            "category_id": payload.category_id,
            "subcategory_id": payload.subcategory_id,
            "cost_center_id": payload.cost_center_id,
            "contact_id": payload.contact_id,
            "description": payload.description,
            "document": payload.document,
            "receiving_method": payload.receiving_method,
            "account_id": payload.account_id,
            "competence": payload.competence,
            "project": payload.project,
            "tags": payload.tags,
            "notes": payload.notes,
            "transfer_id": None,
            "installment_group_id": group.id,
            "installment_number": installment_number,
            "installments_total": installments_total,
            "active": payload.active,
        }

        if payload.status == "recebido":
            amount = Decimal(str(income_data.get("amount") or 0))
            interest = Decimal(str(payload.interest or 0))
            fine = Decimal(str(payload.fine or 0))
            discount = Decimal(str(payload.discount or 0))
            income_data["total_received"] = amount + interest + fine - discount

        db_income = Income(
            **income_data,
            id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(db_income)
        incomes.append(db_income)

    session.commit()
    return IncomeInstallmentGroupWithIncomesOut(
        group=IncomeInstallmentGroupOut.model_validate(group),
        incomes=[IncomeOut.model_validate(i) for i in incomes],
    )


def get_installment_group(
    session: Session, gid: UUID
) -> IncomeInstallmentGroupWithIncomesOut | None:
    group = session.get(IncomeInstallmentGroup, gid)
    if not group:
        return None

    incomes = session.scalars(
        select(Income)
        .where(Income.installment_group_id == gid)
        .order_by(Income.installment_number.asc())
    ).all()

    return IncomeInstallmentGroupWithIncomesOut(
        group=IncomeInstallmentGroupOut.model_validate(group),
        incomes=[IncomeOut.model_validate(i) for i in incomes],
    )


def list_installment_groups(
    session: Session,
    limit: int = 200,
    account_id: str | None = None,
    contact_id: str | None = None,
    active: bool | None = None,
) -> list[IncomeInstallmentGroupSummaryOut]:
    received_sum = func.coalesce(
        func.sum(
            case(
                (Income.status == "recebido", func.coalesce(Income.total_received, Income.amount)),
                else_=0,
            )
        ),
        0,
    )

    incomes_count = func.coalesce(func.count(Income.id), 0)
    pending_count = func.coalesce(func.sum(case((Income.status == "pendente", 1), else_=0)), 0)
    received_count = func.coalesce(func.sum(case((Income.status == "recebido", 1), else_=0)), 0)
    canceled_count = func.coalesce(func.sum(case((Income.status == "cancelado", 1), else_=0)), 0)
    next_due_date = func.min(case((Income.status == "pendente", Income.due_date), else_=None))

    stmt = (
        select(
            IncomeInstallmentGroup,
            incomes_count.label("incomes_count"),
            pending_count.label("pending_count"),
            received_count.label("received_count"),
            canceled_count.label("canceled_count"),
            received_sum.label("total_received"),
            next_due_date.label("next_due_date"),
        )
        .outerjoin(Income, Income.installment_group_id == IncomeInstallmentGroup.id)
        .group_by(IncomeInstallmentGroup.id)
        .order_by(IncomeInstallmentGroup.created_at.desc())
        .limit(limit)
    )

    if account_id:
        stmt = stmt.where(IncomeInstallmentGroup.account_id == account_id)
    if contact_id:
        stmt = stmt.where(IncomeInstallmentGroup.contact_id == contact_id)
    if active is not None:
        stmt = stmt.where(IncomeInstallmentGroup.active == active)

    rows = session.execute(stmt).all()
    results: list[IncomeInstallmentGroupSummaryOut] = []
    for group, inc_count, pend_count, rec_count, c_count, total_received, n_due in rows:
        results.append(
            IncomeInstallmentGroupSummaryOut(
                id=group.id,
                description=group.description,
                amount_total=Decimal(str(group.amount_total or 0)),
                installments_total=group.installments_total,
                issue_date=group.issue_date,
                first_due_date=group.first_due_date,
                account_id=group.account_id,
                contact_id=group.contact_id,
                active=group.active,
                incomes_count=int(inc_count or 0),
                pending_count=int(pend_count or 0),
                received_count=int(rec_count or 0),
                canceled_count=int(c_count or 0),
                total_received=Decimal(str(total_received or 0)),
                next_due_date=n_due,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )
        )
    return results


def update_installment_group(
    session: Session, gid: UUID, payload: IncomeInstallmentGroupUpdate
) -> IncomeInstallmentGroupOut | None:
    group = session.get(IncomeInstallmentGroup, gid)
    if not group:
        return None

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(group, key, value)

    group.updated_at = datetime.now(UTC)
    session.commit()
    return IncomeInstallmentGroupOut.model_validate(group)


def cancel_installment_group(
    session: Session, gid: UUID
) -> IncomeInstallmentGroupWithIncomesOut | None:
    group = session.get(IncomeInstallmentGroup, gid)
    if not group:
        return None

    incomes = session.scalars(select(Income).where(Income.installment_group_id == gid)).all()
    for inc in incomes:
        if inc.status != "recebido":
            inc.status = "cancelado"
            inc.total_received = None
            inc.updated_at = datetime.now(UTC)

    group.updated_at = datetime.now(UTC)
    session.commit()
    return get_installment_group(session, gid)


def deactivate_installment_group(
    session: Session, gid: UUID
) -> IncomeInstallmentGroupWithIncomesOut | None:
    group = session.get(IncomeInstallmentGroup, gid)
    if not group:
        return None

    group.active = False
    group.updated_at = datetime.now(UTC)

    incomes = session.scalars(select(Income).where(Income.installment_group_id == gid)).all()
    for inc in incomes:
        inc.active = False
        inc.updated_at = datetime.now(UTC)

    session.commit()
    return get_installment_group(session, gid)
