from datetime import date, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

def test_bank_statement_partial_account_match(client: TestClient):
    # Create one account
    r_acc = client.post("/accounts/", json={"name": "Existing Acc", "type": "bank", "initial_balance": 100})
    assert r_acc.status_code == 200
    existing_id = r_acc.json()["id"]
    
    missing_id = str(uuid4())
    
    # Request both
    # Query param: account_ids=existing_id&account_ids=missing_id
    response = client.get(f"/bank-statement/?account_ids={existing_id}&account_ids={missing_id}")
    
    # Should fail because one is missing
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"

def test_bank_statement_invalid_uuid(client: TestClient):
    response = client.get("/bank-statement/?account_id=invalid-uuid-string")
    assert response.status_code == 422 # Validation Error

def test_bank_statement_date_range_inverted(client: TestClient):
    # Start date after end date
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    response = client.get(f"/bank-statement/?start_date={today}&end_date={yesterday}")
    assert response.status_code == 200
    data = response.json()
    # Should probably be empty transactions
    assert len(data["transactions"]) == 0

def test_bank_statement_future_transactions(client: TestClient):
    # Create account
    r_acc = client.post("/accounts/", json={"name": "Future Acc", "type": "bank", "initial_balance": 0})
    aid = r_acc.json()["id"]
    
    # Create Income in future (recebido? usually future is pendente)
    # If we mark it 'recebido' in future, it technically affects balance if the logic doesn't filter by date <= today
    # But usually 'recebido' implies it happened.
    
    future_date = (date.today() + timedelta(days=10)).isoformat()
    
    client.post("/incomes/", json={
        "amount": 100,
        "total_received": 100,
        "status": "recebido",
        "receipt_date": future_date,
        "description": "Future Money",
        "account_id": aid
    })
    
    # Query Statement for Today
    response = client.get("/bank-statement/")
    data = response.json()
    
    # If the logic sums ALL 'recebido' incomes for balance, it will include this.
    # Logic: 
    # stmt_incomes_total = select(func.sum(Income.total_received)).where(and_(Income.active == True, Income.status == "recebido", income_account_filter))
    # It does NOT filter by date. So Future 'recebido' counts towards Balance.
    # This is a business rule question. Usually 'recebido' means cash in hand. So date shouldn't matter (maybe it was backdated or pre-dated).
    # But for "Transactions List", it filters by date range.
    
    assert data["account_balance"] == 100.0
    
    # Check transactions list (default range ends today)
    descriptions = [t["description"] for t in data["transactions"]]
    assert "Future Money" not in descriptions
    
    # Query with future range
    response_future = client.get(f"/bank-statement/?end_date={future_date}")
    data_future = response_future.json()
    descriptions_future = [t["description"] for t in data_future["transactions"]]
    assert "Future Money" in descriptions_future

def test_bank_statement_status_filtering(client: TestClient):
    # Ensure Pending items don't affect balance
    r_acc = client.post("/accounts/", json={"name": "Status Test", "type": "bank", "initial_balance": 100})
    aid = r_acc.json()["id"]
    
    client.post("/incomes/", json={
        "amount": 500,
        "total_received": 0, # Pending
        "status": "pendente",
        "receipt_date": date.today().isoformat(),
        "description": "Pending Inc",
        "account_id": aid
    })
    
    client.post("/expenses/", json={
        "amount": 200,
        "total_paid": 0, # Pending
        "status": "pendente",
        "payment_date": date.today().isoformat(),
        "description": "Pending Exp",
        "account_id": aid
    })
    
    response = client.get(f"/bank-statement/?account_id={aid}")
    data = response.json()
    
    # Balance should be just initial 100
    assert data["account_balance"] == 100.0
    
    # Transactions should NOT include pending items
    descriptions = [t["description"] for t in data["transactions"]]
    assert "Pending Inc" not in descriptions
    assert "Pending Exp" not in descriptions
    
    # Should be empty transactions
    assert len(data["transactions"]) == 0

