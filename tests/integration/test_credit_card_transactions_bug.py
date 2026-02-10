from datetime import date
from uuid import uuid4
from fastapi.testclient import TestClient

def test_create_credit_card_transaction_persistence_bug(client: TestClient):
    # 1. Create Account
    r_acc = client.post("/accounts/", json={"name": "CC Test Acc", "type": "credit_card", "initial_balance": 0, "available_limit": 1000})
    assert r_acc.status_code == 200
    account_id = r_acc.json()["id"]

    # 2. Create Transaction
    payload = {
        "amount": 100.50,
        "description": "Test Persistence",
        "account_id": account_id,
        "due_date": date.today().isoformat(),
        "status": "pago"
    }
    
    response = client.post("/credit-card-transactions/", json=payload)
    assert response.status_code == 200
    created_id = response.json()["id"]
    
    # 3. Verify if it persists
    # Retrieve by ID
    get_response = client.get(f"/credit-card-transactions/{created_id}")
    
    # EXPECTED FAILURE: If commit is missing, this might return 404 or fail later
    # Note: In some test setups, the same session might be shared, masking the issue. 
    # But usually TestClient requests run in isolation or the app logic relies on commit.
    
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Test Persistence"

    # 4. List transactions for account
    list_response = client.get(f"/credit-card-transactions/?account_id={account_id}")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) > 0
    assert any(i["id"] == created_id for i in items)
