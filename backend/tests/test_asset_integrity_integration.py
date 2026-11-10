"""HTTP integration tests for Asset Integrity Monitoring."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.api.deps import get_current_authenticated_device
from app.api.routes.assets import get_asset_integrity_status, router as assets_router
from app.core.errors import AppError
from app.db.base import Base
from app.models.asset import Asset
from app.models.auth import Device
from app.services import asset_integrity, asset_storage, assets as assets_service
from app.services.asset_integrity import IntegrityCheckResult


@pytest.fixture
def api_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'asset-integrity-api.sqlite'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    settings = type(
        "AssetTestSettings",
        (),
        {
            "asset_vault_max_file_size_bytes": 50 * 1024 * 1024,
            "storage_directory": storage_dir,
        },
    )()
    monkeypatch.setattr(assets_service, "get_settings", lambda: settings)
    monkeypatch.setattr(asset_storage, "get_settings", lambda: settings)
    test_key = b"I" * 32
    monkeypatch.setattr(assets_service, "derive_asset_key", lambda _device_id: test_key)

    device_ids = {
        "owner": f"integrity-owner-{uuid.uuid4().hex[:8]}",
        "other": f"integrity-other-{uuid.uuid4().hex[:8]}",
    }
    with factory.begin() as db:
        for role, device_id in device_ids.items():
            db.add(
                Device(
                    device_id=device_id,
                    device_name=f"Test {role}",
                    model="Test Device",
                    android_version="14",
                    public_key_x509="test-public-key",
                    public_key_fingerprint=f"fp:{uuid.uuid4().hex}",
                    status="ACTIVE",
                )
            )

    try:
        with factory() as db:
            owner = db.query(Device).filter(Device.device_id == device_ids["owner"]).first()
            other = db.query(Device).filter(Device.device_id == device_ids["other"]).first()
            yield {
                "db": db,
                "factory": factory,
                "device_ids": device_ids,
                "owner": owner,
                "other": other,
                "storage_dir": storage_dir,
            }
    finally:
        engine.dispose()


def upload_text_asset(api_context) -> uuid.UUID:
    asset = assets_service.create_asset(
        db=api_context["db"],
        device_id=api_context["owner"].device_id,
        filename="proof.txt",
        content_type="text/plain",
        data=b"M4 integrity fixture",
    )
    return asset.id


def _create_asset(api_context):
    return assets_service.create_asset(
        db=api_context["db"],
        device_id=api_context["owner"].device_id,
        filename="proof.txt",
        content_type="text/plain",
        data=b"M4 integrity fixture",
    )


def test_upload_uses_final_ciphertext_baseline_and_download_verifies(api_context):
    asset_id = upload_text_asset(api_context)
    asset = api_context["db"].get(Asset, asset_id)
    assert asset is not None
    ciphertext_path = api_context["storage_dir"] / asset.storage_key
    assert asset.sha256_hash == hashlib.sha256(ciphertext_path.read_bytes()).hexdigest()
    assert asset.integrity_status == "PENDING"
    assert asset.last_checked_at is None
    assert asset.last_observed_sha256 is None

    downloaded, content = assets_service.download_asset(
        api_context["db"], asset_id, api_context["owner"].device_id
    )
    assert downloaded.id == asset_id
    assert content == b"M4 integrity fixture"
    refreshed = api_context["db"].get(Asset, asset_id)
    api_context["db"].refresh(refreshed)
    assert refreshed.integrity_status == "VERIFIED"
    assert refreshed.last_observed_sha256 == refreshed.sha256_hash


def test_download_mismatch_fails_before_decryption(api_context, monkeypatch):
    asset_id = upload_text_asset(api_context)
    asset = api_context["db"].get(Asset, asset_id)
    ciphertext_path = api_context["storage_dir"] / asset.storage_key
    ciphertext_path.write_bytes(b"tampered ciphertext")
    decrypt_called = False

    def forbidden_decrypt(*args, **kwargs):
        nonlocal decrypt_called
        decrypt_called = True
        raise AssertionError("decryption must not run after an integrity mismatch")

    monkeypatch.setattr(assets_service, "decrypt_asset_bytes", forbidden_decrypt)

    with pytest.raises(AppError) as raised:
        assets_service.download_asset(api_context["db"], asset_id, api_context["owner"].device_id)
    assert raised.value.status_code == 409
    assert raised.value.code == "integrity_check_failed"
    assert decrypt_called is False
    refreshed = api_context["db"].get(Asset, asset_id)
    api_context["db"].refresh(refreshed)
    assert refreshed.integrity_status == "MISMATCH"
    assert refreshed.sha256_hash != refreshed.last_observed_sha256


def test_download_missing_fails_closed_and_records_status(api_context):
    asset_id = upload_text_asset(api_context)
    asset = api_context["db"].get(Asset, asset_id)
    (api_context["storage_dir"] / asset.storage_key).unlink()

    with pytest.raises(AppError) as raised:
        assets_service.download_asset(api_context["db"], asset_id, api_context["owner"].device_id)
    assert raised.value.status_code == 404
    assert raised.value.code == "asset_file_missing"
    refreshed = api_context["db"].get(Asset, asset_id)
    api_context["db"].refresh(refreshed)
    assert refreshed.integrity_status == "MISSING"
    assert refreshed.sha256_hash != ""


def test_download_storage_error_fails_closed_and_records_status(api_context, monkeypatch):
    asset_id = upload_text_asset(api_context)

    def storage_error(*args, **kwargs):
        raise PermissionError("private storage detail")

    monkeypatch.setattr(asset_integrity, "inspect_ciphertext_file", storage_error)

    with pytest.raises(AppError) as raised:
        assets_service.download_asset(api_context["db"], asset_id, api_context["owner"].device_id)
    assert raised.value.status_code == 503
    assert raised.value.code == "asset_integrity_unavailable"
    assert "private storage detail" not in str(raised.value)
    refreshed = api_context["db"].get(Asset, asset_id)
    api_context["db"].refresh(refreshed)
    assert refreshed.integrity_status == "ERROR"


@pytest.mark.parametrize("status_value", ["PENDING", "", "UNKNOWN"])
def test_download_rejects_any_unrecognized_integrity_status(
    api_context, monkeypatch, status_value
):
    asset_id = upload_text_asset(api_context)
    decrypt_called = False

    def forbidden_decrypt(*args, **kwargs):
        nonlocal decrypt_called
        decrypt_called = True
        raise AssertionError("decryption must not run unless status is VERIFIED")

    monkeypatch.setattr(assets_service, "decrypt_asset_bytes", forbidden_decrypt)
    monkeypatch.setattr(
        assets_service,
        "verify_asset_integrity",
        lambda *args, **kwargs: IntegrityCheckResult(
            status=status_value,
            checked_at=datetime.now(timezone.utc),
            observed_sha256=None,
            ciphertext=b"unverified bytes",
        ),
    )

    with pytest.raises(AppError) as raised:
        assets_service.download_asset(api_context["db"], asset_id, api_context["owner"].device_id)

    assert raised.value.status_code == 503
    assert raised.value.code == "asset_integrity_unavailable"
    assert decrypt_called is False


def test_download_rejects_verified_result_without_captured_ciphertext(api_context, monkeypatch):
    asset_id = upload_text_asset(api_context)
    monkeypatch.setattr(
        assets_service,
        "verify_asset_integrity",
        lambda *args, **kwargs: IntegrityCheckResult(
            status="VERIFIED",
            checked_at=datetime.now(timezone.utc),
            observed_sha256="a" * 64,
            ciphertext=None,
        ),
    )

    with pytest.raises(AppError) as raised:
        assets_service.download_asset(api_context["db"], asset_id, api_context["owner"].device_id)

    assert raised.value.status_code == 503
    assert raised.value.code == "asset_integrity_unavailable"


def test_download_rejects_verified_result_without_committed_audit_event(
    api_context, monkeypatch
):
    asset_id = upload_text_asset(api_context)
    decrypt_called = False

    def forbidden_decrypt(*args, **kwargs):
        nonlocal decrypt_called
        decrypt_called = True
        raise AssertionError("decryption requires a committed integrity audit event")

    monkeypatch.setattr(assets_service, "decrypt_asset_bytes", forbidden_decrypt)
    monkeypatch.setattr(
        assets_service,
        "verify_asset_integrity",
        lambda *args, **kwargs: IntegrityCheckResult(
            status="VERIFIED",
            checked_at=datetime.now(timezone.utc),
            observed_sha256="a" * 64,
            ciphertext=b"unrecorded bytes",
            audit_recorded=False,
        ),
    )

    with pytest.raises(AppError) as raised:
        assets_service.download_asset(api_context["db"], asset_id, api_context["owner"].device_id)

    assert raised.value.status_code == 503
    assert raised.value.code == "asset_integrity_unavailable"
    assert decrypt_called is False


def test_precommit_failure_cleans_up_ciphertext(api_context, monkeypatch):
    stored = asset_storage.store_ciphertext_file
    captured = {}

    def capture_store(ciphertext):
        result = stored(ciphertext)
        captured.update(result)
        return result

    def fail_flush():
        raise RuntimeError("flush rejected")

    monkeypatch.setattr(assets_service, "store_ciphertext_file", capture_store)
    monkeypatch.setattr(api_context["db"], "flush", fail_flush)

    with pytest.raises(AppError) as raised:
        _create_asset(api_context)

    assert raised.value.code == "database_commit_failed"
    assert not (api_context["storage_dir"] / captured["storage_key"]).exists()


def test_commit_outcome_unknown_preserves_file_and_logs_reconciliation_key(
    api_context, monkeypatch, caplog
):
    stored = asset_storage.store_ciphertext_file
    captured = {}

    def capture_store(ciphertext):
        result = stored(ciphertext)
        captured.update(result)
        return result

    def fail_commit():
        raise OSError("connection outcome uncertain")

    monkeypatch.setattr(assets_service, "store_ciphertext_file", capture_store)
    monkeypatch.setattr(api_context["db"], "commit", fail_commit)

    with pytest.raises(AppError) as raised:
        _create_asset(api_context)

    assert raised.value.code == "database_commit_failed"
    assert (api_context["storage_dir"] / captured["storage_key"]).is_file()
    assert "asset_upload_commit_outcome_unknown" in caplog.text
    assert captured["storage_key"] in caplog.text
    assert "connection outcome uncertain" not in caplog.text


def test_cleanup_failure_is_logged_without_exception_details(
    api_context, monkeypatch, caplog
):
    stored = asset_storage.store_ciphertext_file
    captured = {}

    def capture_store(ciphertext):
        result = stored(ciphertext)
        captured.update(result)
        return result

    def fail_flush():
        raise RuntimeError("flush rejected")

    monkeypatch.setattr(assets_service, "store_ciphertext_file", capture_store)
    monkeypatch.setattr(api_context["db"], "flush", fail_flush)
    monkeypatch.setattr(assets_service, "delete_stored_file", lambda _key: False)

    with pytest.raises(AppError):
        _create_asset(api_context)

    assert "asset_upload_orphan_cleanup_failed" in caplog.text
    assert captured["storage_key"] in caplog.text
    assert "flush rejected" not in caplog.text


def test_postcommit_refresh_failure_does_not_delete_file_or_row(
    api_context, monkeypatch, caplog
):
    stored = asset_storage.store_ciphertext_file
    captured = {}

    def capture_store(ciphertext):
        result = stored(ciphertext)
        captured.update(result)
        return result

    def fail_refresh(_asset):
        raise OSError("refresh unavailable")

    monkeypatch.setattr(assets_service, "store_ciphertext_file", capture_store)
    monkeypatch.setattr(api_context["db"], "refresh", fail_refresh)

    with pytest.raises(AppError) as raised:
        _create_asset(api_context)

    assert raised.value.code == "asset_saved_refresh_failed"
    assert (api_context["storage_dir"] / captured["storage_key"]).is_file()
    with api_context["factory"]() as observer:
        saved = observer.query(Asset).filter_by(storage_key=captured["storage_key"]).one()
        assert saved.sha256_hash == captured["sha256_hash"]
    assert "asset_upload_postcommit_refresh_failed" in caplog.text


def test_integrity_api_is_owner_scoped_and_returns_only_public_metadata(api_context):
    asset_id = upload_text_asset(api_context)
    own_response = get_asset_integrity_status(
        asset_id, api_context["db"], api_context["owner"]
    )
    assert own_response.model_dump(mode="json") == {
        "asset_id": str(asset_id),
        "integrity_status": "PENDING",
        "last_checked_at": None,
    }
    assert "storage_key" not in own_response.model_dump()
    assert "sha256_hash" not in own_response.model_dump()
    with pytest.raises(AppError) as raised:
        get_asset_integrity_status(asset_id, api_context["db"], api_context["other"])
    assert raised.value.status_code == 404


def test_integrity_route_requires_existing_device_auth_dependency():
    route = next(route for route in assets_router.routes if route.path == "/{asset_id}/integrity")
    assert any(
        dependency.call is get_current_authenticated_device
        for dependency in route.dependant.dependencies
    )
