"""
IPGuard Milestone 3 — Asset Vault Comprehensive Test Suite.
Verifies XChaCha20-Poly1305 AEAD cryptography, HKDF per-device key derivation,
AAD context binding, magic-byte inspection, atomic file storage, and API endpoints.
"""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import io
import os
from pathlib import Path
import secrets
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import SessionLocal, get_db
from app.main import app
from app.models.asset import Asset
from app.models.auth import AuthSession, Device
from app.services.asset_crypto import (
    AssetDecryptionError,
    ENCRYPTION_VERSION_V1,
    build_asset_aad,
    decrypt_asset_bytes,
    derive_asset_key,
    encrypt_asset_bytes,
)
from app.services.asset_storage import (
    StorageIntegrityError,
    StorageNotFoundError,
    delete_stored_file,
    load_ciphertext_file,
    store_ciphertext_file,
)
from app.services.asset_validation import (
    AssetValidationError,
    detect_and_validate_file,
    sanitize_filename,
)
from app.services import assets as assets_service

client = TestClient(app)


# ---------------------------------------------------------------------------
# Cryptography Unit Tests
# ---------------------------------------------------------------------------

def test_xchacha20poly1305_roundtrip():
    """Verify clean encryption and decryption of binary data using XChaCha20-Poly1305."""
    original_data = b"IPGuard Secret Asset Payload: Top Secret Technical Drawings!"
    key = secrets.token_bytes(32)
    aad = b"v1|device-123|asset-456"

    ciphertext, nonce_b64 = encrypt_asset_bytes(original_data, key, aad=aad)

    assert ciphertext != original_data
    # 24 bytes Base64-encoded is 32 characters
    decoded_nonce = base64.b64decode(nonce_b64)
    assert len(decoded_nonce) == 24

    decrypted = decrypt_asset_bytes(ciphertext, nonce_b64, key, aad=aad)
    assert decrypted == original_data


def test_decrypt_with_wrong_key_fails():
    """Verify that decryption fails closed when provided an invalid key."""
    original_data = b"Confidential document"
    key1 = secrets.token_bytes(32)
    key2 = secrets.token_bytes(32)

    ciphertext, nonce_b64 = encrypt_asset_bytes(original_data, key1)

    with pytest.raises(AssetDecryptionError):
        decrypt_asset_bytes(ciphertext, nonce_b64, key2)


def test_decrypt_with_tampered_ciphertext_fails():
    """Verify that any single-bit tampering of ciphertext is caught by Poly1305 tag."""
    original_data = b"Tamper detection verification data"
    key = secrets.token_bytes(32)

    ciphertext, nonce_b64 = encrypt_asset_bytes(original_data, key)

    tampered = bytearray(ciphertext)
    tampered[0] ^= 1  # Flip a bit

    with pytest.raises(AssetDecryptionError):
        decrypt_asset_bytes(bytes(tampered), nonce_b64, key)


def test_decrypt_with_tampered_aad_fails():
    """Verify that AAD mismatch causes Poly1305 authentication to fail."""
    original_data = b"Bound asset data"
    key = secrets.token_bytes(32)
    valid_aad = b"v1|device-A|asset-1"
    wrong_aad = b"v1|device-B|asset-1"  # Simulated cross-tenant swap

    ciphertext, nonce_b64 = encrypt_asset_bytes(original_data, key, aad=valid_aad)

    with pytest.raises(AssetDecryptionError):
        decrypt_asset_bytes(ciphertext, nonce_b64, key, aad=wrong_aad)


def test_hkdf_per_device_isolation():
    """Verify that different device_ids yield cryptographically independent keys."""
    master_key = secrets.token_bytes(32)
    key_device_a = derive_asset_key("device-alpha-1234", master_key=master_key)
    key_device_b = derive_asset_key("device-bravo-5678", master_key=master_key)

    assert len(key_device_a) == 32
    assert len(key_device_b) == 32
    assert key_device_a != key_device_b

    # Cross-decryption must fail
    data = b"Tenant A Secret"
    ciphertext, nonce_b64 = encrypt_asset_bytes(data, key_device_a)
    with pytest.raises(AssetDecryptionError):
        decrypt_asset_bytes(ciphertext, nonce_b64, key_device_b)


# ---------------------------------------------------------------------------
# File Validation & Magic Byte Tests
# ---------------------------------------------------------------------------

def test_sanitize_filename():
    """Verify directory traversal and dangerous characters are rejected."""
    assert sanitize_filename("safe_document.pdf") == "safe_document.pdf"
    assert sanitize_filename("  spaced file.png  ") == "spaced file.png"

    with pytest.raises(AssetValidationError):
        sanitize_filename("../../etc/passwd")

    with pytest.raises(AssetValidationError):
        sanitize_filename("folder\\malicious.exe")

    with pytest.raises(AssetValidationError):
        sanitize_filename("null\x00byte.png")

    with pytest.raises(AssetValidationError):
        sanitize_filename("")


def test_magic_byte_detection():
    """Verify MIME detection based on file signatures."""
    png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    assert detect_and_validate_file(png_data, "photo.png") == "image/png"

    pdf_data = b"%PDF-1.7\n" + b"sample pdf content"
    assert detect_and_validate_file(pdf_data, "manual.pdf") == "application/pdf"

    txt_data = b"Plain text file content without binary bytes."
    assert detect_and_validate_file(txt_data, "notes.txt") == "text/plain"


def test_dangerous_executable_rejection():
    """Verify that Windows PE and Linux ELF executables are strictly blocked."""
    pe_data = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 50
    with pytest.raises(AssetValidationError, match="dangerous executable format"):
        detect_and_validate_file(pe_data, "innocent.png")

    elf_data = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 50
    with pytest.raises(AssetValidationError, match="dangerous executable format"):
        detect_and_validate_file(elf_data, "script.pdf")


# ---------------------------------------------------------------------------
# Storage Layer Unit Tests
# ---------------------------------------------------------------------------

def test_storage_atomic_write_and_load():
    """Verify ciphertext is stored and loaded with SHA-256 verification."""
    data = b"Ciphertext bytes on disk"
    stored = store_ciphertext_file(data)
    storage_key = stored["storage_key"]
    sha256_hash = stored["sha256_hash"]

    # Verify file exists
    loaded = load_ciphertext_file(storage_key, expected_hash=sha256_hash)
    assert loaded == data

    # Verify tampering with expected hash raises error
    with pytest.raises(StorageIntegrityError):
        load_ciphertext_file(storage_key, expected_hash="0" * 64)

    # Cleanup
    assert delete_stored_file(storage_key) is True
    with pytest.raises(StorageNotFoundError):
        load_ciphertext_file(storage_key)


# ---------------------------------------------------------------------------
# API Integration Fixtures & Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_context():
    """Create a temporary registered device and approved session for API testing."""
    db = SessionLocal()
    device_id = f"test-device-{uuid.uuid4().hex[:12]}"
    session_token = secrets.token_hex(32)

    device = Device(
        device_id=device_id,
        device_name="QA Test Pixel 8",
        model="Pixel 8 Pro",
        android_version="14",
        public_key_x509="dummy_public_key_x509",
        public_key_fingerprint=f"fp:{uuid.uuid4().hex}",
        security_level="HARDWARE_KEYSTORE",
        status="ACTIVE",
    )
    db.add(device)
    db.flush()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=2)

    auth_session = AuthSession(
        session_token=session_token,
        challenge_nonce=uuid.uuid4().hex,
        session_type="AUTHENTICATION",
        status="APPROVED",
        client_origin="http://localhost:5173",
        device_id=device.id,
        created_at=now,
        expires_at=expires_at,
        signed_at=now,
    )
    db.add(auth_session)
    db.commit()

    token_header = f"Bearer ipguard_sess_{session_token[:24]}"

    yield {
        "device_id": device_id,
        "token": token_header,
        "db": db,
    }

    # Teardown
    try:
        cleanup_db = SessionLocal()
        assets = cleanup_db.query(Asset).filter(Asset.device_id == device_id).all()
        for a in assets:
            delete_stored_file(a.storage_key)
        cleanup_db.query(Asset).filter(Asset.device_id == device_id).delete(synchronize_session=False)
        cleanup_db.query(AuthSession).filter(AuthSession.device_id == device.id).delete(synchronize_session=False)
        cleanup_db.query(Device).filter(Device.device_id == device_id).delete(synchronize_session=False)
        cleanup_db.commit()
        cleanup_db.close()
    except Exception:
        pass
    finally:
        db.close()


def test_asset_vault_api_lifecycle(auth_context):
    """
    Test complete lifecycle via API:
    Upload -> List -> Detail -> Download -> Rename -> Delete.
    """
    headers = {"Authorization": auth_context["token"]}

    # 1. Upload valid PNG file
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128
    upload_resp = client.post(
        "/api/v1/assets",
        headers=headers,
        files={"file": ("blueprint.png", io.BytesIO(fake_png), "image/png")},
    )
    assert upload_resp.status_code == 201, upload_resp.text
    created = upload_resp.json()
    asset_id = created["id"]
    assert created["original_filename"] == "blueprint.png"
    assert created["size_bytes"] == len(fake_png)
    assert created["encryption_status"] == "ENCRYPTED_XCHACHA20_POLY1305"

    # 2. List assets
    list_resp = client.get("/api/v1/assets", headers=headers)
    assert list_resp.status_code == 200
    assets = list_resp.json()
    assert any(a["id"] == asset_id for a in assets)

    # 3. Get asset detail
    detail_resp = client.get(f"/api/v1/assets/{asset_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == asset_id

    # 4. Download asset and verify decrypted bytes match exactly
    download_resp = client.get(f"/api/v1/assets/{asset_id}/download", headers=headers)
    assert download_resp.status_code == 200
    assert download_resp.content == fake_png
    assert 'attachment; filename="blueprint.png"' in download_resp.headers["Content-Disposition"]

    # 5. Rename asset
    rename_resp = client.patch(
        f"/api/v1/assets/{asset_id}",
        headers=headers,
        json={"filename": "renamed_blueprint.png"},
    )
    assert rename_resp.status_code == 200
    assert rename_resp.json()["original_filename"] == "renamed_blueprint.png"

    # Verify download uses the updated filename
    dl_after_rename = client.get(f"/api/v1/assets/{asset_id}/download", headers=headers)
    assert "renamed_blueprint.png" in dl_after_rename.headers["Content-Disposition"]

    # 6. Delete asset
    del_resp = client.delete(f"/api/v1/assets/{asset_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify asset is gone from DB and list
    detail_after_del = client.get(f"/api/v1/assets/{asset_id}", headers=headers)
    assert detail_after_del.status_code == 404


def test_cross_device_isolation(auth_context):
    """Verify that Device B cannot view, download, or delete Device A's assets."""
    # Device A uploads an asset
    headers_a = {"Authorization": auth_context["token"]}
    fake_pdf = b"%PDF-1.4\n" + b"Secret Defense Blueprint"
    upload_resp = client.post(
        "/api/v1/assets",
        headers=headers_a,
        files={"file": ("confidential.pdf", io.BytesIO(fake_pdf), "application/pdf")},
    )
    assert upload_resp.status_code == 201
    asset_id = upload_resp.json()["id"]

    # Create Device B
    db = SessionLocal()
    device_b_id = f"device-b-{uuid.uuid4().hex[:10]}"
    sess_b_token = secrets.token_hex(32)

    dev_b = Device(
        device_id=device_b_id,
        device_name="Attacker Device B",
        model="Rooted Phone",
        android_version="14",
        public_key_x509="pub_b",
        public_key_fingerprint=f"fp:{uuid.uuid4().hex}",
        security_level="HARDWARE_KEYSTORE",
        status="ACTIVE",
    )
    db.add(dev_b)
    db.flush()

    now = datetime.now(timezone.utc)
    sess_b = AuthSession(
        session_token=sess_b_token,
        challenge_nonce=uuid.uuid4().hex,
        session_type="AUTHENTICATION",
        status="APPROVED",
        client_origin="http://localhost:5173",
        device_id=dev_b.id,
        created_at=now,
        expires_at=now + timedelta(hours=1),
        signed_at=now,
    )
    db.add(sess_b)
    db.commit()

    headers_b = {"Authorization": f"Bearer ipguard_sess_{sess_b_token[:24]}"}

    try:
        # Device B attempts to get detail of Device A's asset -> 404
        get_resp = client.get(f"/api/v1/assets/{asset_id}", headers=headers_b)
        assert get_resp.status_code == 404

        # Device B attempts to download Device A's asset -> 404
        dl_resp = client.get(f"/api/v1/assets/{asset_id}/download", headers=headers_b)
        assert dl_resp.status_code == 404

        # Device B attempts to rename Device A's asset -> 404
        rename_resp = client.patch(
            f"/api/v1/assets/{asset_id}",
            headers=headers_b,
            json={"filename": "hacked.pdf"},
        )
        assert rename_resp.status_code == 404

        # Device B attempts to delete Device A's asset -> 404
        del_resp = client.delete(f"/api/v1/assets/{asset_id}", headers=headers_b)
        assert del_resp.status_code == 404

    finally:
        # Cleanup Device B
        db.query(AuthSession).filter(AuthSession.device_id == dev_b.id).delete()
        db.query(Device).filter(Device.device_id == device_b_id).delete()
        db.commit()
        db.close()


def test_revoked_device_rejected(auth_context):
    """Verify that a revoked device is blocked with HTTP 403 Forbidden."""
    db = auth_context["db"]
    device = db.query(Device).filter(Device.device_id == auth_context["device_id"]).first()
    device.status = "REVOKED"
    db.commit()

    headers = {"Authorization": auth_context["token"]}
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

    resp = client.post(
        "/api/v1/assets",
        headers=headers,
        files={"file": ("blocked.png", io.BytesIO(fake_png), "image/png")},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "device_revoked"
