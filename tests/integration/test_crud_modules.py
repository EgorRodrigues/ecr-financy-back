from datetime import date

from fastapi.testclient import TestClient


# --- Incomes ---
def test_income_lifecycle(client: TestClient):
    # Create Account and Contact first
    acc_res = client.post("/accounts/", json={"name": "Bank Account", "type": "bank"})
    assert acc_res.status_code == 200
    account_id = acc_res.json()["id"]

    con_res = client.post("/contacts/", json={"name": "Contact", "type": "customer", "person_type": "individual"})
    assert con_res.status_code == 200
    contact_id = con_res.json()["id"]

    # Create
    payload = {
        "amount": 5000,
        "description": "Salary",
        "status": "recebido",
        "issue_date": str(date.today()),
        "account_id": account_id,
        "contact_id": contact_id,
    }
    res = client.post("/incomes/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

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


def test_income_installments_group_summary_and_actions(client: TestClient):
    acc_res = client.post("/accounts/", json={"name": "Bank Account", "type": "bank"})
    assert acc_res.status_code == 200
    account_id = acc_res.json()["id"]

    con_res = client.post(
        "/contacts/", json={"name": "Customer", "type": "customer", "person_type": "individual"}
    )
    assert con_res.status_code == 200
    contact_id = con_res.json()["id"]

    today = date.today()
    payload = {
        "amount_total": 300,
        "installments_total": 3,
        "issue_date": str(today),
        "first_due_date": str(today),
        "contact_id": contact_id,
        "description": "Contrato parcelado",
        "account_id": account_id,
        "status": "pendente",
    }

    create_res = client.post("/incomes/installments", json=payload)
    assert create_res.status_code == 200
    data = create_res.json()
    group_id = data["group"]["id"]
    assert len(data["incomes"]) == 3
    assert sum(i["amount"] for i in data["incomes"]) == 300
    assert [i["description"] for i in data["incomes"]] == [
        "Contrato parcelado (1/3)",
        "Contrato parcelado (2/3)",
        "Contrato parcelado (3/3)",
    ]

    list_res = client.get("/incomes/installment-groups", params={"account_id": account_id})
    assert list_res.status_code == 200
    groups = list_res.json()
    group = next((g for g in groups if g["id"] == group_id), None)
    assert group is not None
    assert group["incomes_count"] == 3
    assert group["pending_count"] == 3
    assert group["received_count"] == 0
    assert group["canceled_count"] == 0

    upd_res = client.put(
        f"/incomes/installment-groups/{group_id}", json={"description": "Contrato (editado)"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["description"] == "Contrato (editado)"

    cancel_res = client.post(f"/incomes/installment-groups/{group_id}/cancel")
    assert cancel_res.status_code == 200
    cancel_data = cancel_res.json()
    assert all(i["status"] == "cancelado" for i in cancel_data["incomes"])

    deactivate_res = client.post(f"/incomes/installment-groups/{group_id}/deactivate")
    assert deactivate_res.status_code == 200
    deact_data = deactivate_res.json()
    assert deact_data["group"]["active"] is False
    assert all(i["active"] is False for i in deact_data["incomes"])


# --- Expenses ---
def test_expense_lifecycle(client: TestClient):
    # Create Account and Contact first
    acc_res = client.post("/accounts/", json={"name": "Bank Account", "type": "bank"})
    assert acc_res.status_code == 200
    account_id = acc_res.json()["id"]

    con_res = client.post("/contacts/", json={"name": "Contact", "type": "supplier", "person_type": "individual"})
    assert con_res.status_code == 200
    contact_id = con_res.json()["id"]

    # Create
    payload = {
        "amount": 100,
        "description": "Groceries",
        "status": "pago",
        "issue_date": str(date.today()),
        "account_id": account_id,
        "contact_id": contact_id,
    }
    res = client.post("/expenses/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

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


# --- Cost Centers ---
def test_cost_center_lifecycle(client: TestClient):
    # Create
    payload = {"name": "IT Department", "description": "Tech stuff", "active": True}
    res = client.post("/cost-centers/", json=payload)
    assert res.status_code == 200
    item_id = res.json()["id"]

    # List
    res = client.get("/cost-centers/")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update
    res = client.put(f"/cost-centers/{item_id}", json={"name": "Engineering"})
    assert res.status_code == 200
    assert res.json()["name"] == "Engineering"

    # Delete
    res = client.delete(f"/cost-centers/{item_id}")
    assert res.status_code == 200


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
