import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.accounts import Account
from app.models.credit_card_invoices import CreditCardInvoice
from app.models.expenses import Expense
from app.schemas.credit_card_invoices import (
    CreditCardInvoiceCreate,
    CreditCardInvoiceOut,
    CreditCardInvoiceUpdate,
)

UTC = timezone.utc


def calculate_invoice_period(transaction_date: date, closing_day: int, due_day: int):
    # Determine the closing date for the transaction
    if transaction_date.day <= closing_day:
        last_day_current = calendar.monthrange(transaction_date.year, transaction_date.month)[1]
        effective_closing = min(closing_day, last_day_current)
        period_end = date(transaction_date.year, transaction_date.month, effective_closing)
    else:
        # Closes next month
        if transaction_date.month == 12:
            year = transaction_date.year + 1
            month = 1
        else:
            year = transaction_date.year
            month = transaction_date.month + 1

        last_day_next = calendar.monthrange(year, month)[1]
        effective_closing = min(closing_day, last_day_next)
        period_end = date(year, month, effective_closing)

    # Calculate period start (day after previous closing)
    if period_end.month == 1:
        prev_year = period_end.year - 1
        prev_month = 12
    else:
        prev_year = period_end.year
        prev_month = period_end.month - 1

    last_day_prev = calendar.monthrange(prev_year, prev_month)[1]
    effective_prev_closing = min(closing_day, last_day_prev)
    prev_closing_date = date(prev_year, prev_month, effective_prev_closing)

    period_start = prev_closing_date + timedelta(days=1)

    # Calculate Due Date
    if due_day >= closing_day:
        due_year = period_end.year
        due_month = period_end.month
    else:
        if period_end.month == 12:
            due_year = period_end.year + 1
            due_month = 1
        else:
            due_year = period_end.year
            due_month = period_end.month + 1

    last_day_due = calendar.monthrange(due_year, due_month)[1]
    effective_due_day = min(due_day, last_day_due)
    due_date = date(due_year, due_month, effective_due_day)

    return period_start, period_end, due_date


def calculate_period_from_due_date(target_due_date: date, closing_day: int, due_day: int):
    # Determine the "official" invoice due date for the month/year of the target_due_date
    last_day_target_month = calendar.monthrange(target_due_date.year, target_due_date.month)[1]
    effective_due_day = min(due_day, last_day_target_month)
    invoice_due_date = date(target_due_date.year, target_due_date.month, effective_due_day)

    # Backtrack to find Period End (Closing Date)
    if due_day >= closing_day:
        # Closing was in the SAME month/year
        closing_year = invoice_due_date.year
        closing_month = invoice_due_date.month
    else:
        # Closing was in the PREVIOUS month/year
        if invoice_due_date.month == 1:
            closing_year = invoice_due_date.year - 1
            closing_month = 12
        else:
            closing_year = invoice_due_date.year
            closing_month = invoice_due_date.month - 1

    last_day_closing = calendar.monthrange(closing_year, closing_month)[1]
    effective_closing_day = min(closing_day, last_day_closing)
    period_end = date(closing_year, closing_month, effective_closing_day)

    # Backtrack to find Period Start (Day after Previous Closing)
    if period_end.month == 1:
        prev_year = period_end.year - 1
        prev_month = 12
    else:
        prev_year = period_end.year
        prev_month = period_end.month - 1

    last_day_prev = calendar.monthrange(prev_year, prev_month)[1]
    effective_prev_closing = min(closing_day, last_day_prev)
    prev_closing_date = date(prev_year, prev_month, effective_prev_closing)

    period_start = prev_closing_date + timedelta(days=1)

    return period_start, period_end, invoice_due_date


def get_invoice_by_period(session: Session, account_id: UUID, period_start: date, period_end: date):
    query = select(CreditCardInvoice).where(
        CreditCardInvoice.account_id == account_id,
        CreditCardInvoice.period_start == period_start,
        CreditCardInvoice.period_end == period_end,
    )
    result = session.scalar(query)
    if result:
        return CreditCardInvoiceOut.model_validate(result)
    return None


def get_invoice(session: Session, invoice_id: UUID):
    result = session.get(CreditCardInvoice, invoice_id)

    if result:
        return CreditCardInvoiceOut.model_validate(result)
    return None


def list_invoices(
    session: Session, account_id: UUID | None = None, status: str | None = None, limit: int = 50
):
    query = select(CreditCardInvoice)

    if account_id:
        query = query.where(CreditCardInvoice.account_id == account_id)

    if status:
        query = query.where(CreditCardInvoice.status == status)

    query = query.order_by(CreditCardInvoice.due_date.desc()).limit(limit)

    rows = session.scalars(query).all()

    return [CreditCardInvoiceOut.model_validate(row) for row in rows]


def create_invoice(session: Session, payload: CreditCardInvoiceCreate):
    # Sync with Expenses first to get ID
    account_query = select(Account).where(Account.id == payload.account_id)
    account = session.scalar(account_query)
    
    account_name = account.name if account else "Unknown Account"
    contact_id = account.contact_id if account and account.contact_id else None

    if not contact_id:
        raise ValueError(f"Account '{account_name}' must have a contact linked for credit card invoices")

    expense_status = "pago" if payload.status == "paid" else "pendente"
    description = f"Fatura Cartão - {account_name} - {payload.due_date.strftime('%m/%Y')}"

    expense_id = uuid4()

    new_expense = Expense(
        id=expense_id,
        amount=payload.amount,
        status=expense_status,
        issue_date=date.today(),  # Added issue_date
        due_date=payload.due_date,
        description=description,
        account_id=payload.account_id,
        contact_id=contact_id,
        active=True,
    )
    session.add(new_expense)

    new_invoice = CreditCardInvoice(
        account_id=payload.account_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        due_date=payload.due_date,
        amount=payload.amount,
        status=payload.status,
        expense_id=expense_id,
    )
    session.add(new_invoice)
    session.flush()

    return CreditCardInvoiceOut.model_validate(new_invoice)


def update_invoice(session: Session, invoice_id: UUID, payload: CreditCardInvoiceUpdate):
    current = session.get(CreditCardInvoice, invoice_id)
    if not current:
        return None

    if payload.amount is not None:
        current.amount = payload.amount
    if payload.status is not None:
        current.status = payload.status
    if payload.due_date is not None:
        current.due_date = payload.due_date
    if payload.payment_date is not None:
        current.payment_date = payload.payment_date
        # If payment_date is provided, we assume the invoice is being paid
        if not payload.status:
            current.status = "paid"

    if payload.interest is not None:
        current.interest = payload.interest
    if payload.fine is not None:
        current.fine = payload.fine
    if payload.discount is not None:
        current.discount = payload.discount
    if payload.total_paid is not None:
        current.total_paid = payload.total_paid

    # Sync with Expenses
    if current.expense_id:
        expense = session.get(Expense, current.expense_id)
        if expense:
            if payload.amount is not None:
                expense.amount = current.amount
            
            # Sync status if it changed explicitly or implicitly via payment_date
            if payload.status is not None or payload.payment_date is not None:
                expense.status = "pago" if current.status == "paid" else "pendente"
            
            if payload.due_date is not None:
                expense.due_date = current.due_date
            if payload.payment_date is not None:
                expense.payment_date = current.payment_date
            if payload.interest is not None:
                expense.interest = current.interest
            if payload.fine is not None:
                expense.fine = current.fine
            if payload.discount is not None:
                expense.discount = current.discount
            if payload.total_paid is not None:
                expense.total_paid = current.total_paid

    session.flush()

    return CreditCardInvoiceOut.model_validate(current)


def update_invoice_amount(session: Session, invoice_id: UUID, amount_delta: Decimal):
    current = session.get(CreditCardInvoice, invoice_id)
    if not current:
        return None
    
    current.amount += amount_delta
    
    # Sync with Expenses
    if current.expense_id:
        expense = session.get(Expense, current.expense_id)
        if expense:
            expense.amount = current.amount

    session.flush()

    return CreditCardInvoiceOut.model_validate(current)


def get_account_details(session: Session, account_id: UUID):
    return session.get(Account, account_id)


def ensure_invoice_for_transaction(session: Session, account_id: UUID, transaction_date: date):
    # 1. Get Account Settings
    account = get_account_details(session, account_id)
    if not account:
        raise ValueError("Account not found")

    closing_day = account.closing_day
    due_day = account.due_day

    if not closing_day or not due_day:
        raise ValueError("Account missing closing_day or due_day configuration")

    # 2. Calculate Period
    period_start, period_end, due_date = calculate_invoice_period(
        transaction_date, closing_day, due_day
    )

    # 3. Check if invoice exists
    invoice = get_invoice_by_period(session, account_id, period_start, period_end)

    if not invoice:
        # Create new invoice
        invoice_create = CreditCardInvoiceCreate(
            account_id=account_id,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            amount=Decimal("0"),
            status="open",
        )
        invoice = create_invoice(session, invoice_create)

    return invoice


def get_account_invoices_summary(session: Session, account_id: UUID):
    # Get all non-paid invoices ordered by due_date, excluding past due dates
    today = date.today()
    query = (
        select(CreditCardInvoice)
        .where(
            CreditCardInvoice.account_id == account_id,
            CreditCardInvoice.status != "paid",
            CreditCardInvoice.due_date >= today,
        )
        .order_by(CreditCardInvoice.due_date.asc())
    )

    rows = session.scalars(query).all()

    invoices = [CreditCardInvoiceOut.model_validate(row) for row in rows]

    if not invoices:
        return None, []

    # The first one is the oldest open invoice (current or overdue)
    current_invoice = invoices[0]
    next_invoices = invoices[1:]

    return current_invoice, next_invoices


def delete_invoice(session: Session, invoice_id: UUID):
    # Get invoice to find expense_id
    stmt = select(CreditCardInvoice.expense_id).where(CreditCardInvoice.id == invoice_id)
    expense_id = session.scalar(stmt)

    # Delete Invoice
    invoice = session.get(CreditCardInvoice, invoice_id)
    if invoice:
        session.delete(invoice)

    # Sync with Expenses
    if expense_id:
        expense = session.get(Expense, expense_id)
        if expense:
            session.delete(expense)

    session.flush()

    return True
