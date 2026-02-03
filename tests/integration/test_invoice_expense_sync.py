from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.accounts import Account
from app.models.credit_card_invoices import CreditCardInvoice
from app.models.expenses import Expense
from app.schemas.credit_card_invoices import CreditCardInvoiceCreate, CreditCardInvoiceUpdate
from app.schemas.expenses import ExpenseUpdate
from app.repositories.credit_card_invoices import (
    create_invoice,
    delete_invoice,
    update_invoice,
    update_invoice_amount,
)
from app.repositories.expenses import delete_expense, update_expense


@pytest.fixture
def test_account(session):
    account_id = uuid4()
    session.add(
        Account(
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
    expense = session.get(Expense, invoice.expense_id)

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
    expense = session.get(Expense, invoice.expense_id)

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
    expense = session.get(Expense, invoice.expense_id)

    assert expense.status == "pago"
    assert expense.due_date == date(2026, 1, 10)


def test_update_invoice_payment_fields_syncs_expense(session, test_account):
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )
    invoice = create_invoice(session, invoice_data)

    payment_date = date(2026, 1, 9)
    update_data = CreditCardInvoiceUpdate(
        status="paid",
        payment_date=payment_date,
        interest=Decimal("10.00"),
        fine=Decimal("5.00"),
        discount=Decimal("3.00"),
        total_paid=Decimal("112.00"),
    )
    update_invoice(session, invoice.id, update_data)

    expense = session.get(Expense, invoice.expense_id)

    assert expense is not None
    assert expense.status == "pago"
    assert expense.payment_date == payment_date
    assert expense.interest == Decimal("10.00")
    assert expense.fine == Decimal("5.00")
    assert expense.discount == Decimal("3.00")
    assert expense.total_paid == Decimal("112.00")


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
    assert session.get(Expense, invoice.expense_id) is not None

    # Delete Invoice
    delete_invoice(session, invoice.id)

    # Check Expense Deleted
    assert session.get(Expense, invoice.expense_id) is None

    # Check Invoice Deleted
    assert session.get(CreditCardInvoice, invoice.id) is None


def test_cannot_update_linked_expense_directly(session, test_account):
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )
    invoice = create_invoice(session, invoice_data)

    with pytest.raises(ValueError):
        update_expense(
            session,
            invoice.expense_id,
            ExpenseUpdate(description="Should not update directly"),
        )


def test_cannot_delete_linked_expense_directly(session, test_account):
    invoice_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 12, 2),
        period_end=date(2026, 1, 1),
        due_date=date(2026, 1, 8),
        amount=Decimal("100.00"),
        status="open",
    )
    invoice = create_invoice(session, invoice_data)

    with pytest.raises(ValueError):
        delete_expense(session, invoice.expense_id)
