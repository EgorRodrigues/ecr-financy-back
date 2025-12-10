from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, insert, update, delete
from app.models.expenses import ExpenseCreate, ExpenseUpdate, ExpenseOut
from app.db.postgres import expenses


def _to_date(value):
    return value.date() if hasattr(value, "date") else value


def create_expense(session, data: ExpenseCreate) -> ExpenseOut:
    eid = uuid4()
    now = datetime.now(timezone.utc)
    session.execute(
        insert(expenses).values(
            id=eid,
            amount=data.amount,
            status=data.status,
            issue_date=data.issue_date,
            due_date=data.due_date,
            payment_date=data.payment_date,
            original_amount=data.original_amount,
            interest=data.interest,
            fine=data.fine,
            discount=data.discount,
            total_paid=data.total_paid,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            cost_center_id=data.cost_center_id,
            contact_id=data.contact_id,
            description=data.description,
            document=data.document,
            payment_method=data.payment_method,
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
    )
    session.commit()
    return ExpenseOut(
        id=eid,
        amount=data.amount,
        status=data.status,
        issue_date=data.issue_date,
        due_date=data.due_date,
        payment_date=data.payment_date,
        original_amount=data.original_amount,
        interest=data.interest,
        fine=data.fine,
        discount=data.discount,
        total_paid=data.total_paid,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        cost_center_id=data.cost_center_id,
        contact_id=data.contact_id,
        description=data.description,
        document=data.document,
        payment_method=data.payment_method,
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


def list_expenses(session, limit: int = 50) -> list[ExpenseOut]:
    rows = session.execute(
        select(
            expenses.c.id,
            expenses.c.amount,
            expenses.c.status,
            expenses.c.issue_date,
            expenses.c.due_date,
            expenses.c.payment_date,
            expenses.c.original_amount,
            expenses.c.interest,
            expenses.c.fine,
            expenses.c.discount,
            expenses.c.total_paid,
            expenses.c.category_id,
            expenses.c.subcategory_id,
            expenses.c.cost_center_id,
            expenses.c.contact_id,
            expenses.c.description,
            expenses.c.document,
            expenses.c.payment_method,
            expenses.c.account,
            expenses.c.recurrence,
            expenses.c.competence,
            expenses.c.project,
            expenses.c.tags,
            expenses.c.notes,
            expenses.c.active,
            expenses.c.created_at,
            expenses.c.updated_at,
        ).limit(limit)
    ).all()
    return [
        ExpenseOut(
            id=row.id,
            amount=row.amount if row.amount is not None else Decimal('0'),
            status=row.status,
            issue_date=_to_date(row.issue_date),
            due_date=_to_date(row.due_date),
            payment_date=_to_date(row.payment_date),
            original_amount=row.original_amount,
            interest=row.interest,
            fine=row.fine,
            discount=row.discount,
            total_paid=row.total_paid,
            category_id=row.category_id,
            subcategory_id=row.subcategory_id,
            cost_center_id=row.cost_center_id,
            contact_id=row.contact_id,
            description=row.description,
            document=row.document,
            payment_method=row.payment_method,
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


def get_expense(session, eid: UUID) -> ExpenseOut | None:
    row = session.execute(
        select(
            expenses.c.id,
            expenses.c.amount,
            expenses.c.status,
            expenses.c.issue_date,
            expenses.c.due_date,
            expenses.c.payment_date,
            expenses.c.original_amount,
            expenses.c.interest,
            expenses.c.fine,
            expenses.c.discount,
            expenses.c.total_paid,
            expenses.c.category_id,
            expenses.c.subcategory_id,
            expenses.c.cost_center_id,
            expenses.c.contact_id,
            expenses.c.description,
            expenses.c.document,
            expenses.c.payment_method,
            expenses.c.account,
            expenses.c.recurrence,
            expenses.c.competence,
            expenses.c.project,
            expenses.c.tags,
            expenses.c.notes,
            expenses.c.active,
            expenses.c.created_at,
            expenses.c.updated_at,
        ).where(expenses.c.id == eid)
    ).one_or_none()
    if not row:
        return None
    return ExpenseOut(
        id=row.id,
        amount=row.amount if row.amount is not None else Decimal('0'),
        status=row.status,
        issue_date=_to_date(row.issue_date),
        due_date=_to_date(row.due_date),
        payment_date=_to_date(row.payment_date),
        original_amount=row.original_amount,
        interest=row.interest,
        fine=row.fine,
        discount=row.discount,
        total_paid=row.total_paid,
        category_id=row.category_id,
        subcategory_id=row.subcategory_id,
        cost_center_id=row.cost_center_id,
        contact_id=row.contact_id,
        description=row.description,
        document=row.document,
        payment_method=row.payment_method,
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


def update_expense(session, eid: UUID, data: ExpenseUpdate) -> ExpenseOut | None:
    current = get_expense(session, eid)
    if not current:
        return None
    new_amount = data.amount if data.amount is not None else current.amount
    new_status = data.status if data.status is not None else current.status
    new_issue_date = data.issue_date if data.issue_date is not None else current.issue_date
    new_due_date = data.due_date if data.due_date is not None else current.due_date
    new_payment_date = data.payment_date if data.payment_date is not None else current.payment_date
    new_category_id = data.category_id if data.category_id is not None else current.category_id
    new_subcategory_id = data.subcategory_id if data.subcategory_id is not None else current.subcategory_id
    new_cost_center_id = data.cost_center_id if data.cost_center_id is not None else current.cost_center_id
    new_contact_id = data.contact_id if data.contact_id is not None else current.contact_id
    new_description = data.description if data.description is not None else current.description
    new_document = data.document if data.document is not None else current.document
    new_payment_method = data.payment_method if data.payment_method is not None else current.payment_method
    new_account = data.account if data.account is not None else current.account
    new_recurrence = data.recurrence if data.recurrence is not None else current.recurrence
    new_competence = data.competence if data.competence is not None else current.competence
    new_project = data.project if data.project is not None else current.project
    new_tags = data.tags if data.tags is not None else current.tags
    new_notes = data.notes if data.notes is not None else current.notes
    new_active = data.active if data.active is not None else current.active
    new_original_amount = data.original_amount if data.original_amount is not None else current.original_amount
    new_interest = data.interest if data.interest is not None else current.interest
    new_fine = data.fine if data.fine is not None else current.fine
    new_discount = data.discount if data.discount is not None else current.discount
    new_total_paid = data.total_paid if data.total_paid is not None else current.total_paid
    now = datetime.now(timezone.utc)
    session.execute(
        update(expenses)
        .where(expenses.c.id == eid)
        .values(
            amount=new_amount,
            status=new_status,
            issue_date=new_issue_date,
            due_date=new_due_date,
            payment_date=new_payment_date,
            original_amount=new_original_amount,
            interest=new_interest,
            fine=new_fine,
            discount=new_discount,
            total_paid=new_total_paid,
            category_id=new_category_id,
            subcategory_id=new_subcategory_id,
            cost_center_id=new_cost_center_id,
            contact_id=new_contact_id,
            description=new_description,
            document=new_document,
            payment_method=new_payment_method,
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
    return ExpenseOut(
        id=eid,
        amount=new_amount,
        status=new_status,
        issue_date=new_issue_date,
        due_date=new_due_date,
        payment_date=new_payment_date,
        original_amount=new_original_amount,
        interest=new_interest,
        fine=new_fine,
        discount=new_discount,
        total_paid=new_total_paid,
        category_id=new_category_id,
        subcategory_id=new_subcategory_id,
        cost_center_id=new_cost_center_id,
        contact_id=new_contact_id,
        description=new_description,
        document=new_document,
        payment_method=new_payment_method,
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


def delete_expense(session, eid: UUID) -> bool:
    session.execute(delete(expenses).where(expenses.c.id == eid))
    session.commit()
    return True
