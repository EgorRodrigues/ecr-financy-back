from fastapi.testclient import TestClient


def test_bank_statement_accounts_param(client: TestClient):
    # 1. Create Two Accounts
    r_acc1 = client.post(
        "/accounts/",
        json={"name": "Account 1", "type": "bank", "initial_balance": 1000.00, "active": True},
    )
    assert r_acc1.status_code == 200
    acc1_id = r_acc1.json()["id"]

    r_acc2 = client.post(
        "/accounts/",
        json={"name": "Account 2", "type": "bank", "initial_balance": 2000.00, "active": True},
    )
    assert r_acc2.status_code == 200
    acc2_id = r_acc2.json()["id"]

    # 2. Call with accounts param (singular value in list)
    # Using 'accounts' query param instead of account_ids
    # FastAPI handles list query params by repeating key: ?accounts=id1&accounts=id2
    # But requests/TestClient usually takes a list.

    # Test case A: Filter only Account 1
    response = client.get(f"/bank-statement/?accounts={acc1_id}")
    assert response.status_code == 200
    data = response.json()

    # Should be 1000 (initial balance of acc1)
    # Note: no transactions created, so balance = initial_balance
    assert data["account_balance"] == 1000.00

    # Test case B: Filter only Account 2
    response = client.get(f"/bank-statement/?accounts={acc2_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["account_balance"] == 2000.00

    # Test case C: Filter Both using 'accounts'
    response = client.get(f"/bank-statement/?accounts={acc1_id}&accounts={acc2_id}")
    assert response.status_code == 200
    data = response.json()
    # 1000 + 2000 = 3000
    assert data["account_balance"] == 3000.00

    # Test case D: Mixed usage (account_id + accounts) - should merge
    response = client.get(f"/bank-statement/?account_id={acc1_id}&accounts={acc2_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["account_balance"] == 3000.00
