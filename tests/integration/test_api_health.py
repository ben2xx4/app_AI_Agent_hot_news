from __future__ import annotations


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database_url"].startswith("sqlite:///")
    assert body["database_driver"].startswith("sqlite")
