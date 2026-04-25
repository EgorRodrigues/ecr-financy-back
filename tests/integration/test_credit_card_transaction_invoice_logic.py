from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from app.models.accounts import Account
from app.models.contacts import Contact
from app.models.credit_card_invoices import CreditCardInvoice
from app.models.credit_card_transactions import CreditCardTransaction
from app.models.expenses import Expense
from app.repositories.credit_card_invoices import create_invoice
from app.repositories.credit_card_transactions import (
    create_credit_card_transaction,
    transfer_transaction_invoice,
    update_credit_card_transaction,
)
from app.schemas.credit_card_invoices import CreditCardInvoiceCreate
from app.schemas.credit_card_transactions import (
    CreditCardTransactionCreate,
    CreditCardTransactionUpdate,
)


@pytest.fixture
def test_account(session):
    contact_id = uuid4()
    session.add(
        Contact(
            id=contact_id,
            name="Bank Contact",
            type="supplier",
            person_type="legal",
            active=True,
        )
    )
    account_id = uuid4()
    session.add(
        Account(
            id=account_id,
            name="Test Account Logic",
            type="credit_card",
            closing_day=1,
            due_day=8,
            contact_id=contact_id,
            active=True,
        )
    )
    session.flush()
    return account_id


def test_update_transaction_keeps_invoice_on_date_change(session, test_account):
    """
    Test that updating issue_date or due_date DOES NOT change the invoice automatically.
    """
    # 1. Create Invoice A
    # With closing_day=1, a transaction on Jan 15 belongs to period ending Feb 1.
    # Period: Jan 2 to Feb 1.
    invoice_a_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 1, 2),
        period_end=date(2025, 2, 1),
        due_date=date(2025, 2, 8),
        amount=Decimal("0.00"),
        status="open",
    )
    invoice_a = create_invoice(session, invoice_a_data)

    # 2. Create Transaction linked to Invoice A
    # (By using due_date matching the invoice logic, create_credit_card_transaction ensures it)
    # But here we can manually verify it gets linked or just create it and see.
    # Actually create_credit_card_transaction uses ensure_invoice_for_transaction logic.
    # To force it to Invoice A, we can just create it.
    
    transaction_data = CreditCardTransactionCreate(
        account_id=test_account,
        amount=Decimal("100.00"),
        description="Test Transaction",
        due_date=date(2025, 1, 15), # Use a date that maps to the Jan/Feb period (Closing Jan 1 -> Period Jan 2-Feb 1 -> Due Feb 8)
        issue_date=date(2025, 1, 15),
    )
    transaction = create_credit_card_transaction(session, transaction_data)

    # Force the due_date to be what we want (Feb 8) if needed, but for the logic test, sticking to the invoice is key.
    # If create_credit_card_transaction uses due_date to find invoice, then setting it to Jan 15 puts it in Invoice A.
    
    assert transaction.invoice_id == invoice_a.id
    assert session.get(CreditCardInvoice, invoice_a.id).amount == Decimal("100.00")

    # 3. Update Transaction Date to a different month (which would typically trigger a new invoice)
    # Move to next month
    update_data = CreditCardTransactionUpdate(
        issue_date=date(2025, 2, 15),
        due_date=date(2025, 3, 8),
    )
    
    updated_transaction = update_credit_card_transaction(session, transaction.id, update_data)
    
    # Assert it stayed on Invoice A
    assert updated_transaction.invoice_id == invoice_a.id
    
    # Assert Invoice A amount is still 100
    assert session.get(CreditCardInvoice, invoice_a.id).amount == Decimal("100.00")
    
    # Assert Invoice B was NOT created/used (check invoice count or something, but verifying ID match is enough)


def test_transfer_transaction_between_invoices(session, test_account):
    """
    Test transferring a transaction from Invoice A to Invoice B.
    """
    # 1. Create Invoice A and B
    invoice_a_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 1, 2),
        period_end=date(2025, 2, 1),
        due_date=date(2025, 2, 8),
        amount=Decimal("0.00"),
        status="open",
    )
    invoice_a = create_invoice(session, invoice_a_data)
    
    invoice_b_data = CreditCardInvoiceCreate(
        account_id=test_account,
        period_start=date(2025, 2, 2),
        period_end=date(2025, 3, 1),
        due_date=date(2025, 3, 8),
        amount=Decimal("0.00"),
        status="open",
    )
    invoice_b = create_invoice(session, invoice_b_data)

    # 2. Create Transaction on Invoice A
    transaction_data = CreditCardTransactionCreate(
        account_id=test_account,
        amount=Decimal("100.00"),
        description="Test Transaction",
        due_date=date(2025, 1, 15), # Mapped to Invoice A
        issue_date=date(2025, 1, 15),
    )
    transaction = create_credit_card_transaction(session, transaction_data)
    
    assert transaction.invoice_id == invoice_a.id
    assert session.get(CreditCardInvoice, invoice_a.id).amount == Decimal("100.00")
    assert session.get(CreditCardInvoice, invoice_b.id).amount == Decimal("0.00")

    # 3. Transfer to Invoice B
    transferred = transfer_transaction_invoice(session, transaction.id, invoice_b.id)
    
    assert transferred.invoice_id == invoice_b.id
    
    # 4. Verify Amounts
    # Invoice A should be 0
    assert session.get(CreditCardInvoice, invoice_a.id).amount == Decimal("0.00")
    # Invoice B should be 100
    assert session.get(CreditCardInvoice, invoice_b.id).amount == Decimal("100.00")
