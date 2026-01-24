from datetime import date

from fastapi.testclient import TestClient


def test_financial_forecast(client: TestClient):
    start_date = str(date.today())
    # end_date 30 days from now
    from datetime import timedelta

    end_date = str(date.today() + timedelta(days=30))

    url = f"/financial-forecast/?startDate={start_date}&endDate={end_date}"
    res = client.get(url)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
