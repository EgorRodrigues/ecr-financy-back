from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import insert

from app.core.security import verify_token
from app.db.postgres import categories, expenses
from app.main import app


def ensure_auth_override():
    app.dependency_overrides[verify_token] = lambda: {"sub": "testuser"}


def test_expenses_by_category_empty(client: TestClient):
    ensure_auth_override()
    res = client.get("/reports/expenses-by-category")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_expenses_by_category_with_data(session, client: TestClient):
    ensure_auth_override()
    cid = uuid4()
    session.execute(insert(categories).values(id=cid, name="Categoria Teste", active=True))
    session.execute(
        insert(expenses).values(
            amount=Decimal("150.00"),
            status="pago",
            payment_date=date(2025, 1, 10),
            category_id=str(cid),
            active=True,
        )
    )
    session.flush()

    url = "/reports/expenses-by-category?start_date=2025-01-01&end_date=2025-01-31"
    res = client.get(url)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = next((i for i in data if i["category_id"] == str(cid)), None)
    assert item is not None
    assert item["category_name"] == "Categoria Teste"
    assert item["total_amount"] == 150.0
