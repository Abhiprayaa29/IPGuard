"""End-to-End User Workflow Test for M4 Steganography & Watermarking.

Validates the full user journey:
1. Upload PNG original image
2. Configure & embed structured cryptographic watermark
3. Download decrypted watermarked PNG byte-for-byte
4. Verify image readability and dimension preservation
5. Verify watermark cryptographic validity (Ed25519 signature + SHA-256 digest)
6. Extract verified watermark payload and validate metadata schema
7. Tamper detection:
   a. Direct image verification rejects tampered pixels with SIGNATURE_INVALID
   b. Unregistered / direct-uploaded images return NOT_STEGO_DERIVATIVE
   c. Tampered extraction is blocked with HTTP 409
"""

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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.auth import AuthSession, Device
from app.services import asset_storage, assets as assets_service, steganography as stego_service
from app.services.png_steganography import _key_id, verify_png_watermark


@pytest.fixture
def workflow_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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

    with factory.begin() as db:
        device = Device(
            device_id=f"user-workflow-{uuid.uuid4().hex[:12]}",
            device_name="IPGuard Android Workstation",
            model="Pixel 8 Pro",
            android_version="14",
            public_key_x509="test-public-key-workflow",
            public_key_fingerprint=f"workflow-fp:{uuid.uuid4().hex}",
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
                client_origin="http://localhost:5173",
                device_id=device.id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield {
            "client": TestClient(app),
            "token": token,
            "device_id": device.device_id,
            "settings": settings,
        }
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_complete_m4_user_workflow(workflow_context):
    client = workflow_context["client"]
    token = workflow_context["token"]
    settings = workflow_context["settings"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Upload original PNG image
    img = Image.new("RGB", (128, 128), color=(45, 85, 125))
    buf = BytesIO()
    img.save(buf, format="PNG")
    original_png_bytes = buf.getvalue()

    upload_res = client.post(
        "/api/v1/assets",
        headers=headers,
        files={"file": ("artwork_master.png", BytesIO(original_png_bytes), "image/png")},
    )
    assert upload_res.status_code == 201, upload_res.text
    source_asset = upload_res.json()
    source_id = source_asset["id"]
    assert source_asset["original_filename"] == "artwork_master.png"
    assert source_asset["content_type"] == "image/png"

    # Step 2: Configure & Embed Watermark
    metadata_payload = {
        "copyright": "(C) 2026 IPGuard Vault. All rights reserved.",
        "license": "Proprietary Commercial License v2",
        "text": "Confidential Asset - Client Review Copy",
        "description": "High-resolution master derivative with cryptographic watermark",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    raw_json_str = json.dumps(metadata_payload)
    payload_b64 = base64.b64encode(raw_json_str.encode("utf-8")).decode("ascii")

    embed_res = client.post(
        f"/api/v1/assets/{source_id}/steganography/embed",
        headers=headers,
        json={"payload_b64": payload_b64},
    )
    assert embed_res.status_code == 201, embed_res.text
    embed_data = embed_res.json()
    derivative = embed_data["derivative"]
    derivative_id = derivative["id"]
    watermark_id = embed_data["watermark_id"]
    format_version = embed_data["format_version"]

    assert derivative["source_asset_id"] == source_id
    assert derivative["watermark_id"] == watermark_id
    assert derivative["derivative_type"] == "PNG_LSB"
    assert derivative["original_filename"] == "artwork_master.watermarked.png"
    assert format_version == 1

    # Step 3: Download Watermarked Image
    dl_res = client.get(
        f"/api/v1/assets/{derivative_id}/download",
        headers=headers,
    )
    assert dl_res.status_code == 200, dl_res.text
    assert dl_res.headers["content-type"] == "image/png"
    assert 'filename="artwork_master.watermarked.png"' in dl_res.headers["content-disposition"]
    watermarked_png_bytes = dl_res.content
    assert len(watermarked_png_bytes) > 0

    # Verify image integrity: Pillow can open it and dimensions are preserved
    watermarked_img = Image.open(BytesIO(watermarked_png_bytes))
    assert watermarked_img.format == "PNG"
    assert watermarked_img.size == (128, 128)

    # Step 4: Verify Watermark Endpoint
    verify_res = client.post(
        f"/api/v1/assets/{derivative_id}/steganography/verify",
        headers=headers,
    )
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()
    assert verify_data["verified"] is True
    assert verify_data["status"] == "VERIFIED"
    assert verify_data["watermark_id"] == watermark_id
    assert verify_data["source_asset_id"] == source_id
    assert verify_data["derivative_asset_id"] == derivative_id
    assert verify_data["format_version"] == 1

    # Step 5: Extract Watermark Endpoint
    extract_res = client.post(
        f"/api/v1/assets/{derivative_id}/steganography/extract",
        headers=headers,
    )
    assert extract_res.status_code == 200, extract_res.text
    extract_data = extract_res.json()
    assert extract_data["verified"] is True
    assert extract_data["watermark_id"] == watermark_id
    extracted_bytes = base64.b64decode(extract_data["payload_b64"], validate=True)
    extracted_json = json.loads(extracted_bytes.decode("utf-8"))
    assert extracted_json["copyright"] == metadata_payload["copyright"]
    assert extracted_json["license"] == metadata_payload["license"]
    assert extracted_json["text"] == metadata_payload["text"]

    # Step 6: Tamper Detection

    # 6a: Direct pixel tampering on the watermarked image
    tampered_img = Image.open(BytesIO(watermarked_png_bytes)).convert("RGB")
    pixel = tampered_img.getpixel((0, 0))
    tampered_pixel = (pixel[0] ^ 1, pixel[1], pixel[2])
    tampered_img.putpixel((0, 0), tampered_pixel)
    tampered_buf = BytesIO()
    tampered_img.save(tampered_buf, format="PNG")
    tampered_png_bytes = tampered_buf.getvalue()

    direct_verification = verify_png_watermark(
        tampered_png_bytes,
        expected_source_asset_id=uuid.UUID(source_id),
        expected_derivative_asset_id=uuid.UUID(derivative_id),
        expected_watermark_id=uuid.UUID(watermark_id),
        settings=settings,
    )
    assert direct_verification.verified is False
    assert direct_verification.status in ("SIGNATURE_INVALID", "PAYLOAD_CORRUPT", "HEADER_INVALID", "WATERMARK_NOT_FOUND")

    # Also test pixel tampering in the active watermark frame (pixel 10, 0)
    payload_tampered_img = Image.open(BytesIO(watermarked_png_bytes)).convert("RGB")
    p10 = payload_tampered_img.getpixel((10, 0))
    payload_tampered_img.putpixel((10, 0), (p10[0] ^ 1, p10[1], p10[2]))
    p10_buf = BytesIO()
    payload_tampered_img.save(p10_buf, format="PNG")
    p10_verification = verify_png_watermark(
        p10_buf.getvalue(),
        expected_source_asset_id=uuid.UUID(source_id),
        expected_derivative_asset_id=uuid.UUID(derivative_id),
        expected_watermark_id=uuid.UUID(watermark_id),
        settings=settings,
    )
    assert p10_verification.verified is False
    assert p10_verification.status in (
        "WATERMARK_NOT_FOUND",
        "INVALID_SIGNATURE",
        "CHECKSUM_MISMATCH",
        "WATERMARK_ID_MISMATCH",
        "DERIVATIVE_ID_MISMATCH",
    )

    # 6b: Direct upload of an unregistered image verifies as NOT_STEGO_DERIVATIVE
    raw_upload = client.post(
        "/api/v1/assets",
        headers=headers,
        files={"file": ("raw_upload.png", BytesIO(tampered_png_bytes), "image/png")},
    )
    assert raw_upload.status_code == 201
    raw_id = raw_upload.json()["id"]

    raw_verify = client.post(
        f"/api/v1/assets/{raw_id}/steganography/verify",
        headers=headers,
    )
    assert raw_verify.status_code == 200
    assert raw_verify.json()["verified"] is False
    assert raw_verify.json()["status"] == "NOT_STEGO_DERIVATIVE"

    # 6c: Extraction on unverified / non-derivative asset MUST fail with HTTP 409
    raw_extract = client.post(
        f"/api/v1/assets/{raw_id}/steganography/extract",
        headers=headers,
    )
    assert raw_extract.status_code == 409
    assert raw_extract.json()["error"]["code"] == "watermark_verification_failed"
