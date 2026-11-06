from collections.abc import Generator
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app

client = TestClient(app)


class BrokenSession:
    def execute(self, *_: Any, **__: Any) -> None:
        raise OperationalError(
            "SELECT 1",
            {},
            Exception("simulated database outage with private details"),
        )


def override_database() -> Generator[BrokenSession, None, None]:
    yield BrokenSession()


def test_database_failure_returns_generic_error() -> None:
    app.dependency_overrides[get_db] = override_database
    try:
        response = client.get("/api/v1/health/database")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "database_unavailable"
    assert payload["error"]["message"] == "PostgreSQL is unavailable."
    assert "private details" not in response.text
    assert "password" not in response.text.lower()
