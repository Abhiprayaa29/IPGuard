from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_info_returns_non_sensitive_metadata() -> None:
    response = client.get("/api/v1/system/info")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "name": "IPGuard",
        "version": "1.0.0",
        "environment": "development",
        "api_version": "v1",
        "database_engine": "postgresql",
    }
    assert "password" not in response.text.lower()
    assert "database_url" not in response.text.lower()
