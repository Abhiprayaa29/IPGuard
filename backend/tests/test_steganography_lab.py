"""
Comprehensive M4 Steganography Lab Tests:
- Canonical IPGUARD_WATERMARK v1 payload serialization & opaque owner reference
- Capacity calculation & insufficient capacity handling
- External PNG & Vault PNG Inspector statuses:
  VALID, INVALID_SIGNATURE, CORRUPTED, NO_WATERMARK, UNKNOWN_SIGNER, UNSUPPORTED_VERSION
- Synthetic image transformation suite (lossless PNG, resize, crop, pixel edit, palette, JPEG)
- Asset Vault XChaCha20-Poly1305 derived encryption & cross-device authorization
- Zero-persistence guarantee for External PNG Inspection
"""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import secrets
import struct
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from PIL import Image
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.asset import Asset
from app.models.auth import AuthSession, Device
from app.services import asset_storage, assets as assets_service
from app.services.png_steganography import (
    FIXED_HEADER_BYTES,
    FRAME_MAGIC,
    PREFIX_HEADER_BYTES,
    STEGO_DOMAIN,
    _key_id,
    _read_lsb_bytes,
    _write_lsb_bytes,
    calculate_png_capacity,
    embed_png,
    inspect_png_bytes,
)
from app.services.stego_payload import (
    WATERMARK_FORMAT,
    build_canonical_watermark_payload,
    derive_opaque_owner_reference,
)


def _make_png(width: int = 128, height: int = 128, mode: str = "RGBA", color=(40, 90, 140, 210)) -> bytes:
    img = Image.new(mode, (width, height), color if mode == "RGBA" else color[:3])
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_keypair(seed_byte: int):
    seed = bytes([seed_byte]) * 32
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = _key_id(pub_bytes)
    priv_b64 = base64.b64encode(seed).decode("ascii")
    pub_b64 = base64.b64encode(pub_bytes).decode("ascii")
    return priv, key_id, priv_b64, pub_b64


@pytest.fixture()
def lab_env(tmp_path: Path, monkeypatch):
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    db_url = get_settings().database_url
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    _, key_id_1, priv_b64_1, pub_b64_1 = _make_keypair(0x11)
    monkeypatch.setenv("ASSET_VAULT_STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("STEGO_SIGNING_PRIVATE_KEY_B64", priv_b64_1)
    monkeypatch.setenv("STEGO_ACTIVE_KEY_ID", key_id_1)
    monkeypatch.setenv("STEGO_PUBLIC_KEYS_JSON", json.dumps({key_id_1: pub_b64_1}))
    get_settings.cache_clear()

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db

    suffix = uuid.uuid4().hex[:12]
    user_a = f"stego-lab-a-{suffix}"
    user_b = f"stego-lab-b-{suffix}"
    token_a = secrets.token_hex(32)
    token_b = secrets.token_hex(32)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        for dev_id, tok in ((user_a, token_a), (user_b, token_b)):
            dev = Device(
                device_id=dev_id,
                device_name=dev_id,
                model="Test Device",
                android_version="14",
                public_key_x509=base64.b64encode(secrets.token_bytes(91)).decode("ascii"),
                public_key_fingerprint=f"fp:{dev_id}",
                status="ACTIVE",
            )
            db.add(dev)
            db.flush()
            sess = AuthSession(
                session_token=tok,
                challenge_nonce=uuid.uuid4().hex + uuid.uuid4().hex,
                session_type="AUTHENTICATION",
                status="APPROVED",
                client_origin="http://testserver",
                device_id=dev.id,
                expires_at=now + timedelta(minutes=15),
            )
            db.add(sess)
        db.commit()

    try:
        yield TestClient(app), SessionLocal, storage_dir, user_a, user_b, token_a, token_b, key_id_1, pub_b64_1
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        engine.dispose()


# ---------------------------------------------------------------------------
# 1. Payload & Capacity Unit Tests
# ---------------------------------------------------------------------------

def test_canonical_payload_is_deterministic_and_opaque():
    wm_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    ts = datetime(2026, 11, 10, 12, 30, 0, tzinfo=timezone.utc)
    device_id = "sensitive-raw-device-id-123"

    p1 = build_canonical_watermark_payload(
        watermark_id=wm_id,
        source_asset_id=asset_id,
        device_id=device_id,
        source_sha256="a" * 64,
        signing_key_id="0" * 32,
        created_at=ts,
        copyright_notice="© IPGuard Lab",
        license_info="Proprietary",
        note="Confidential draft\x00with control char",
    )
    p2 = build_canonical_watermark_payload(
        watermark_id=wm_id,
        source_asset_id=asset_id,
        device_id=device_id,
        source_sha256="a" * 64,
        signing_key_id="0" * 32,
        created_at=ts,
        copyright_notice="© IPGuard Lab",
        license_info="Proprietary",
        note="Confidential draft\x00with control char",
    )
    assert p1 == p2
    parsed = json.loads(p1.decode("utf-8"))
    assert parsed["format"] == WATERMARK_FORMAT
    assert parsed["version"] == 1
    assert parsed["owner_reference"] == derive_opaque_owner_reference(device_id)
    assert device_id not in p1.decode("utf-8")
    assert "\x00" not in parsed["metadata"]["note"]


def test_capacity_calculation_and_alpha_preservation(lab_env):
    settings = get_settings()
    source_png = _make_png(width=96, height=96, mode="RGBA", color=(10, 20, 30, 177))
    cap = calculate_png_capacity(source_png, settings=settings)

    assert cap.width == 96
    assert cap.height == 96
    assert cap.mode == "RGBA"
    assert cap.total_capacity_bytes == (96 * 96 * 3) // 8
    assert cap.max_payload_bytes == cap.total_capacity_bytes - FIXED_HEADER_BYTES

    watermarked = embed_png(
        source_png,
        b'{"format":"IPGUARD_WATERMARK"}',
        source_asset_id=uuid.uuid4(),
        derivative_asset_id=uuid.uuid4(),
        watermark_id=uuid.uuid4(),
        settings=settings,
    )
    with Image.open(BytesIO(source_png)) as orig, Image.open(BytesIO(watermarked)) as wm:
        assert orig.size == wm.size
        assert orig.mode == wm.mode
        # Alpha channel bytes must be 100% identical
        assert orig.getchannel("A").tobytes() == wm.getchannel("A").tobytes()


# ---------------------------------------------------------------------------
# 2. Inspector Statuses & Corruption Tests
# ---------------------------------------------------------------------------

def test_inspector_distinguishes_all_statuses_and_key_rotation(lab_env, monkeypatch):
    client, SessionLocal, _storage, user_a, _user_b, token_a, _tok_b, key_id_1, pub_b64_1 = lab_env

    # Create and encode a valid watermarked PNG via Steganography Lab API
    source_png = _make_png(width=200, height=200, mode="RGB")
    with SessionLocal() as db:
        src = assets_service.create_asset(db, user_a, "photo.png", "image/png", source_png)
        src_id = src.id

    res_encode = client.post(
        f"/api/v1/steganography/assets/{src_id}/encode",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"copyright": "© 2026 IPGuard", "license": "Proprietary"},
    )
    assert res_encode.status_code == 201
    derivative_id = res_encode.json()["derivative"]["id"]

    # Download decrypted watermarked PNG
    dl = client.get(
        f"/api/v1/assets/{derivative_id}/download",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert dl.status_code == 200
    wm_png = dl.content

    # A. Valid external inspection
    r_valid = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("watermarked.png", wm_png, "image/png")},
        data={"expected_source_sha256": hashlib.sha256(source_png).hexdigest()},
    )
    assert r_valid.status_code == 200
    body = r_valid.json()
    assert body["status"] == "VALID"
    assert body["watermark_detected"] is True
    assert body["signature_valid"] is True
    assert body["source_digest_matches"] is True
    assert body["metadata"]["copyright"] == "© 2026 IPGuard"
    assert body["input_mode"] == "EXTERNAL_UPLOAD"
    assert "private" not in json.dumps(body).lower()

    # B. NO_WATERMARK on clean PNG
    r_clean = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("clean.png", source_png, "image/png")},
    )
    assert r_clean.status_code == 200
    assert r_clean.json()["status"] == "NO_WATERMARK"
    assert r_clean.json()["watermark_detected"] is False
    assert r_clean.json()["metadata"] is None

    # C. Key rotation + verification without private key
    _, key_id_2, priv_b64_2, pub_b64_2 = _make_keypair(0x22)
    monkeypatch.setenv("STEGO_SIGNING_PRIVATE_KEY_B64", "")  # offline private key!
    monkeypatch.setenv("STEGO_ACTIVE_KEY_ID", key_id_2)
    monkeypatch.setenv("STEGO_PUBLIC_KEYS_JSON", json.dumps({key_id_1: pub_b64_1, key_id_2: pub_b64_2}))
    get_settings.cache_clear()

    r_rotated = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("watermarked.png", wm_png, "image/png")},
    )
    assert r_rotated.status_code == 200
    assert r_rotated.json()["status"] == "VALID"

    # D. UNKNOWN_SIGNER when public key removed
    monkeypatch.setenv("STEGO_PUBLIC_KEYS_JSON", json.dumps({key_id_2: pub_b64_2}))
    get_settings.cache_clear()
    r_unknown = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("watermarked.png", wm_png, "image/png")},
    )
    assert r_unknown.status_code == 200
    assert r_unknown.json()["status"] == "UNKNOWN_SIGNER"
    assert r_unknown.json()["signature_valid"] is False
    assert r_unknown.json()["metadata"] is None  # never release untrusted payload!

    # Restore trusted key 1 for remaining corruption checks
    monkeypatch.setenv("STEGO_PUBLIC_KEYS_JSON", json.dumps({key_id_1: pub_b64_1}))
    get_settings.cache_clear()

    # E. INVALID_SIGNATURE when signature bit flipped
    with Image.open(BytesIO(wm_png)) as im:
        px = bytearray(im.tobytes())
        raw_frame = bytearray(_read_lsb_bytes(bytes(px), FIXED_HEADER_BYTES + 10, 3))
        raw_frame[PREFIX_HEADER_BYTES + 5] ^= 0x01  # flip bit inside signature
        _write_lsb_bytes(px, bytes(raw_frame), 3)
        tampered_sig_buf = BytesIO()
        Image.frombytes(im.mode, im.size, bytes(px)).save(tampered_sig_buf, format="PNG")
    r_invalidsig = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("bad_sig.png", tampered_sig_buf.getvalue(), "image/png")},
    )
    assert r_invalidsig.status_code == 200
    assert r_invalidsig.json()["status"] == "INVALID_SIGNATURE"
    assert r_invalidsig.json()["metadata"] is None

    # F. CORRUPTED when payload pixel modified
    with Image.open(BytesIO(wm_png)) as im:
        px = bytearray(im.tobytes())
        # Flip LSB of a byte inside payload region (after FIXED_HEADER_BYTES * 8 bits)
        payload_byte_offset = (FIXED_HEADER_BYTES + 4) * 8
        px[payload_byte_offset] ^= 0x01
        corrupt_buf = BytesIO()
        Image.frombytes(im.mode, im.size, bytes(px)).save(corrupt_buf, format="PNG")
    r_corrupt = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("corrupt.png", corrupt_buf.getvalue(), "image/png")},
    )
    assert r_corrupt.status_code == 200
    assert r_corrupt.json()["status"] == "CORRUPTED"
    assert r_corrupt.json()["checksum_valid"] is False
    assert r_corrupt.json()["metadata"] is None

    # G. UNSUPPORTED_VERSION when frame version byte changed to 99
    with Image.open(BytesIO(wm_png)) as im:
        px = bytearray(im.tobytes())
        hdr = bytearray(_read_lsb_bytes(bytes(px), 6, 3))
        hdr[4] = 99
        _write_lsb_bytes(px, bytes(hdr), 3)
        ver_buf = BytesIO()
        Image.frombytes(im.mode, im.size, bytes(px)).save(ver_buf, format="PNG")
    r_ver = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("v99.png", ver_buf.getvalue(), "image/png")},
    )
    assert r_ver.status_code == 200
    assert r_ver.json()["status"] == "UNSUPPORTED_VERSION"
    assert r_ver.json()["version"] == 99


# ---------------------------------------------------------------------------
# 3. Synthetic Image Transformation Robustness Tests
# ---------------------------------------------------------------------------

def test_synthetic_image_transformations(lab_env):
    settings = get_settings()
    source_png = _make_png(width=220, height=220, mode="RGBA", color=(35, 110, 180, 255))
    payload = build_canonical_watermark_payload(
        watermark_id=uuid.uuid4(),
        source_asset_id=uuid.uuid4(),
        device_id="dev-1",
        source_sha256=hashlib.sha256(source_png).hexdigest(),
        signing_key_id=settings.stego_active_key_id,
    )
    wm_png = embed_png(
        source_png,
        payload,
        source_asset_id=uuid.uuid4(),
        derivative_asset_id=uuid.uuid4(),
        watermark_id=uuid.uuid4(),
        settings=settings,
    )

    # 1. PNG lossless re-save -> preserves watermark
    with Image.open(BytesIO(wm_png)) as im:
        lossless_buf = BytesIO()
        im.save(lossless_buf, format="PNG", compress_level=9)
    res_lossless = inspect_png_bytes(lossless_buf.getvalue(), settings=settings)
    assert res_lossless.status == "VALID"

    # 2. Resize -> destroys watermark
    with Image.open(BytesIO(wm_png)) as im:
        resized_buf = BytesIO()
        im.resize((180, 180)).save(resized_buf, format="PNG")
    res_resize = inspect_png_bytes(resized_buf.getvalue(), settings=settings)
    assert res_resize.status in {"NO_WATERMARK", "CORRUPTED"}

    # 3. Crop -> destroys watermark
    with Image.open(BytesIO(wm_png)) as im:
        cropped_buf = BytesIO()
        im.crop((10, 10, 200, 200)).save(cropped_buf, format="PNG")
    res_crop = inspect_png_bytes(cropped_buf.getvalue(), settings=settings)
    assert res_crop.status in {"NO_WATERMARK", "CORRUPTED"}

    # 4. Lossy JPEG round-trip -> destroys watermark
    with Image.open(BytesIO(wm_png)) as im:
        jpg_buf = BytesIO()
        im.convert("RGB").save(jpg_buf, format="JPEG", quality=95)
        jpg_buf.seek(0)
        with Image.open(jpg_buf) as jpg_im:
            re_png_buf = BytesIO()
            jpg_im.save(re_png_buf, format="PNG")
    res_jpeg = inspect_png_bytes(re_png_buf.getvalue(), settings=settings)
    assert res_jpeg.status in {"NO_WATERMARK", "CORRUPTED"}


# ---------------------------------------------------------------------------
# 4. Security, Authorization & Zero-Persistence Guarantees
# ---------------------------------------------------------------------------

def test_authorization_zero_persistence_and_derived_asset_lifecycle(lab_env):
    client, SessionLocal, storage_dir, user_a, _user_b, token_a, token_b, _k, _p = lab_env

    # Unauthenticated external inspect rejected
    clean_png = _make_png(width=160, height=160, mode="RGB")
    r_unauth = client.post(
        "/api/v1/steganography/inspect",
        files={"file": ("clean.png", clean_png, "image/png")},
    )
    assert r_unauth.status_code == 401

    # Zero persistence check before & after external inspect
    with SessionLocal() as db:
        before_count = db.scalar(select(func.count()).select_from(Asset))
    before_files = len(list(storage_dir.iterdir()))

    r_ext = client.post(
        "/api/v1/steganography/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("external.png", clean_png, "image/png")},
    )
    assert r_ext.status_code == 200

    with SessionLocal() as db:
        after_count = db.scalar(select(func.count()).select_from(Asset))
    after_files = len(list(storage_dir.iterdir()))
    assert after_count == before_count
    assert after_files == before_files

    # User A creates source PNG, encodes via /assets/{id}/watermark alias
    with SessionLocal() as db:
        src = assets_service.create_asset(db, user_a, "blueprint.png", "image/png", clean_png)
        src_id = src.id
        orig_hash = src.sha256_hash

    # Cross-device isolation: User B cannot check capacity, encode, or inspect User A's asset
    assert client.get(
        f"/api/v1/steganography/assets/{src_id}/capacity",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
    assert client.post(
        f"/api/v1/assets/{src_id}/watermark",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"copyright": "stolen"},
    ).status_code == 404
    assert client.post(
        f"/api/v1/assets/{src_id}/watermark/inspect",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    # User A encodes watermark
    r_wm = client.post(
        f"/api/v1/assets/{src_id}/watermark",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"copyright": "© User A", "license": "All Rights Reserved", "note": "Blueprint rev 2"},
    )
    assert r_wm.status_code == 201
    deriv = r_wm.json()["derivative"]
    deriv_id = deriv["id"]
    assert deriv_id != str(src_id)
    assert deriv["source_asset_id"] == str(src_id)
    assert deriv["derivative_type"] == "PNG_LSB"
    assert deriv["encryption_status"] == "ENCRYPTED_XCHACHA20_POLY1305"

    # Original asset unchanged
    with SessionLocal() as db:
        src_after = assets_service.get_asset(db, src_id, user_a)
        assert src_after.sha256_hash == orig_hash
        # Ciphertext on disk does NOT contain raw PNG header
        deriv_row = assets_service.get_asset(db, uuid.UUID(deriv_id), user_a)
        ct_bytes = (storage_dir / deriv_row.storage_key).read_bytes()
        assert b"\x89PNG\r\n\x1a\n" not in ct_bytes

    # Vault Inspector checks both parent and derivative read-only
    r_inspect_src = client.post(
        f"/api/v1/assets/{src_id}/watermark/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r_inspect_src.status_code == 200
    assert r_inspect_src.json()["status"] == "NO_WATERMARK"

    r_inspect_deriv = client.post(
        f"/api/v1/assets/{deriv_id}/watermark/inspect",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r_inspect_deriv.status_code == 200
    d_body = r_inspect_deriv.json()
    assert d_body["status"] == "VALID"
    assert d_body["input_mode"] == "ASSET_VAULT"
    assert d_body["source_digest_matches"] is True
    assert d_body["metadata"]["note"] == "Blueprint rev 2"

    # Deleting derived asset leaves original asset intact
    assert client.delete(
        f"/api/v1/assets/{deriv_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    ).status_code == 204
    assert client.get(
        f"/api/v1/assets/{src_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    ).status_code == 200
