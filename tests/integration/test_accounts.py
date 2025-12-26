from fastapi.testclient import TestClient
from uuid import uuid4

def test_create_account(client: TestClient):
    payload = {
        "name": "Test Bank Account",
        "type": "bank",
        "initial_balance": 1000.00,
        "active": True
    }
    response = client.post("/accounts/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["type"] == payload["type"]
    assert data["initial_balance"] == payload["initial_balance"]
    assert "id" in data

def test_create_credit_card_account(client: TestClient):
    payload = {
        "name": "Test Credit Card",
        "type": "credit_card",
        "closing_day": 10,
        "due_day": 15,
        "available_limit": 5000.00
    }
    response = client.post("/accounts/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["closing_day"] == payload["closing_day"]
    assert data["due_day"] == payload["due_day"]

def test_list_accounts(client: TestClient):
    # Create an account first
    client.post("/accounts/", json={"name": "Account 1", "type": "wallet"})
    
    response = client.get("/accounts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_account(client: TestClient):
    # Create
    create_res = client.post("/accounts/", json={"name": "To Get", "type": "bank"})
    account_id = create_res.json()["id"]
    
    # Get
    response = client.get(f"/accounts/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == account_id
    assert data["name"] == "To Get"

def test_get_account_not_found(client: TestClient):
    response = client.get(f"/accounts/{uuid4()}")
    assert response.status_code == 404

def test_update_account(client: TestClient):
    # Create
    create_res = client.post("/accounts/", json={"name": "To Update", "type": "bank"})
    account_id = create_res.json()["id"]
    
    # Update
    payload = {"name": "Updated Name", "initial_balance": 2000.0}
    response = client.put(f"/accounts/{account_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["initial_balance"] == 2000.0

def test_delete_account(client: TestClient):
    # Create
    create_res = client.post("/accounts/", json={"name": "To Delete", "type": "bank"})
    account_id = create_res.json()["id"]
    
    # Delete
    response = client.delete(f"/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    
    # Verify gone
    get_res = client.get(f"/accounts/{account_id}")
    assert get_res.status_code == 404
