import calendar
from datetime import datetime, UTC
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.credit_card_invoices import CreditCardInvoice
from app.models.expenses import Expense, ExpenseInstallmentGroup
from app.schemas.expenses import (
    ExpenseCreate,
    ExpenseInstallmentGroupOut,
    ExpenseInstallmentGroupWithExpensesOut,
    ExpenseInstallmentGroupSummaryOut,
    ExpenseInstallmentGroupUpdate,
    ExpenseInstallmentPlanCreate,
    ExpenseOut,
    ExpenseUpdate,
)


def _add_months(d, months: int):
    month_index = (d.month - 1) + months
    year = d.year + (month_index // 12)
    month = (month_index % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return d.replace(year=year, month=month, day=day)


def create_expense(session: Session, data: ExpenseCreate) -> ExpenseOut:
    expense_data = data.model_dump()
    
    # Calculate total_paid if status is "pago"
    if expense_data.get("status") == "pago":
        amount = expense_data.get("amount") or 0
        interest = expense_data.get("interest") or 0
        fine = expense_data.get("fine") or 0
        discount = expense_data.get("discount") or 0
        expense_data["total_paid"] = amount + interest + fine - discount

    db_expense = Expense(
        **expense_data,
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_expense)
    session.commit()
    return ExpenseOut.model_validate(db_expense)


def list_expenses(
    session: Session,
    limit: int,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
    installment_group_id: str | None = None,
) -> list[ExpenseOut]:
    query = select(Expense)

    if account:
        query = query.where(Expense.account_id == account)

    if status:
        query = query.where(Expense.status == status)

    if installment_group_id:
        query = query.where(Expense.installment_group_id == installment_group_id)

    query = query.order_by(Expense.issue_date.desc()).limit(limit)
    rows = session.scalars(query).all()
    return [ExpenseOut.model_validate(row) for row in rows]


def get_expense(session: Session, eid: UUID) -> ExpenseOut | None:
    db_expense = session.get(Expense, eid)
    if not db_expense:
        return None
    return ExpenseOut.model_validate(db_expense)


def update_expense(session: Session, eid: UUID, data: ExpenseUpdate) -> ExpenseOut | None:
    db_expense = session.get(Expense, eid)
    if not db_expense:
        return None
    
    # Check if linked to an invoice
    linked_invoice = session.scalars(
        select(CreditCardInvoice).where(CreditCardInvoice.expense_id == eid)
    ).first()
    
    if linked_invoice:
        raise ValueError("Cannot update expense linked to a credit card invoice")

    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_expense, key, value)

    # Calculate total_paid if status is "pago"
    if db_expense.status == "pago":
        amount = db_expense.amount or 0
        interest = db_expense.interest or 0
        fine = db_expense.fine or 0
        discount = db_expense.discount or 0
        db_expense.total_paid = amount + interest + fine - discount

    db_expense.updated_at = datetime.now(UTC)
    session.commit()
    return ExpenseOut.model_validate(db_expense)


def delete_expense(session: Session, eid: UUID):
    db_expense = session.get(Expense, eid)
    if db_expense:
        # Check if linked to an invoice
        linked_invoice = session.scalars(
            select(CreditCardInvoice).where(CreditCardInvoice.expense_id == eid)
        ).first()
        
        if linked_invoice:
            raise ValueError("Cannot delete expense linked to a credit card invoice")
            
        session.delete(db_expense)
        session.commit()


def create_installment_expenses(
    session: Session, payload: ExpenseInstallmentPlanCreate
) -> ExpenseInstallmentGroupWithExpensesOut:
    if payload.installments_total < 2:
        raise ValueError("installments_total must be >= 2")

    amount_total = payload.amount_total
    installments_total = payload.installments_total
    first_due_date = payload.first_due_date or payload.issue_date

    group = ExpenseInstallmentGroup(
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

    expenses: list[Expense] = []
    for installment_number in range(1, installments_total + 1):
        due_date = _add_months(first_due_date, installment_number - 1)

        if installment_number < installments_total:
            installment_amount = per_installment
        else:
            installment_amount = amount_total - (per_installment * Decimal(installments_total - 1))

        expense_data = {
            "amount": installment_amount,
            "status": payload.status,
            "issue_date": payload.issue_date,
            "due_date": due_date,
            "payment_date": payload.payment_date,
            "interest": payload.interest,
            "fine": payload.fine,
            "discount": payload.discount,
            "total_paid": None,
            "category_id": payload.category_id,
            "subcategory_id": payload.subcategory_id,
            "cost_center_id": payload.cost_center_id,
            "contact_id": payload.contact_id,
            "description": payload.description,
            "document": payload.document,
            "payment_method": payload.payment_method,
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

        if payload.status == "pago":
            amount = Decimal(str(expense_data.get("amount") or 0))
            interest = Decimal(str(payload.interest or 0))
            fine = Decimal(str(payload.fine or 0))
            discount = Decimal(str(payload.discount or 0))
            expense_data["total_paid"] = amount + interest + fine - discount

        db_expense = Expense(
            **expense_data,
            id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(db_expense)
        expenses.append(db_expense)

    session.commit()
    return ExpenseInstallmentGroupWithExpensesOut(
        group=ExpenseInstallmentGroupOut.model_validate(group),
        expenses=[ExpenseOut.model_validate(e) for e in expenses],
    )


def get_installment_group(session: Session, gid: UUID) -> ExpenseInstallmentGroupWithExpensesOut | None:
    group = session.get(ExpenseInstallmentGroup, gid)
    if not group:
        return None

    expenses = session.scalars(
        select(Expense)
        .where(Expense.installment_group_id == gid)
        .order_by(Expense.installment_number.asc())
    ).all()

    return ExpenseInstallmentGroupWithExpensesOut(
        group=ExpenseInstallmentGroupOut.model_validate(group),
        expenses=[ExpenseOut.model_validate(e) for e in expenses],
    )


def list_installment_groups(
    session: Session,
    limit: int = 200,
    account_id: str | None = None,
    contact_id: str | None = None,
    active: bool | None = None,
) -> list[ExpenseInstallmentGroupSummaryOut]:
    paid_sum = func.coalesce(
        func.sum(
            case(
                (Expense.status == "pago", func.coalesce(Expense.total_paid, Expense.amount)),
                else_=0,
            )
        ),
        0,
    )

    expenses_count = func.coalesce(func.count(Expense.id), 0)
    pending_count = func.coalesce(func.sum(case((Expense.status == "pendente", 1), else_=0)), 0)
    paid_count = func.coalesce(func.sum(case((Expense.status == "pago", 1), else_=0)), 0)
    canceled_count = func.coalesce(func.sum(case((Expense.status == "cancelado", 1), else_=0)), 0)
    next_due_date = func.min(
        case((Expense.status == "pendente", Expense.due_date), else_=None)
    )

    stmt = (
        select(
            ExpenseInstallmentGroup,
            expenses_count.label("expenses_count"),
            pending_count.label("pending_count"),
            paid_count.label("paid_count"),
            canceled_count.label("canceled_count"),
            paid_sum.label("total_paid"),
            next_due_date.label("next_due_date"),
        )
        .outerjoin(Expense, Expense.installment_group_id == ExpenseInstallmentGroup.id)
        .group_by(ExpenseInstallmentGroup.id)
        .order_by(ExpenseInstallmentGroup.created_at.desc())
        .limit(limit)
    )

    if account_id:
        stmt = stmt.where(ExpenseInstallmentGroup.account_id == account_id)
    if contact_id:
        stmt = stmt.where(ExpenseInstallmentGroup.contact_id == contact_id)
    if active is not None:
        stmt = stmt.where(ExpenseInstallmentGroup.active == active)

    rows = session.execute(stmt).all()
    results: list[ExpenseInstallmentGroupSummaryOut] = []
    for group, exp_count, pend_count, p_count, c_count, total_paid, n_due in rows:
        results.append(
            ExpenseInstallmentGroupSummaryOut(
                id=group.id,
                description=group.description,
                amount_total=Decimal(str(group.amount_total or 0)),
                installments_total=group.installments_total,
                issue_date=group.issue_date,
                first_due_date=group.first_due_date,
                account_id=group.account_id,
                contact_id=group.contact_id,
                active=group.active,
                expenses_count=int(exp_count or 0),
                pending_count=int(pend_count or 0),
                paid_count=int(p_count or 0),
                canceled_count=int(c_count or 0),
                total_paid=Decimal(str(total_paid or 0)),
                next_due_date=n_due,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )
        )
    return results


def update_installment_group(
    session: Session, gid: UUID, payload: ExpenseInstallmentGroupUpdate
) -> ExpenseInstallmentGroupOut | None:
    group = session.get(ExpenseInstallmentGroup, gid)
    if not group:
        return None

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(group, key, value)

    group.updated_at = datetime.now(UTC)
    session.commit()
    return ExpenseInstallmentGroupOut.model_validate(group)


def cancel_installment_group(session: Session, gid: UUID) -> ExpenseInstallmentGroupWithExpensesOut | None:
    group = session.get(ExpenseInstallmentGroup, gid)
    if not group:
        return None

    expenses = session.scalars(select(Expense).where(Expense.installment_group_id == gid)).all()
    for exp in expenses:
        if exp.status != "pago":
            exp.status = "cancelado"
            exp.total_paid = None
            exp.updated_at = datetime.now(UTC)

    group.updated_at = datetime.now(UTC)
    session.commit()
    return get_installment_group(session, gid)


def deactivate_installment_group(
    session: Session, gid: UUID
) -> ExpenseInstallmentGroupWithExpensesOut | None:
    group = session.get(ExpenseInstallmentGroup, gid)
    if not group:
        return None

    group.active = False
    group.updated_at = datetime.now(UTC)

    expenses = session.scalars(select(Expense).where(Expense.installment_group_id == gid)).all()
    for exp in expenses:
        exp.active = False
        exp.updated_at = datetime.now(UTC)

    session.commit()
    return get_installment_group(session, gid)
