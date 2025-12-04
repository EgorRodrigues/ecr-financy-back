from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.expenses import ExpenseCreate, ExpenseUpdate, ExpenseOut


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_expense(session, data: ExpenseCreate) -> ExpenseOut:
    eid = uuid1()
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_expense",
        "INSERT INTO expenses (id, amount, status, issue_date, due_date, payment_date, category_id, subcategory_id, cost_center_id, contact_id, description, document, payment_method, account, recurrence, competence, project, tags, notes, active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    )
    session.execute(
        stmt,
        (
            eid,
            data.amount,
            data.status,
            data.issue_date,
            data.due_date,
            data.payment_date,
            data.category_id,
            data.subcategory_id,
            data.cost_center_id,
            data.contact_id,
            data.description,
            data.document,
            data.payment_method,
            data.account,
            data.recurrence,
            data.competence,
            data.project,
            data.tags,
            data.notes,
            data.active,
            now,
            now,
        ),
    )
    return ExpenseOut(
        id=eid,
        amount=data.amount,
        status=data.status,
        issue_date=data.issue_date,
        due_date=data.due_date,
        payment_date=data.payment_date,
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
    stmt = _prepare(
        session,
        "list_expenses",
        "SELECT id, amount, status, issue_date, due_date, payment_date, category_id, subcategory_id, cost_center_id, contact_id, description, document, payment_method, account, recurrence, competence, project, tags, notes, active, created_at, updated_at FROM expenses LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
    return [
        ExpenseOut(
            id=row.id,
            amount=row.amount,
            status=row.status,
            issue_date=row.issue_date,
            due_date=row.due_date,
            payment_date=row.payment_date,
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
    stmt = _prepare(
        session,
        "get_expense",
        "SELECT id, amount, status, issue_date, due_date, payment_date, category_id, subcategory_id, cost_center_id, contact_id, description, document, payment_method, account, recurrence, competence, project, tags, notes, active, created_at, updated_at FROM expenses WHERE id = ?",
    )
    row = session.execute(stmt, (eid,)).one()
    if not row:
        return None
    return ExpenseOut(
        id=row.id,
        amount=row.amount,
        status=row.status,
        issue_date=row.issue_date,
        due_date=row.due_date,
        payment_date=row.payment_date,
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
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_expense",
        "UPDATE expenses SET amount = ?, status = ?, issue_date = ?, due_date = ?, payment_date = ?, category_id = ?, subcategory_id = ?, cost_center_id = ?, contact_id = ?, description = ?, document = ?, payment_method = ?, account = ?, recurrence = ?, competence = ?, project = ?, tags = ?, notes = ?, active = ?, updated_at = ? WHERE id = ?",
    )
    session.execute(
        stmt,
        (
            new_amount,
            new_status,
            new_issue_date,
            new_due_date,
            new_payment_date,
            new_category_id,
            new_subcategory_id,
            new_cost_center_id,
            new_contact_id,
            new_description,
            new_document,
            new_payment_method,
            new_account,
            new_recurrence,
            new_competence,
            new_project,
            new_tags,
            new_notes,
            new_active,
            now,
            eid,
        ),
    )
    return ExpenseOut(
        id=eid,
        amount=new_amount,
        status=new_status,
        issue_date=new_issue_date,
        due_date=new_due_date,
        payment_date=new_payment_date,
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
    stmt = _prepare(session, "delete_expense", "DELETE FROM expenses WHERE id = ?")
    session.execute(stmt, (eid,))
    return True
