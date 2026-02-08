from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.accounts import Account
from app.models.contacts import Contact
from app.models.expenses import Expense
from app.models.incomes import Income


def test_transfer_creates_expense_and_income(client, session):
    # 1. Setup Contacts
    contact_source_bank = Contact(id=uuid4(), name="Bank A (Source)", type="supplier", person_type="legal")
    contact_dest_bank = Contact(id=uuid4(), name="Bank B (Dest)", type="supplier", person_type="legal")
    session.add_all([contact_source_bank, contact_dest_bank])
    session.commit()

    # 2. Setup Accounts linked to Contacts
    # Source Account is at Bank A
    source_account = Account(
        id=uuid4(), name="Account A", type="checking", contact_id=contact_source_bank.id, active=True
    )
    # Destination Account is at Bank B
    dest_account = Account(
        id=uuid4(), name="Account B", type="checking", contact_id=contact_dest_bank.id, active=True
    )
    session.add_all([source_account, dest_account])
    session.commit()

    # 3. Perform Transfer
    payload = {
        "source_account_id": str(source_account.id),
        "destination_account_id": str(dest_account.id),
        "amount": 100.50,
        "date": str(date.today()),
        "description": "Test Transfer"
    }

    from uuid import UUID

    response = client.post("/transfers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "expense_id" in data
    assert "income_id" in data

    # 4. Verify Expense (Source)
    # Expense should be in Source Account, paid to Destination Bank (contact_dest_bank)
    expense = session.get(Expense, UUID(data["expense_id"]))
    assert expense.amount == 100.50
    assert expense.account_id == source_account.id
    assert expense.contact_id == contact_dest_bank.id # Key verification
    assert expense.status == "pago"

    # 5. Verify Income (Destination)
    # Income should be in Destination Account, received from Source Bank (contact_source_bank)
    income = session.get(Income, UUID(data["income_id"]))
    assert income.amount == 100.50
    assert income.account_id == dest_account.id
    assert income.contact_id == contact_source_bank.id # Key verification
    assert income.status == "recebido"
