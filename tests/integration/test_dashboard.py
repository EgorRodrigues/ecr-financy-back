from datetime import date, timedelta
from uuid import uuid4

from app.models.accounts import Account
from app.models.expenses import Expense
from app.models.incomes import Income


def test_dashboard_endpoint(client, session):
    # 1. Setup Data
    # Account 1
    acct1_id = uuid4()
    session.add(
        Account(
            id=acct1_id,
            name="Main Account",
            type="bank",
            initial_balance=1000.00,
            active=True
        )
    )
    
    # Account 2
    acct2_id = uuid4()
    session.add(
        Account(
            id=acct2_id,
            name="Emergency Fund",
            type="bank",
            initial_balance=5000.00,
            active=True
        )
    )

    # Incomes for Account 1
    # 1. Income last month
    last_month = date.today().replace(day=1) - timedelta(days=1)
    session.add(
        Income(
            id=uuid4(),
            description="Salary",
            amount=3000.00,
            total_received=3000.00,
            issue_date=last_month,
            status="recebido",
            account_id=acct1_id,
            active=True
        )
    )
    
    # 2. Income this month
    session.add(
        Income(
            id=uuid4(),
            description="Freelance",
            amount=500.00,
            total_received=500.00,
            issue_date=date.today(),
            status="recebido",
            account_id=acct1_id,
            active=True
        )
    )

    # Expenses for Account 1
    # 1. Expense last month
    session.add(
        Expense(
            id=uuid4(),
            description="Rent",
            amount=1200.00,
            total_paid=1200.00,
            issue_date=last_month,
            status="pago",
            account_id=acct1_id,
            active=True
        )
    )

    session.commit()

    # 2. Call Endpoint
    response = client.get("/dashboard/")
    assert response.status_code == 200
    data = response.json()

    # 3. Assertions
    # Accounts
    assert len(data["accounts"]) == 2
    # Check Account 1 balance: 1000 + 3000 + 500 - 1200 = 3300
    acct1 = next(a for a in data["accounts"] if a["id"] == str(acct1_id))
    assert acct1["name"] == "Main Account"
    assert acct1["balance"] == 3300.00
    
    # Check Account 2 balance: 5000 + 0 - 0 = 5000
    acct2 = next(a for a in data["accounts"] if a["id"] == str(acct2_id))
    assert acct2["balance"] == 5000.00

    # Monthly Summary
    # Should have entries for last_month and this_month (if different)
    assert len(data["monthlySummary"]) >= 1
    
    # Recent Transactions
    # Should have 3 transactions
    assert len(data["recentTransactions"]) == 3
    # Check sort order (desc date)
    assert data["recentTransactions"][0]["date"] >= data["recentTransactions"][1]["date"]
