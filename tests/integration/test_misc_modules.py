from fastapi.testclient import TestClient
from datetime import date

def test_health(client: TestClient):
    res = client.get("/health/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_dashboard(client: TestClient):
    # Ensure at least one transaction exists (optional, but good for real-world check)
    # We can create a transaction or just rely on empty state returning valid empty structure
    res = client.get("/dashboard/?months=6&recent_limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "big_numbers" in data
    assert "monthly" in data
    assert "recent_transactions" in data

def test_financial_forecast(client: TestClient):
    start_date = str(date.today())
    # end_date 30 days from now
    from datetime import timedelta
    end_date = str(date.today() + timedelta(days=30))
    
    url = f"/financial-forecast/?startDate={start_date}&endDate={end_date}"
    res = client.get(url)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
