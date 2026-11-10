"""Isolated SQLite HTTP integration tests for signed PNG LSB Asset Vault flows."""

import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import uuid
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.asset import Asset
from app.models.audit import AuditEvent
from app.models.auth import AuthSession, Device
from app.services import asset_storage, assets as assets_service, steganography as stego_service
from app.services.audit_chain import verify_audit_chain
from app.services.png_steganography import _key_id

# pytestmark = pytest.mark.skipif(
#     os.name == "nt",
#     reason="Starlette TestClient cannot start its asyncio socket pair in this Windows sandbox.",
# )


@pytest.fixture
def stego_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pg_url = os.getenv("DATABASE_URL") or "postgresql+psycopg://ipguard:96e53c7bc2cee94c27d88acc99d85af6809765b79ccc1ec126571f6c0af24461@127.0.0.1:5432/ipguard"
    engine = create_engine(pg_url, pool_pre_ping=True)

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    storage = tmp_path / "storage"
    storage.mkdir()

    seed = bytes(range(32))
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = _key_id(public_key)
    settings = SimpleNamespace(
        asset_vault_max_file_size_bytes=50 * 1024 * 1024,
        storage_directory=storage,
        stego_signing_private_key_b64=base64.b64encode(seed).decode("ascii"),
        stego_active_key_id=key_id,
        stego_public_keys_json=json.dumps({key_id: base64.b64encode(public_key).decode("ascii")}),
        stego_max_image_bytes=50 * 1024 * 1024,
        stego_max_image_pixels=20_000_000,
        stego_max_image_dimension=10_000,
        stego_max_payload_bytes=4 * 1024 * 1024,
    )
    monkeypatch.setattr(assets_service, "get_settings", lambda: settings)
    monkeypatch.setattr(asset_storage, "get_settings", lambda: settings)
    monkeypatch.setattr(stego_service, "get_settings", lambda: settings)
    monkeypatch.setattr("app.api.routes.assets.get_settings", lambda: settings)
    monkeypatch.setattr(assets_service, "derive_asset_key", lambda _device_id: b"K" * 32)

    credentials = {}
    device_ids = {}
    with factory.begin() as db:
        for role in ("owner", "other"):
            device = Device(
                device_id=f"stego-{role}-{uuid.uuid4().hex[:12]}",
                device_name=f"Stego {role}",
                model="Test Device",
                android_version="14",
                public_key_x509="test-public-key",
                public_key_fingerprint=f"stego-fp:{uuid.uuid4().hex}",
                status="ACTIVE",
            )
            token = secrets.token_hex(32)
            db.add(device)
            db.flush()
            db.add(
                AuthSession(
                    session_token=token,
                    challenge_nonce=uuid.uuid4().hex + uuid.uuid4().hex,
                    session_type="AUTHENTICATION",
                    status="APPROVED",
                    client_origin="http://testserver",
                    device_id=device.id,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            credentials[role] = token
            device_ids[role] = device.device_id

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield {
            "client": TestClient(app),
            "factory": factory,
            "storage": storage,
            "credentials": credentials,
            "device_ids": device_ids,
        }
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def _valid_png(size=(64, 64)) -> bytes:
    image = Image.new("RGB", size, color=(31, 73, 127))
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_authenticated_embed_verify_extract_and_lineage(stego_api):
    client = stego_api["client"]
    token = stego_api["credentials"]["owner"]
    headers = {"Authorization": f"Bearer {token}"}
    source_png = _valid_png()
    payload = b"private watermark payload"

    upload = client.post(
        "/api/v1/assets",
        headers=headers,
        files={"file": ("source.png", BytesIO(source_png), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    source_id = uuid.UUID(upload.json()["id"])
    original_baseline = upload.json()["sha256_hash"]

    embed = client.post(
        f"/api/v1/assets/{source_id}/steganography/embed",
        headers=headers,
        json={"payload_b64": base64.b64encode(payload).decode("ascii")},
    )
    assert embed.status_code == 201, embed.text
    derivative = embed.json()["derivative"]
    derivative_id = uuid.UUID(derivative["id"])
    watermark_id = uuid.UUID(embed.json()["watermark_id"])
    assert derivative_id != source_id
    assert derivative["source_asset_id"] == str(source_id)
    assert derivative["watermark_id"] == str(watermark_id)
    assert derivative["sha256_hash"] != original_baseline

    verify = client.post(
        f"/api/v1/assets/{derivative_id}/steganography/verify", headers=headers
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["verified"] is True
    assert verify.json()["source_asset_id"] == str(source_id)
    assert verify.json()["derivative_asset_id"] == str(derivative_id)

    extract = client.post(
        f"/api/v1/assets/{derivative_id}/steganography/extract", headers=headers
    )
    assert extract.status_code == 200, extract.text
    assert base64.b64decode(extract.json()["payload_b64"], validate=True) == payload

    foreign = client.post(
        f"/api/v1/assets/{derivative_id}/steganography/verify",
        headers={"Authorization": f"Bearer {stego_api['credentials']['other']}"},
    )
    assert foreign.status_code == 404

    with stego_api["factory"]() as db:
        source = db.get(Asset, source_id)
        stored_derivative = db.get(Asset, derivative_id)
        assert source.sha256_hash == original_baseline
        assert source.source_asset_id is None
        assert stored_derivative.source_asset_id == source_id
        assert stored_derivative.derivative_type == "PNG_LSB"
        assert stored_derivative.integrity_status in ("PENDING", "VERIFIED")
        event_types = list(
            db.scalars(
                select(AuditEvent.event_type)
                .where(AuditEvent.chain_id == stego_api["device_ids"]["owner"])
                .order_by(AuditEvent.sequence)
            )
        )
        assert "ASSET_STEGO_EMBEDDED" in event_types
        assert "STEGO_WATERMARK_VERIFIED" in event_types
        assert "STEGO_PAYLOAD_EXTRACTED" in event_types
        assert verify_audit_chain(db, stego_api["device_ids"]["owner"]).valid is True


def test_source_asset_cannot_be_deleted_while_derivative_exists(stego_api):
    client = stego_api["client"]
    headers = {"Authorization": f"Bearer {stego_api['credentials']['owner']}"}
    upload = client.post(
        "/api/v1/assets",
        headers=headers,
        files={"file": ("source.png", BytesIO(_valid_png()), "image/png")},
    )
    source_id = upload.json()["id"]
    embedded = client.post(
        f"/api/v1/assets/{source_id}/steganography/embed",
        headers=headers,
        json={"payload_b64": base64.b64encode(b"x").decode("ascii")},
    )
    assert embedded.status_code == 201

    response = client.delete(f"/api/v1/assets/{source_id}", headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "asset_has_derivatives"

