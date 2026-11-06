from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_service_metadata() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ipguard-api",
        "version": "1.0.0",
    }


def test_unknown_route_uses_consistent_error_shape() -> None:
    response = client.get("/api/v1/not-a-route")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["message"] == "Not Found"
