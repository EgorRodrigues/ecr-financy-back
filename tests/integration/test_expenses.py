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
