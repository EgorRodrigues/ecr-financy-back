from datetime import date
from uuid import uuid4
from fastapi.testclient import TestClient

def test_financial_forecast_execution(client: TestClient):
    # 1. Setup Data
    # Create Account
    r_acc = client.post("/accounts/", json={"name": "Forecast Acc", "type": "bank", "initial_balance": 1000})
    assert r_acc.status_code == 200
    aid = r_acc.json()["id"]

    # Create Category
    r_cat = client.post("/categories/", json={"name": "Forecast Cat", "active": True})
    assert r_cat.status_code == 200
    cid = r_cat.json()["id"]

    # Create Income
    client.post("/incomes/", json={
        "amount": 500,
        "total_received": 500,
        "status": "recebido",
        "receipt_date": date.today().isoformat(),
        "description": "Forecast Inc",
        "account_id": aid,
        "category_id": cid
    })

    # Create Expense
    client.post("/expenses/", json={
        "amount": 200,
        "total_paid": 200,
        "status": "pago",
        "payment_date": date.today().isoformat(),
        "description": "Forecast Exp",
        "account_id": aid,
        "category_id": cid
    })

    # 2. Call Endpoint
    # Use a wide range to ensure we hit the logic
    today = date.today().isoformat()
    # Assuming start/end date params are required
    response = client.get(f"/financial-forecast/?startDate={today}&endDate={today}")
    
    # 3. Assertions
    # If the bug persists (UUID=TEXT), this will be 500.
    assert response.status_code == 200, f"Failed with {response.text}"
    
    data = response.json()
    assert isinstance(data, list)
    # We might verify content, but main goal is ensuring query execution works
    assert all("description" in item for item in data)
