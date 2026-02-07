from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credit_card_invoices import CreditCardInvoice
from app.models.expenses import Expense
from app.schemas.expenses import ExpenseCreate, ExpenseOut, ExpenseUpdate


def create_expense(session: Session, data: ExpenseCreate) -> ExpenseOut:
    expense_data = data.model_dump()
    # Convert UUIDs to strings for Text columns
    for field in ["category_id", "subcategory_id", "cost_center_id", "contact_id", "account"]:
        if expense_data.get(field):
            expense_data[field] = str(expense_data[field])

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
    session.refresh(db_expense)
    return ExpenseOut.model_validate(db_expense)


def list_expenses(
    session: Session,
    limit: int = 50,
    account: str | None = None,
    account_type: str | None = None,
    status: str | None = None,
) -> list[ExpenseOut]:
    query = select(Expense)

    if account:
        query = query.where(Expense.account == account)

    if status:
        query = query.where(Expense.status == status)

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
    session.refresh(db_expense)
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
