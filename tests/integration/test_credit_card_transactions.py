from datetime import date

from fastapi.testclient import TestClient


def test_create_cc_transaction(client: TestClient):
    # Create Contact first
    con_res = client.post("/contacts/", json={"name": "Bank Contact", "type": "supplier", "person_type": "company"})
    assert con_res.status_code == 200
    contact_id = con_res.json()["id"]

    # Create Credit Card Account
    acc_payload = {
        "name": "My CC",
        "type": "credit_card",
        "closing_day": 5,
        "due_day": 10,
        "available_limit": 1000.0,
        "contact_id": contact_id,
    }
    acc_res = client.post("/accounts/", json=acc_payload)
    assert acc_res.status_code == 200
    account_id = acc_res.json()["id"]

    # Create Transaction
    tx_payload = {
        "amount": 100.50,
        "description": "Lunch",
        "account_id": account_id,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),  # Just setting a date to trigger invoice creation
        "status": "pendente",
    }
    response = client.post("/credit-card-transactions/", json=tx_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 100.50
    assert data["account_id"] == account_id
    assert "invoice_id" in data
    assert data["invoice_id"] is not None


def _create_cc_transaction_helper(client: TestClient):
    # Create Contact first
    con_res = client.post("/contacts/", json={"name": "Bank Contact Helper", "type": "supplier", "person_type": "company"})
    contact_id = con_res.json()["id"]

    # Create Credit Card Account
    acc_payload = {
        "name": "My CC Helper",
        "type": "credit_card",
        "closing_day": 5,
        "due_day": 10,
        "available_limit": 1000.0,
        "contact_id": contact_id,
    }
    acc_res = client.post("/accounts/", json=acc_payload)
    account_id = acc_res.json()["id"]

    # Create Transaction
    tx_payload = {
        "amount": 100.50,
        "description": "Lunch Helper",
        "account_id": account_id,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),
        "status": "pendente",
    }
    response = client.post("/credit-card-transactions/", json=tx_payload)
    data = response.json()
    return account_id, data["id"]


def test_get_cc_summary(client: TestClient):
    account_id, _ = _create_cc_transaction_helper(client)

    response = client.get(f"/credit-card-transactions/summary/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_limit"] == 1000.0
    # Available limit should decrease
    assert data["available_limit"] == 1000.0 - 100.50
    assert len(data["transactions"]) >= 1
    assert data["current_invoice"] is not None


def test_list_cc_transactions(client: TestClient):
    account_id, _ = _create_cc_transaction_helper(client)

    # List all
    response = client.get("/credit-card-transactions/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # Filter by account
    response = client.get(f"/credit-card-transactions/?account_id={account_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_cc_transaction(client: TestClient):
    _, tx_id = _create_cc_transaction_helper(client)

    response = client.get(f"/credit-card-transactions/{tx_id}")
    assert response.status_code == 200
    assert response.json()["id"] == tx_id


def test_update_cc_transaction(client: TestClient):
    _, tx_id = _create_cc_transaction_helper(client)

    response = client.put(
        f"/credit-card-transactions/{tx_id}",
        json={"description": "Updated Lunch", "amount": 200.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated Lunch"
    assert data["amount"] == 200.00


def test_delete_cc_transaction(client: TestClient):
    _, tx_id = _create_cc_transaction_helper(client)

    response = client.delete(f"/credit-card-transactions/{tx_id}")
    assert response.status_code == 200

    assert client.get(f"/credit-card-transactions/{tx_id}").status_code == 404


def test_cc_transaction_installments_group_flow(client: TestClient):
    con_res = client.post(
        "/contacts/", json={"name": "Bank Contact - Installments", "type": "supplier", "person_type": "company"}
    )
    assert con_res.status_code == 200
    contact_id = con_res.json()["id"]

    acc_payload = {
        "name": "My CC - Installments",
        "type": "credit_card",
        "closing_day": 5,
        "due_day": 10,
        "available_limit": 1000.0,
        "contact_id": contact_id,
    }
    acc_res = client.post("/accounts/", json=acc_payload)
    assert acc_res.status_code == 200
    account_id = acc_res.json()["id"]

    today = date.today()
    payload = {
        "amount_total": 300,
        "installments_total": 3,
        "issue_date": str(today),
        "first_due_date": str(today),
        "account_id": account_id,
        "description": "Compra 3x",
        "status": "pendente",
    }

    create_res = client.post("/credit-card-transactions/installments", json=payload)
    assert create_res.status_code == 200
    data = create_res.json()
    group_id = data["group"]["id"]
    assert data["group"]["installments_total"] == 3
    assert len(data["transactions"]) == 3
    assert sum(t["amount"] for t in data["transactions"]) == 300
    assert all(t["installment_group_id"] == group_id for t in data["transactions"])
    assert all(t["installments_total"] == 3 for t in data["transactions"])
    assert [t["installment_number"] for t in data["transactions"]] == [1, 2, 3]
    assert all(t["invoice_id"] is not None for t in data["transactions"])

    summary_res = client.get(f"/credit-card-transactions/summary/{account_id}")
    assert summary_res.status_code == 200
    assert summary_res.json()["available_limit"] == 700.0

    list_groups = client.get(
        "/credit-card-transactions/installment-groups", params={"account_id": account_id}
    )
    assert list_groups.status_code == 200
    groups = list_groups.json()
    assert next((g for g in groups if g["id"] == group_id), None) is not None

    upd_res = client.put(
        f"/credit-card-transactions/installment-groups/{group_id}",
        json={"description": "Compra 3x (editada)"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["description"] == "Compra 3x (editada)"

    cancel_res = client.post(f"/credit-card-transactions/installment-groups/{group_id}/cancel")
    assert cancel_res.status_code == 200
    cancel_data = cancel_res.json()
    assert all(t["status"] == "cancelado" for t in cancel_data["transactions"])

    summary_res2 = client.get(f"/credit-card-transactions/summary/{account_id}")
    assert summary_res2.status_code == 200
    assert summary_res2.json()["available_limit"] == 1000.0
