from datetime import date
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import text
from app.models.accounts import Account
from app.models.incomes import Income

def test_bank_statement_total_incomes_error(client, session):
    # 1. Setup Account
    account_id = uuid4()
    session.add(
        Account(
            id=account_id,
            name="Test Account",
            type="checking",
            initial_balance=1000.00,
            active=True
        )
    )
    session.commit()

    # 2. Add Income with total_received
    session.add(
        Income(
            id=uuid4(),
            description="Salary",
            amount=5000.00,
            total_received=5000.00,
            issue_date=date.today(),
            status="recebido",
            account=account_id,
            active=True
        )
    )
    
    # 3. Add Income pending (should be ignored by status filter)
    session.add(
        Income(
            id=uuid4(),
            description="Future Income",
            amount=1000.00,
            total_received=None, # Pending often has None here
            issue_date=date.today(),
            status="pendente",
            account=account_id,
            active=True
        )
    )
    session.commit()

    # 4. Call Endpoint
    response = client.get("/bank-statement/")
    
    # Check if successful
    assert response.status_code == 200, f"Error response: {response.text}"
    
    data = response.json()
    # Check if calculation makes sense
    # Balance = Initial (1000) + Income (5000) - Expenses (0) = 6000
    assert data["account_balance"] == 6000.0

    # 5. Test with Filter
    # Should work same as above since we only have one account in context that matches
    response_filter = client.get(f"/bank-statement/?account_id={account_id}")
    assert response_filter.status_code == 200
    data_filter = response_filter.json()
    assert data_filter["account_balance"] == 6000.0

    # 6. Test with Filter for non-existent account (or other account)
    other_account_id = uuid4()
    response_other = client.get(f"/bank-statement/?account_id={other_account_id}")
    assert response_other.status_code == 200
    data_other = response_other.json()
    # Balance should be 0 (no initial balance for random id, no transactions)
    assert data_other["account_balance"] == 0.0

