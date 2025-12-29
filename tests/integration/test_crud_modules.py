from fastapi.testclient import TestClient
from datetime import date


# --- Incomes ---
def test_income_lifecycle(client: TestClient):
    # Create
    payload = {
        "amount": 5000,
        "description": "Salary",
        "status": "recebido",
        "issue_date": str(date.today()),
    }
    res = client.post("/incomes/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

    # Get
    res = client.get(f"/incomes/{item_id}")
    assert res.status_code == 200
    assert res.json()["description"] == "Salary"

    # List
    res = client.get("/incomes/")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update
    res = client.put(f"/incomes/{item_id}", json={"description": "Updated Salary", "amount": 5500})
    assert res.status_code == 200
    assert res.json()["amount"] == 5500

    # Delete
    res = client.delete(f"/incomes/{item_id}")
    assert res.status_code == 200
    assert client.get(f"/incomes/{item_id}").status_code == 404


# --- Expenses ---
def test_expense_lifecycle(client: TestClient):
    # Create
    payload = {
        "amount": 100,
        "description": "Groceries",
        "status": "pago",
        "issue_date": str(date.today()),
    }
    res = client.post("/expenses/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

    # Get
    res = client.get(f"/expenses/{item_id}")
    assert res.status_code == 200
    assert res.json()["description"] == "Groceries"

    # List
    res = client.get("/expenses/")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update
    res = client.put(f"/expenses/{item_id}", json={"description": "More Groceries", "amount": 150})
    assert res.status_code == 200
    assert res.json()["amount"] == 150

    # Delete
    res = client.delete(f"/expenses/{item_id}")
    assert res.status_code == 200
    assert client.get(f"/expenses/{item_id}").status_code == 404


# --- Cost Centers ---
def test_cost_center_lifecycle(client: TestClient):
    # Create
    payload = {"name": "IT Department", "description": "Tech stuff", "active": True}
    res = client.post("/cost-centers/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

    # Get
    res = client.get(f"/cost-centers/{item_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "IT Department"

    # List
    res = client.get("/cost-centers/")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update
    res = client.patch(f"/cost-centers/{item_id}", json={"name": "Engineering"})
    assert res.status_code == 200
    assert res.json()["name"] == "Engineering"

    # Delete
    res = client.delete(f"/cost-centers/{item_id}")
    assert res.status_code == 200
    assert client.get(f"/cost-centers/{item_id}").status_code == 404


# --- Contacts ---
def test_contact_lifecycle(client: TestClient):
    # Create
    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "type": "customer",
        "person_type": "individual",
    }
    res = client.post("/contacts/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

    # Get
    res = client.get(f"/contacts/{item_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "John Doe"

    # List
    res = client.get("/contacts/")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update
    res = client.put(f"/contacts/{item_id}", json={"name": "Jane Doe"})
    assert res.status_code == 200
    assert res.json()["name"] == "Jane Doe"

    # Delete
    res = client.delete(f"/contacts/{item_id}")
    assert res.status_code == 200
    assert client.get(f"/contacts/{item_id}").status_code == 404
