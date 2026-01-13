from datetime import date
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import insert
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import verify_token
from app.db.postgres import contacts, incomes


def ensure_auth_override():
    app.dependency_overrides[verify_token] = lambda: {"sub": "testuser"}


def test_incomes_by_customer_empty(client: TestClient):
    ensure_auth_override()
    res = client.get("/reports/incomes-by-customer")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_incomes_by_customer_with_data(session, client: TestClient):
    ensure_auth_override()
    contact_id = uuid4()
    session.execute(
        insert(contacts).values(
            id=contact_id, type="customer", person_type="company", name="Cliente Teste", active=True
        )
    )
    session.execute(
        insert(incomes).values(
            amount=Decimal("250.00"),
            status="recebido",
            receipt_date=date(2025, 2, 10),
            contact_id=str(contact_id),
            active=True,
        )
    )
    session.flush()

    url = "/reports/incomes-by-customer?start_date=2025-02-01&end_date=2025-02-28"
    res = client.get(url)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    item = next((i for i in data if i["contact_id"] == str(contact_id)), None)
    assert item is not None
    assert item["contact_name"] == "Cliente Teste"
    assert item["total_amount"] == 250.0

