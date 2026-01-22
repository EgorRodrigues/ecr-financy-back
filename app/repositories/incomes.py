from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Text, delete, func, insert, select, update

from app.db.postgres import accounts, incomes
from app.models.incomes import IncomeCreate, IncomeOut, IncomeUpdate


def _to_date(value):
    return value.date() if hasattr(value, "date") else value


def create_income(session, data: IncomeCreate) -> IncomeOut:
    iid = uuid4()
    now = datetime.now(UTC)
    session.execute(
        insert(incomes).values(
            id=iid,
            amount=data.amount,
            status=data.status,
            issue_date=data.issue_date,
            due_date=data.due_date,
            receipt_date=data.receipt_date,
            original_amount=data.original_amount,
            interest=data.interest,
            fine=data.fine,
            discount=data.discount,
            total_received=data.total_received,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            cost_center_id=data.cost_center_id,
            contact_id=data.contact_id,
            description=data.description,
            document=data.document,
            receiving_method=data.receiving_method,
            account=str(data.account) if data.account else None,
            recurrence=data.recurrence,
            competence=data.competence,
            project=data.project,
            tags=data.tags,
            notes=data.notes,
            active=data.active,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()
    return IncomeOut(
        id=iid,
        amount=data.amount,
        status=data.status,
        issue_date=data.issue_date,
        due_date=data.due_date,
        receipt_date=data.receipt_date,
        original_amount=data.original_amount,
        interest=data.interest,
        fine=data.fine,
        discount=data.discount,
        total_received=data.total_received,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        cost_center_id=data.cost_center_id,
        contact_id=data.contact_id,
        description=data.description,
        document=data.document,
        receiving_method=data.receiving_method,
        account=data.account,
        recurrence=data.recurrence,
        competence=data.competence,
        project=data.project,
        tags=data.tags,
        notes=data.notes,
        active=data.active,
        created_at=now,
        updated_at=now,
    )


def list_incomes(
    session,
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
) -> list[IncomeOut]:
    query = select(
        incomes.c.id,
        incomes.c.amount,
        incomes.c.status,
        incomes.c.issue_date,
        incomes.c.due_date,
        incomes.c.receipt_date,
        incomes.c.original_amount,
        incomes.c.interest,
        incomes.c.fine,
        incomes.c.discount,
        incomes.c.total_received,
        incomes.c.category_id,
        incomes.c.subcategory_id,
        incomes.c.cost_center_id,
        incomes.c.contact_id,
        incomes.c.description,
        incomes.c.document,
        incomes.c.receiving_method,
        incomes.c.account,
        incomes.c.recurrence,
        incomes.c.competence,
        incomes.c.project,
        incomes.c.tags,
        incomes.c.notes,
        incomes.c.active,
        incomes.c.created_at,
        incomes.c.updated_at,
    )

    if account:
        query = query.where(incomes.c.account == account)

    if account_type:
        query = query.join(accounts, incomes.c.account == func.cast(accounts.c.id, Text))
        query = query.where(accounts.c.type == account_type)

    if status:
        query = query.where(incomes.c.status == status)

    rows = session.execute(query.limit(limit)).all()
    return [
        IncomeOut(
            id=row.id,
            amount=row.amount if row.amount is not None else Decimal("0"),
            status=row.status,
            issue_date=_to_date(row.issue_date),
            due_date=_to_date(row.due_date),
            receipt_date=_to_date(row.receipt_date),
            original_amount=row.original_amount,
            interest=row.interest,
            fine=row.fine,
            discount=row.discount,
            total_received=row.total_received,
            category_id=row.category_id,
            subcategory_id=row.subcategory_id,
            cost_center_id=row.cost_center_id,
            contact_id=row.contact_id,
            description=row.description,
            document=row.document,
            receiving_method=row.receiving_method,
            account=row.account,
            recurrence=row.recurrence,
            competence=row.competence,
            project=row.project,
            tags=row.tags,
            notes=row.notes,
            active=row.active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_income(session, iid: UUID) -> IncomeOut | None:
    row = session.execute(
        select(
            incomes.c.id,
            incomes.c.amount,
            incomes.c.status,
            incomes.c.issue_date,
            incomes.c.due_date,
            incomes.c.receipt_date,
            incomes.c.original_amount,
            incomes.c.interest,
            incomes.c.fine,
            incomes.c.discount,
            incomes.c.total_received,
            incomes.c.category_id,
            incomes.c.subcategory_id,
            incomes.c.cost_center_id,
            incomes.c.contact_id,
            incomes.c.description,
            incomes.c.document,
            incomes.c.receiving_method,
            incomes.c.account,
            incomes.c.recurrence,
            incomes.c.competence,
            incomes.c.project,
            incomes.c.tags,
            incomes.c.notes,
            incomes.c.active,
            incomes.c.created_at,
            incomes.c.updated_at,
        ).where(incomes.c.id == iid)
    ).one_or_none()
    if not row:
        return None
    return IncomeOut(
        id=row.id,
        amount=row.amount if row.amount is not None else Decimal("0"),
        status=row.status,
        issue_date=_to_date(row.issue_date),
        due_date=_to_date(row.due_date),
        receipt_date=_to_date(row.receipt_date),
        original_amount=row.original_amount,
        interest=row.interest,
        fine=row.fine,
        discount=row.discount,
        total_received=row.total_received,
        category_id=row.category_id,
        subcategory_id=row.subcategory_id,
        cost_center_id=row.cost_center_id,
        contact_id=row.contact_id,
        description=row.description,
        document=row.document,
        receiving_method=row.receiving_method,
        account=row.account,
        recurrence=row.recurrence,
        competence=row.competence,
        project=row.project,
        tags=row.tags,
        notes=row.notes,
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_income(session, iid: UUID, data: IncomeUpdate) -> IncomeOut | None:
    current = get_income(session, iid)
    if not current:
        return None
    new_amount = data.amount if data.amount is not None else current.amount
    new_status = data.status if data.status is not None else current.status
    new_issue_date = data.issue_date if data.issue_date is not None else current.issue_date
    new_due_date = data.due_date if data.due_date is not None else current.due_date
    new_receipt_date = data.receipt_date if data.receipt_date is not None else current.receipt_date
    new_category_id = data.category_id if data.category_id is not None else current.category_id
    new_subcategory_id = (
        data.subcategory_id if data.subcategory_id is not None else current.subcategory_id
    )
    new_cost_center_id = (
        data.cost_center_id if data.cost_center_id is not None else current.cost_center_id
    )
    new_contact_id = data.contact_id if data.contact_id is not None else current.contact_id
    new_description = data.description if data.description is not None else current.description
    new_document = data.document if data.document is not None else current.document
    new_receiving_method = (
        data.receiving_method if data.receiving_method is not None else current.receiving_method
    )
    new_account = str(data.account) if data.account is not None else current.account
    new_recurrence = data.recurrence if data.recurrence is not None else current.recurrence
    new_competence = data.competence if data.competence is not None else current.competence
    new_project = data.project if data.project is not None else current.project
    new_tags = data.tags if data.tags is not None else current.tags
    new_notes = data.notes if data.notes is not None else current.notes
    new_active = data.active if data.active is not None else current.active
    new_original_amount = (
        data.original_amount if data.original_amount is not None else current.original_amount
    )
    new_interest = data.interest if data.interest is not None else current.interest
    new_fine = data.fine if data.fine is not None else current.fine
    new_discount = data.discount if data.discount is not None else current.discount
    new_total_received = (
        data.total_received if data.total_received is not None else current.total_received
    )
    now = datetime.now(UTC)
    session.execute(
        update(incomes)
        .where(incomes.c.id == iid)
        .values(
            amount=new_amount,
            status=new_status,
            issue_date=new_issue_date,
            due_date=new_due_date,
            receipt_date=new_receipt_date,
            original_amount=new_original_amount,
            interest=new_interest,
            fine=new_fine,
            discount=new_discount,
            total_received=new_total_received,
            category_id=new_category_id,
            subcategory_id=new_subcategory_id,
            cost_center_id=new_cost_center_id,
            contact_id=new_contact_id,
            description=new_description,
            document=new_document,
            receiving_method=new_receiving_method,
            account=new_account,
            recurrence=new_recurrence,
            competence=new_competence,
            project=new_project,
            tags=new_tags,
            notes=new_notes,
            active=new_active,
            updated_at=now,
        )
    )
    session.commit()
    return IncomeOut(
        id=iid,
        amount=new_amount,
        status=new_status,
        issue_date=new_issue_date,
        due_date=new_due_date,
        receipt_date=new_receipt_date,
        original_amount=new_original_amount,
        interest=new_interest,
        fine=new_fine,
        discount=new_discount,
        total_received=new_total_received,
        category_id=new_category_id,
        subcategory_id=new_subcategory_id,
        cost_center_id=new_cost_center_id,
        contact_id=new_contact_id,
        description=new_description,
        document=new_document,
        receiving_method=new_receiving_method,
        account=new_account,
        recurrence=new_recurrence,
        competence=new_competence,
        project=new_project,
        tags=new_tags,
        notes=new_notes,
        active=new_active,
        created_at=current.created_at,
        updated_at=now,
    )


def delete_income(session, iid: UUID) -> bool:
    session.execute(delete(incomes).where(incomes.c.id == iid))
    session.commit()
    return True
