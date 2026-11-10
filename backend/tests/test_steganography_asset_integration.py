"""SQLite service integration for derivative persistence, ownership, and audit."""

import base64
from io import BytesIO
import json
from pathlib import Path
import uuid
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from PIL import Image
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
import pytest

from app.core.errors import AppError
from app.db.base import Base
from app.models.asset import Asset
from app.models.audit import AuditEvent
from app.models.auth import Device
from app.services import asset_storage, assets as assets_service, steganography
from app.services.audit_chain import verify_audit_chain
from app.services.png_steganography import _key_id


@pytest.fixture
def context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'stego-service.sqlite'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _sqlite_features(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    storage = tmp_path / "storage"
    storage.mkdir()
    seed = bytes(range(32))
    private = Ed25519PrivateKey.from_private_bytes(seed)
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = _key_id(public)
    settings = SimpleNamespace(
        asset_vault_max_file_size_bytes=50 * 1024 * 1024,
        storage_directory=storage,
        stego_signing_private_key_b64=base64.b64encode(seed).decode("ascii"),
        stego_active_key_id=key_id,
        stego_public_keys_json=json.dumps({key_id: base64.b64encode(public).decode("ascii")}),
        stego_max_image_bytes=50 * 1024 * 1024,
        stego_max_image_pixels=20_000_000,
        stego_max_image_dimension=10_000,
        stego_max_payload_bytes=4 * 1024 * 1024,
    )
    monkeypatch.setattr(assets_service, "get_settings", lambda: settings)
    monkeypatch.setattr(asset_storage, "get_settings", lambda: settings)
    monkeypatch.setattr(steganography, "get_settings", lambda: settings)
    monkeypatch.setattr(assets_service, "derive_asset_key", lambda _device_id: b"K" * 32)

    owner_id = f"stego-owner-{uuid.uuid4().hex[:12]}"
    other_id = f"stego-other-{uuid.uuid4().hex[:12]}"
    with factory.begin() as db:
        for device_id in (owner_id, other_id):
            db.add(
                Device(
                    device_id=device_id,
                    device_name="Steganography test device",
                    model="Test Device",
                    android_version="14",
                    public_key_x509="test-public-key",
                    public_key_fingerprint=f"stego-test:{uuid.uuid4().hex}",
                    status="ACTIVE",
                )
            )
    try:
        yield factory, storage, owner_id, other_id
    finally:
        engine.dispose()


def _png() -> bytes:
    image = Image.new("RGBA", (64, 64), (29, 91, 143, 177))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_embed_verify_extract_preserve_source_and_record_safe_audit(context):
    factory, _storage, owner_id, other_id = context
    original = _png()
    payload = b"payload that must never enter the audit ledger"
    with factory() as db:
        source = assets_service.create_asset(
            db, owner_id, "source.png", "image/png", original
        )
        source_id = source.id
        source_baseline = source.sha256_hash
        derivative, watermark_id = steganography.embed_asset_watermark(
            db,
            source_asset_id=source_id,
            device_id=owner_id,
            payload=payload,
        )
        derivative_id = derivative.id
        derivative_baseline = derivative.sha256_hash

    with factory() as db:
        stored_source = db.get(Asset, source_id)
        stored_derivative = db.get(Asset, derivative_id)
        assert stored_source.sha256_hash == source_baseline
        assert stored_source.source_asset_id is None
        assert stored_derivative.source_asset_id == source_id
        assert stored_derivative.derivative_type == "PNG_LSB"
        assert stored_derivative.watermark_id == watermark_id
        assert stored_derivative.stego_format_version == 1
        assert stored_derivative.sha256_hash == derivative_baseline

        verified_asset, verified = steganography.verify_asset_watermark(
            db,
            asset_id=derivative_id,
            device_id=owner_id,
        )
        assert verified_asset.id == derivative_id
        assert verified.verified is True
        extracted_asset, extracted = steganography.extract_asset_watermark(
            db,
            asset_id=derivative_id,
            device_id=owner_id,
        )
        assert extracted_asset.id == derivative_id
        assert extracted.payload == payload

        with pytest.raises(AppError) as foreign_access:
            steganography.verify_asset_watermark(db, asset_id=derivative_id, device_id=other_id)
        assert foreign_access.value.status_code == 404

        event_rows = list(
            db.scalars(
                select(AuditEvent).where(AuditEvent.chain_id == owner_id).order_by(AuditEvent.sequence)
            )
        )
        event_types = [row.event_type for row in event_rows]
        assert "ASSET_STEGO_EMBEDDED" in event_types
        assert event_types.count("STEGO_WATERMARK_VERIFIED") == 2
        assert "STEGO_PAYLOAD_EXTRACTED" in event_types
        assert all(payload not in row.canonical_payload for row in event_rows)
        assert verify_audit_chain(db, owner_id).valid is True


def test_failed_verification_is_audited_without_payload(context, monkeypatch):
    _factory, _storage, owner_id, _other_id = context
    factory, *_ = context
    original = _png()
    payload = b"not for ledger"
    with factory() as db:
        source = assets_service.create_asset(db, owner_id, "source.png", "image/png", original)
        derivative, _ = steganography.embed_asset_watermark(
            db, source_asset_id=source.id, device_id=owner_id, payload=payload
        )
        derivative_id = derivative.id

    from app.services import png_steganography

    monkeypatch.setattr(
        steganography,
        "verify_png_watermark",
        lambda *args, **kwargs: png_steganography.WatermarkVerification(False, "INVALID_SIGNATURE"),
    )
    with factory() as db:
        _, result = steganography.verify_asset_watermark(
            db, asset_id=derivative_id, device_id=owner_id
        )
        assert result.verified is False
        assert result.payload is None
        rejected = db.scalar(
            select(AuditEvent).where(
                AuditEvent.chain_id == owner_id,
                AuditEvent.event_type == "STEGO_WATERMARK_REJECTED",
            )
        )
        assert rejected is not None
        assert payload not in rejected.canonical_payload


def test_source_delete_is_blocked_until_derivative_is_removed(context):
    factory, _storage, owner_id, _other_id = context
    with factory() as db:
        source = assets_service.create_asset(db, owner_id, "source.png", "image/png", _png())
        source_id = source.id
        derivative, _ = steganography.embed_asset_watermark(
            db, source_asset_id=source_id, device_id=owner_id, payload=b"x"
        )
        derivative_id = derivative.id

    with factory() as db:
        with pytest.raises(AppError) as blocked:
            assets_service.delete_asset(db, source_id, owner_id)
        assert blocked.value.status_code == 409
        assets_service.delete_asset(db, derivative_id, owner_id)
        assert assets_service.delete_asset(db, source_id, owner_id) is True


def test_failed_embed_is_audited_without_payload(context, monkeypatch):
    factory, _storage, owner_id, _other_id = context
    secret_payload = b"never add this payload to audit"
    with factory() as db:
        source = assets_service.create_asset(db, owner_id, "source.png", "image/png", _png())
        source_id = source.id

    from app.services import png_steganography

    def reject_embed(*args, **kwargs):
        raise png_steganography.PngSteganographyError("INVALID_PNG", "bad image")

    monkeypatch.setattr(steganography, "embed_png", reject_embed)
    with factory() as db:
        with pytest.raises(AppError):
            steganography.embed_asset_watermark(
                db,
                source_asset_id=source_id,
                device_id=owner_id,
                payload=secret_payload,
            )
        failure = db.scalar(
            select(AuditEvent).where(
                AuditEvent.chain_id == owner_id,
                AuditEvent.event_type == "ASSET_STEGO_EMBED_FAILED",
            )
        )
        assert failure is not None
        assert secret_payload not in failure.canonical_payload


def test_missing_signing_key_fails_closed_without_derivative(context, monkeypatch):
    factory, _storage, owner_id, _other_id = context
    with factory() as db:
        source = assets_service.create_asset(db, owner_id, "source.png", "image/png", _png())
        source_id = source.id

    monkeypatch.setattr(
        steganography,
        "get_settings",
        lambda: SimpleNamespace(
            stego_signing_private_key_b64=None,
            stego_active_key_id=None,
            stego_public_keys_json=None,
            stego_max_image_bytes=50 * 1024 * 1024,
            stego_max_image_pixels=20_000_000,
            stego_max_image_dimension=10_000,
            stego_max_payload_bytes=4 * 1024 * 1024,
        ),
    )

    with factory() as db:
        with pytest.raises(AppError) as error:
            steganography.embed_asset_watermark(
                db, source_asset_id=source_id, device_id=owner_id, payload=b"x"
            )
        assert error.value.status_code == 503
        assert db.scalar(select(Asset.id).where(Asset.source_asset_id == source_id)) is None
        failure = db.scalar(
            select(AuditEvent).where(
                AuditEvent.chain_id == owner_id,
                AuditEvent.event_type == "ASSET_STEGO_EMBED_FAILED",
            )
        )
        assert failure is not None
