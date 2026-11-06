from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_allowed_frontend_origin_receives_cors_header() -> None:
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_unknown_origin_does_not_receive_cors_header() -> None:
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://malicious.example"},
    )

    assert "access-control-allow-origin" not in response.headers
