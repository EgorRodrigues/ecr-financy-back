import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from sqlalchemy import insert
from app.db.postgres import accounts
from app.repositories.credit_card_invoices import ensure_invoice_for_transaction

@pytest.fixture
def test_account(session):
    account_id = uuid4()
    session.execute(
        insert(accounts).values(
            id=account_id,
            name="Test Account Integration",
            type="credit_card",
            closing_day=1,
            due_day=8,
            active=True
        )
    )
    session.flush()
    return account_id

@pytest.mark.parametrize("transaction_date, expected_due_date", [
    (date(2025, 12, 1), date(2025, 12, 8)),   # On closing day (1st) -> Current Month (Dec 8)
    (date(2025, 11, 30), date(2025, 12, 8)),  # Before closing day -> Current Month (Dec 8)
    (date(2025, 12, 2), date(2026, 1, 8)),    # After closing day -> Next Month (Jan 8)
    (date(2025, 12, 26), date(2026, 1, 8)),   # Bug Scenario: Late Dec -> Jan 8
    (date(2026, 1, 26), date(2026, 2, 8)),    # Late Jan -> Feb 8
    (date(2026, 2, 26), date(2026, 3, 8)),    # Late Feb -> Mar 8
])
def test_invoice_creation_dates(session, test_account, transaction_date, expected_due_date):
    """
    Test that ensure_invoice_for_transaction correctly calculates the invoice due date
    based on the account's closing_day (1) and due_day (8).
    """
    amount = Decimal("100.00")
    
    invoice = ensure_invoice_for_transaction(
        session, 
        test_account, 
        transaction_date
    )
    
    assert invoice.due_date == expected_due_date, \
        f"For transaction on {transaction_date}, expected due date {expected_due_date}, got {invoice.due_date}"
    
    assert invoice.account_id == test_account

def test_invoice_reuse(session, test_account):
    """
    Test that multiple transactions in the same period reuse the same invoice.
    """
    date1 = date(2025, 12, 26)
    date2 = date(2025, 12, 27)
    amount = Decimal("50.00")
    
    invoice1 = ensure_invoice_for_transaction(session, test_account, date1)
    invoice2 = ensure_invoice_for_transaction(session, test_account, date2)
    
    assert invoice1.id == invoice2.id
    assert invoice1.due_date == date(2026, 1, 8)
