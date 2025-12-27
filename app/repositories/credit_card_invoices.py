from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, delete, func
from app.db.postgres import credit_card_invoices, accounts, expenses
from app.models.credit_card_invoices import CreditCardInvoiceCreate, CreditCardInvoiceUpdate, CreditCardInvoiceOut
from datetime import date, timedelta
from decimal import Decimal
import calendar

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
    query = select(credit_card_invoices).where(
        credit_card_invoices.c.account_id == account_id,
        credit_card_invoices.c.period_start == period_start,
        credit_card_invoices.c.period_end == period_end
    )
    result = session.execute(query).one_or_none()
    if result:
        return CreditCardInvoiceOut(
            id=result.id,
            account_id=result.account_id,
            period_start=result.period_start,
            period_end=result.period_end,
            due_date=result.due_date,
            amount=result.amount,
            status=result.status,
            created_at=result.created_at,
            updated_at=result.updated_at
        )
    return None

def get_invoice(session: Session, invoice_id: UUID):
    result = session.execute(
        select(credit_card_invoices).where(credit_card_invoices.c.id == invoice_id)
    ).one_or_none()
    
    if result:
        return CreditCardInvoiceOut(
            id=result.id,
            account_id=result.account_id,
            period_start=result.period_start,
            period_end=result.period_end,
            due_date=result.due_date,
            amount=result.amount,
            status=result.status,
            created_at=result.created_at,
            updated_at=result.updated_at
        )
    return None

def list_invoices(session: Session, account_id: UUID | None = None, status: str | None = None, limit: int = 50):
    query = select(credit_card_invoices)
    
    if account_id:
        query = query.where(credit_card_invoices.c.account_id == account_id)
        
    if status:
        query = query.where(credit_card_invoices.c.status == status)
        
    query = query.order_by(credit_card_invoices.c.due_date.desc()).limit(limit)
    
    rows = session.execute(query).all()
    
    return [
        CreditCardInvoiceOut(
            id=row.id,
            account_id=row.account_id,
            period_start=row.period_start,
            period_end=row.period_end,
            due_date=row.due_date,
            amount=row.amount,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        for row in rows
    ]

def create_invoice(session: Session, payload: CreditCardInvoiceCreate):
    stmt = insert(credit_card_invoices).values(
        account_id=payload.account_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        due_date=payload.due_date,
        amount=payload.amount,
        status=payload.status
    ).returning(credit_card_invoices)
    
    result = session.execute(stmt).one()

    # Sync with Expenses
    account_name_query = select(accounts.c.name).where(accounts.c.id == payload.account_id)
    account_name = session.execute(account_name_query).scalar_one_or_none() or "Unknown Account"

    expense_status = "pago" if result.status == "paid" else "pendente"
    description = f"Fatura Cartão - {account_name} - {result.due_date.strftime('%m/%Y')}"

    session.execute(
        insert(expenses).values(
            id=uuid4(),
            invoice_id=result.id,
            amount=result.amount,
            status=expense_status,
            due_date=result.due_date,
            description=description,
            account=account_name,
            active=True,
            created_at=func.now(),
            updated_at=func.now()
        )
    )

    return CreditCardInvoiceOut(
        id=result.id,
        account_id=result.account_id,
        period_start=result.period_start,
        period_end=result.period_end,
        due_date=result.due_date,
        amount=result.amount,
        status=result.status,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

def update_invoice(session: Session, invoice_id: UUID, payload: CreditCardInvoiceUpdate):
    current = get_invoice(session, invoice_id)
    if not current:
        return None

    values = {}
    if payload.amount is not None:
        values['amount'] = payload.amount
    if payload.status is not None:
        values['status'] = payload.status
    if payload.due_date is not None:
        values['due_date'] = payload.due_date
    
    if not values:
        return current

    values['updated_at'] = func.now()

    stmt = update(credit_card_invoices).where(
        credit_card_invoices.c.id == invoice_id
    ).values(**values).returning(credit_card_invoices)
    
    result = session.execute(stmt).one()

    # Sync with Expenses
    expense_values = {}
    if payload.amount is not None:
        expense_values['amount'] = result.amount
    if payload.status is not None:
        expense_values['status'] = "pago" if result.status == "paid" else "pendente"
    if payload.due_date is not None:
        expense_values['due_date'] = result.due_date
    
    if expense_values:
        expense_values['updated_at'] = func.now()
        session.execute(
            update(expenses).where(
                expenses.c.invoice_id == invoice_id
            ).values(**expense_values)
        )

    return CreditCardInvoiceOut(
        id=result.id,
        account_id=result.account_id,
        period_start=result.period_start,
        period_end=result.period_end,
        due_date=result.due_date,
        amount=result.amount,
        status=result.status,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

def update_invoice_amount(session: Session, invoice_id: UUID, amount_delta: Decimal):
    stmt = update(credit_card_invoices).where(
        credit_card_invoices.c.id == invoice_id
    ).values(
        amount=credit_card_invoices.c.amount + amount_delta,
        updated_at=func.now()
    ).returning(credit_card_invoices)
    
    result = session.execute(stmt).one()

    # Sync with Expenses
    session.execute(
        update(expenses).where(
            expenses.c.invoice_id == invoice_id
        ).values(
            amount=result.amount,
            updated_at=func.now()
        )
    )

    return CreditCardInvoiceOut(
        id=result.id,
        account_id=result.account_id,
        period_start=result.period_start,
        period_end=result.period_end,
        due_date=result.due_date,
        amount=result.amount,
        status=result.status,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

def get_account_details(session: Session, account_id: UUID):
    query = select(accounts).where(accounts.c.id == account_id)
    return session.execute(query).one_or_none()

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
    period_start, period_end, due_date = calculate_invoice_period(transaction_date, closing_day, due_day)
       
    # 3. Check if invoice exists
    invoice = get_invoice_by_period(session, account_id, period_start, period_end)
    
    if not invoice:
        # Create new invoice
        invoice_create = CreditCardInvoiceCreate(
            account_id=account_id,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            amount=Decimal('0'), 
            status="open"
        )
        invoice = create_invoice(session, invoice_create)
        
    return invoice

def get_account_invoices_summary(session: Session, account_id: UUID):
    # Get all non-paid invoices ordered by due_date, excluding past due dates
    today = date.today()
    query = select(credit_card_invoices).where(
        credit_card_invoices.c.account_id == account_id,
        credit_card_invoices.c.status != 'paid',
        credit_card_invoices.c.due_date >= today
    ).order_by(credit_card_invoices.c.due_date.asc())
    
    rows = session.execute(query).all()
    
    invoices = [
        CreditCardInvoiceOut(
            id=row.id,
            account_id=row.account_id,
            period_start=row.period_start,
            period_end=row.period_end,
            due_date=row.due_date,
            amount=row.amount,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        for row in rows
    ]
    
    if not invoices:
        return None, []
        
    # The first one is the oldest open invoice (current or overdue)
    current_invoice = invoices[0]
    next_invoices = invoices[1:]
    
    return current_invoice, next_invoices

def delete_invoice(session: Session, invoice_id: UUID):
    # Sync with Expenses
    session.execute(
        delete(expenses).where(expenses.c.invoice_id == invoice_id)
    )
    
    # Delete Invoice
    session.execute(
        delete(credit_card_invoices).where(credit_card_invoices.c.id == invoice_id)
    )
    return True
