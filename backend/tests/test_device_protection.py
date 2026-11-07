import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def test_device_listing_without_key_returns_401() -> None:
    response = client.get("/api/v1/auth/devices")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "unauthorized_admin_access"


def test_device_listing_with_invalid_key_returns_401() -> None:
    response = client.get(
        "/api/v1/auth/devices",
        headers={"X-Dev-Admin-Key": "wrong-secret-key-12345"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "unauthorized_admin_access"


def test_device_listing_with_valid_key_in_dev_returns_200() -> None:
    settings = get_settings()
    response = client.get(
        "/api/v1/auth/devices",
        headers={"X-Dev-Admin-Key": settings.dev_admin_key},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_device_listing_strictly_disabled_in_production() -> None:
    # Simulate production configuration
    def override_settings() -> Settings:
        current = get_settings()
        return Settings(
            database_url=str(current.database_url),
            app_env="production",
            dev_admin_key="some-secret",
        )

    app.dependency_overrides[get_settings] = override_settings
    try:
        # Even with valid key, production must reject with 403
        response = client.get(
            "/api/v1/auth/devices",
            headers={"X-Dev-Admin-Key": "some-secret"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "endpoint_disabled_in_production"

        # Without key in production, also rejected
        res_nokey = client.get("/api/v1/auth/devices")
        assert res_nokey.status_code == 403
        assert res_nokey.json()["error"]["code"] == "endpoint_disabled_in_production"
    finally:
        app.dependency_overrides.clear()
