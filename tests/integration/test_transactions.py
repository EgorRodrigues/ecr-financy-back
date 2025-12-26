from fastapi.testclient import TestClient

def test_create_transaction(client: TestClient):
    payload = {
        "amount": 1000,
        "description": "Salary",
        "active": True
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 1000
    assert data["description"] == "Salary"
    assert "id" in data

def test_list_transactions(client: TestClient):
    client.post("/transactions/", json={"amount": 50, "description": "Coffee"})
    response = client.get("/transactions/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_get_transaction(client: TestClient):
    res = client.post("/transactions/", json={"amount": 200, "description": "Book"})
    tid = res.json()["id"]
    
    response = client.get(f"/transactions/{tid}")
    assert response.status_code == 200
    assert response.json()["description"] == "Book"

def test_get_transaction_not_found(client: TestClient):
    from uuid import uuid4
    response = client.get(f"/transactions/{uuid4()}")
    assert response.status_code == 404
