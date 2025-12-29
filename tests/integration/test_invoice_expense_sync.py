import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from sqlalchemy import insert, select
from app.db.postgres import accounts, expenses, credit_card_invoices
from app.repositories.credit_card_invoices import (
    create_invoice,
    update_invoice,
    update_invoice_amount,
    delete_invoice,
)
from app.models.credit_card_invoices import CreditCardInvoiceCreate, CreditCardInvoiceUpdate


@pytest.fixture
def test_account(session):
    account_id = uuid4()
    session.execute(
        insert(accounts).values(
            id=account_id,
            name="Test Account Sync",
            type="credit_card",
            closing_day=1,
            due_day=8,
            active=True,
        )
    )
    session.flush()
    return account_id


def test_create_invoice_syncs_expense(session, test_account):
    """
    Test that creating an invoice creates a corresponding expense.
    """
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )

    invoice = create_invoice(session, invoice_data)

    # Check Expense
    assert invoice.expense_id is not None
    stmt = select(expenses).where(expenses.c.id == invoice.expense_id)
    expense = session.execute(stmt).one_or_none()

    assert expense is not None
    assert expense.amount == Decimal("100.00")
    assert expense.due_date == date(2026, 1, 8)
    assert "Test Account Sync" in expense.description
    assert expense.status == "pendente"  # Open invoice -> pendente


def test_update_invoice_amount_syncs_expense(session, test_account):
    """
    Test that updating invoice amount updates the expense amount.
    """
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )
    invoice = create_invoice(session, invoice_data)

    # Update Amount
    update_invoice_amount(session, invoice.id, Decimal("50.00"))  # Add 50

    # Check Expense
    stmt = select(expenses).where(expenses.c.id == invoice.expense_id)
    expense = session.execute(stmt).one_or_none()

    assert expense.amount == Decimal("150.00")


def test_update_invoice_properties_syncs_expense(session, test_account):
    """
    Test that updating invoice status/due_date updates the expense.
    """
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )
    invoice = create_invoice(session, invoice_data)

    # Update Status to Paid and Due Date
    update_data = CreditCardInvoiceUpdate(status="paid", due_date=date(2026, 1, 10))
    update_invoice(session, invoice.id, update_data)

    # Check Expense
    stmt = select(expenses).where(expenses.c.id == invoice.expense_id)
    expense = session.execute(stmt).one_or_none()

    assert expense.status == "pago"
    assert expense.due_date == date(2026, 1, 10)


def test_delete_invoice_syncs_expense(session, test_account):
    """
    Test that deleting an invoice deletes the corresponding expense.
    """
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )
    invoice = create_invoice(session, invoice_data)

    # Ensure expense exists
    assert invoice.expense_id is not None
    stmt = select(expenses).where(expenses.c.id == invoice.expense_id)
    assert session.execute(stmt).one_or_none() is not None

    # Delete Invoice
    delete_invoice(session, invoice.id)

    # Check Expense Deleted
    stmt = select(expenses).where(expenses.c.id == invoice.expense_id)
    assert session.execute(stmt).one_or_none() is None

    # Check Invoice Deleted
    stmt = select(credit_card_invoices).where(credit_card_invoices.c.id == invoice.id)
    assert session.execute(stmt).one_or_none() is None
