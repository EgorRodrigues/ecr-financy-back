import calendar
from datetime import date
from fastapi.testclient import TestClient

def test_list_expenses_with_transfer(client: TestClient):
    # Create contacts
    contact1_res = client.post("/contacts/", json={"name": "Test Supplier 1", "type": "supplier", "person_type": "company"})
    assert contact1_res.status_code == 200
    contact1_id = contact1_res.json()["id"]

    contact2_res = client.post("/contacts/", json={"name": "Test Supplier 2", "type": "supplier", "person_type": "company"})
    assert contact2_res.status_code == 200
    contact2_id = contact2_res.json()["id"]

    # Create accounts
    account1_res = client.post("/accounts/", json={"name": "Test Account 1", "type": "bank", "initial_balance": 1000, "contact_id": contact1_id})
    assert account1_res.status_code == 200
    account1_id = account1_res.json()["id"]

    account2_res = client.post("/accounts/", json={"name": "Test Account 2", "type": "bank", "initial_balance": 500, "contact_id": contact2_id})
    assert account2_res.status_code == 200
    account2_id = account2_res.json()["id"]

    # Create a transfer
    transfer_payload = {
        "amount": 100,
        "source_account_id": account1_id,
        "destination_account_id": account2_id,
        "date": str(date.today()),
    }
    transfer_res = client.post("/transfers/", json=transfer_payload)
    assert transfer_res.status_code == 201
    transfer_id = transfer_res.json()["transfer_id"]

    # List expenses
    response = client.get("/expenses/")
    assert response.status_code == 200

    # Check if the created expense is in the list and has the transfer_id
    expenses = response.json()
    assert len(expenses) > 0
    
    transfer_expense = None
    for expense in expenses:
        if expense.get("transfer_id") == transfer_id:
            transfer_expense = expense
            break
    
    assert transfer_expense is not None
    assert transfer_expense["amount"] == 100


def test_create_expense_installments_group(client: TestClient):
    def add_months(d: date, months: int) -> date:
        month_index = (d.month - 1) + months
        year = d.year + (month_index // 12)
        month = (month_index % 12) + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(d.day, last_day)
        return d.replace(year=year, month=month, day=day)

    contact_res = client.post(
        "/contacts/", json={"name": "Supplier", "type": "supplier", "person_type": "company"}
    )
    assert contact_res.status_code == 200
    contact_id = contact_res.json()["id"]

    account_res = client.post(
        "/accounts/",
        json={"name": "Account", "type": "bank", "initial_balance": 1000, "contact_id": contact_id},
    )
    assert account_res.status_code == 200
    account_id = account_res.json()["id"]

    today = date.today()
    payload = {
        "amount_total": 100,
        "installments_total": 3,
        "issue_date": str(today),
        "first_due_date": str(today),
        "contact_id": contact_id,
        "description": "Compra parcelada",
        "account_id": account_id,
        "status": "pendente",
    }

    res = client.post("/expenses/installments", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "group" in data
    assert "expenses" in data
    assert data["group"]["amount_total"] == 100
    assert data["group"]["installments_total"] == 3

    expenses = data["expenses"]
    assert len(expenses) == 3
    group_id = data["group"]["id"]

    for idx, exp in enumerate(expenses, start=1):
        assert exp["installment_group_id"] == group_id
        assert exp["installment_number"] == idx
        assert exp["installments_total"] == 3
        assert exp["description"] == f"Compra parcelada ({idx}/3)"

    assert sum(e["amount"] for e in expenses) == 100

    assert expenses[0]["due_date"] == str(today)
    assert expenses[1]["due_date"] == str(add_months(today, 1))
    assert expenses[2]["due_date"] == str(add_months(today, 2))


def test_installment_group_summary_and_actions(client: TestClient):
    contact_res = client.post(
        "/contacts/", json={"name": "Supplier", "type": "supplier", "person_type": "company"}
    )
    assert contact_res.status_code == 200
    contact_id = contact_res.json()["id"]

    account_res = client.post(
        "/accounts/",
        json={"name": "Account", "type": "bank", "initial_balance": 1000, "contact_id": contact_id},
    )
    assert account_res.status_code == 200
    account_id = account_res.json()["id"]

    today = date.today()
    payload = {
        "amount_total": 90,
        "installments_total": 3,
        "issue_date": str(today),
        "first_due_date": str(today),
        "contact_id": contact_id,
        "description": "Plano A",
        "account_id": account_id,
        "status": "pendente",
    }

    create_res = client.post("/expenses/installments", json=payload)
    assert create_res.status_code == 200
    group_id = create_res.json()["group"]["id"]

    list_res = client.get("/expenses/installment-groups", params={"account_id": account_id})
    assert list_res.status_code == 200
    groups = list_res.json()
    assert len(groups) >= 1
    group = next((g for g in groups if g["id"] == group_id), None)
    assert group is not None
    assert group["description"] == "Plano A"
    assert group["expenses_count"] == 3
    assert group["pending_count"] == 3
    assert group["paid_count"] == 0
    assert group["canceled_count"] == 0

    upd_res = client.put(
        f"/expenses/installment-groups/{group_id}", json={"description": "Plano A (editado)"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["description"] == "Plano A (editado)"

    cancel_res = client.post(f"/expenses/installment-groups/{group_id}/cancel")
    assert cancel_res.status_code == 200
    cancel_data = cancel_res.json()
    assert cancel_data["group"]["id"] == group_id
    assert all(e["status"] == "cancelado" for e in cancel_data["expenses"])

    deactivate_res = client.post(f"/expenses/installment-groups/{group_id}/deactivate")
    assert deactivate_res.status_code == 200
    deact_data = deactivate_res.json()
    assert deact_data["group"]["active"] is False
    assert all(e["active"] is False for e in deact_data["expenses"])
