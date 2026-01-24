from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_bank_statement_balance_persistence(client: TestClient):
    # 1. Create Account
    r_acc = client.post(
        "/accounts/",
        json={"name": "Balance Test", "type": "bank", "initial_balance": 1000.00, "active": True},
    )
    aid = r_acc.json()["id"]

    # 2. Add Income (Yesterday)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(
        "/incomes/",
        json={
            "amount": 500.00,
            "total_received": 500.00,
            "status": "recebido",
            "receipt_date": yesterday,
            "description": "Old Income",
            "account": aid,
            "active": True,
        },
    )

    # 3. Get Statement for Future Date Range (No transactions should appear)
    future_start = (date.today() + timedelta(days=10)).isoformat()
    future_end = (date.today() + timedelta(days=20)).isoformat()

    response = client.get(
        f"/bank-statement/?start_date={future_start}&end_date={future_end}&account_id={aid}"
    )
    assert response.status_code == 200
    data = response.json()

    # Transactions list should be empty
    assert len(data["transactions"]) == 0

    # BUT Current Balance should be 1500 (1000 + 500)
    # Because "Current Balance" is the state of the account NOW, regardless of the view window.
    assert data["account_balance"] == 1500.00
