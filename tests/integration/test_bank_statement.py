from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient


def test_bank_statement_basic(client: TestClient):
    # 1. Create Account
    acc_payload = {
        "name": "Statement Test Account",
        "type": "bank",
        "initial_balance": 1000.00,
        "active": True,
    }
    r_acc = client.post("/accounts/", json=acc_payload)
    assert r_acc.status_code == 200
    account_id = r_acc.json()["id"]

    # 1.5 Create Categories
    cat_work = client.post("/categories/", json={"name": "Work", "active": True})
    assert cat_work.status_code == 200
    cat_work_id = cat_work.json()["id"]
    
    cat_food = client.post("/categories/", json={"name": "Food", "active": True})
    assert cat_food.status_code == 200
    cat_food_id = cat_food.json()["id"]

    # 2. Create Income (Received)
    today = date.today().isoformat()
    inc_payload = {
        "amount": 500.00,
        "total_received": 500.00,
        "status": "recebido",
        "receipt_date": today,
        "description": "Salary",
        "account": account_id,
        "category_id": cat_work_id,
        "active": True
    }
    r_inc = client.post("/incomes/", json=inc_payload)
    assert r_inc.status_code == 200

    # 3. Create Expense (Paid)
    exp_payload = {
        "amount": 200.00,
        "total_paid": 200.00,
        "status": "pago",
        "payment_date": today,
        "description": "Grocery",
        "account": account_id,
        "category_id": cat_food_id,
        "active": True
    }
    r_exp = client.post("/expenses/", json=exp_payload)
    assert r_exp.status_code == 200

    # 4. Create Pending Expense (Should not be in balance, and likely not in list if no date)
    exp_pending_payload = {
        "amount": 100.00,
        "total_paid": 0.00,
        "status": "pendente",
        # Even if it has a payment_date (user error or scheduled), it should NOT appear if status is pending
        "payment_date": today,
        "description": "Future Bill",
        "account": account_id,
        "active": True
    }
    r_exp_p = client.post("/expenses/", json=exp_pending_payload)
    assert r_exp_p.status_code == 200

    # 5. Get Statement
    # Default params (should cover today)
    response = client.get("/bank-statement/")
    assert response.status_code == 200
    data = response.json()

    # Verify Balance
    # 1000 + 500 - 200 = 1300
    assert data["account_balance"] == 1300.00
    
    # Verify Period Summary
    summary = data["period_summary"]
    assert summary["total_income"] == 500.00
    assert summary["total_expense"] == 200.00
    assert summary["net_result"] == 300.00 # 500 - 200

    # Verify Transactions
    # Should have 2 transactions (Salary, Grocery)
    assert len(data["transactions"]) == 2
    
    # Sort order is date desc. Since both are today, order might be unstable or based on insertion if time matches (but date is only date).
    # My SQL query orders by date desc. If equal, arbitrary.
    
    descriptions = {t["description"] for t in data["transactions"]}
    assert "Salary" in descriptions
    assert "Grocery" in descriptions
    assert "Future Bill" not in descriptions

    # Check details of Salary
    salary_tx = next(t for t in data["transactions"] if t["description"] == "Salary")
    assert salary_tx["amount"] == 500.00
    assert salary_tx["status"] == "recebido"
    assert salary_tx["type"] == "income"
    assert salary_tx["category_name"] == "Work"

    # Check details of Grocery
    grocery_tx = next(t for t in data["transactions"] if t["description"] == "Grocery")
    assert grocery_tx["amount"] == 200.00 # Expecting positive for expense
    assert grocery_tx["status"] == "pago"
    assert grocery_tx["type"] == "expense"
    assert grocery_tx["category_name"] == "Food"


def test_bank_statement_with_filters(client: TestClient):
    # Setup similar data
    r_acc = client.post("/accounts/", json={"name": "Filter Account", "type": "bank", "initial_balance": 0})
    aid = r_acc.json()["id"]
    today = date.today().isoformat()
    
    # Income today
    client.post("/incomes/", json={
        "amount": 100, "total_received": 100, "status": "recebido", "receipt_date": today, "account": aid, "description": "Today Inc"
    })
    
    # Expense last month (should be excluded if we query today only, but default is 1 month window so it might be included)
    # Let's verify default window behavior.
    # Default start_date = today - 30 days.
    # If I create a transaction 40 days ago, it should be excluded.
    
    # Need to manipulate date.
    # Since I can't easily inject "40 days ago" via API if validation forbids past dates? 
    # Usually APIs allow past dates.
    
    from datetime import datetime, timedelta
    past_date = (datetime.now() - timedelta(days=40)).date().isoformat()
    
    client.post("/expenses/", json={
        "amount": 50, "total_paid": 50, "status": "pago", "payment_date": past_date, "account": aid, "description": "Old Exp"
    })

    # Query with default (Last 30 days)
    # Balance should still be Global (0 + 100 - 50 = 50).
    # Transactions list should only show "Today Inc".
    
    # Passing account_ids as a list query parameter
    # FastAPI handles list query params as `key=val1&key=val2`
    response = client.get(f"/bank-statement/?account_ids={aid}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["account_balance"] == 50.00 # Balance is always global
    
    descriptions = [t["description"] for t in data["transactions"]]
    assert "Today Inc" in descriptions
    assert "Old Exp" not in descriptions

def test_bank_statement_multiple_accounts_filter(client: TestClient):
    # Account A
    r_a = client.post("/accounts/", json={"name": "Acc A", "type": "bank", "initial_balance": 100})
    aid_a = r_a.json()["id"]
    
    # Account B
    r_b = client.post("/accounts/", json={"name": "Acc B", "type": "bank", "initial_balance": 200})
    aid_b = r_b.json()["id"]
    
    today = date.today().isoformat()
    
    # Income on A
    client.post("/incomes/", json={
        "amount": 50, "total_received": 50, "status": "recebido", "receipt_date": today, "account": aid_a, "description": "Inc A"
    })
    
    # Income on B
    client.post("/incomes/", json={
        "amount": 60, "total_received": 60, "status": "recebido", "receipt_date": today, "account": aid_b, "description": "Inc B"
    })
    
    # Filter only Account A
    response = client.get(f"/bank-statement/?account_ids={aid_a}")
    data = response.json()
    
    # Balance A: 100 (init) + 50 (inc) = 150
    assert data["account_balance"] == 150.00
    descriptions = [t["description"] for t in data["transactions"]]
    assert "Inc A" in descriptions
    assert "Inc B" not in descriptions
    
    # Filter only Account B
    response = client.get(f"/bank-statement/?account_ids={aid_b}")
    data = response.json()
    
    # Balance B: 200 (init) + 60 (inc) = 260
    assert data["account_balance"] == 260.00
    descriptions = [t["description"] for t in data["transactions"]]
    assert "Inc B" in descriptions
    assert "Inc A" not in descriptions
    
    # No Filter (Both)
    response = client.get("/bank-statement/")
    data = response.json()
    
    # Total Balance: 150 + 260 = 410
    assert data["account_balance"] == 410.00
