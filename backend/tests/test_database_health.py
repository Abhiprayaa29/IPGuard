from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_database_health_uses_real_connection() -> None:
    response = client.get("/api/v1/health/database")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "postgresql"
    assert isinstance(payload["latency_ms"], float)
    assert payload["latency_ms"] >= 0
