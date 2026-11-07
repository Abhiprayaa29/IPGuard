import base64
from datetime import datetime, timedelta, timezone
import uuid
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.auth import AuthSession, Device
from app.services.crypto import build_canonical_payload

client = TestClient(app)


def _generate_p256_keypair() -> tuple[ec.EllipticCurvePrivateKey, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    b64_pub = base64.b64encode(der_bytes).decode("ascii")
    return private_key, b64_pub


def _sign_payload(private_key: ec.EllipticCurvePrivateKey, payload: str) -> str:
    signature_bytes = private_key.sign(
        payload.encode("utf-8"),
        ec.ECDSA(hashes.SHA256()),
    )
    return base64.b64encode(signature_bytes).decode("ascii")


@pytest.fixture(autouse=True)
def cleanup_test_data() -> None:
    yield
    # Clean up any test devices and auth sessions created during testing
    with SessionLocal() as db:
        db.query(AuthSession).delete()
        db.query(Device).delete()
        db.commit()


def test_create_authentication_session() -> None:
    response = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 201
    data = response.json()

    assert len(data["session_token"]) == 64
    assert len(data["challenge_nonce"]) == 64
    assert data["session_type"] == "AUTHENTICATION"
    assert data["status"] == "PENDING"
    assert data["client_origin"] == "http://localhost:5173"
    assert data["poll_interval_ms"] == 1500

    qr = data["qr_payload"]
    assert qr["version"] == "1.0"
    assert qr["type"] == "AUTHENTICATION"
    assert qr["session_token"] == data["session_token"]
    assert qr["nonce"] == data["challenge_nonce"]
    assert qr["origin"] == "http://localhost:5173"
    assert isinstance(qr["timestamp"], int)


def test_create_enrollment_session() -> None:
    response = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "ENROLLMENT", "origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 201
    data = response.json()

    assert data["session_type"] == "ENROLLMENT"
    assert data["client_origin"] == "http://127.0.0.1:5173"
    assert data["qr_payload"]["type"] == "ENROLLMENT"


def test_get_session_status() -> None:
    create_res = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"})
    token = create_res.json()["session_token"]

    status_res = client.get(f"/api/v1/auth/sessions/{token}")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["session_token"] == token
    assert data["status"] == "PENDING"
    assert data["device"] is None
    assert data["access_token"] is None


def test_get_nonexistent_session_404() -> None:
    response = client.get("/api/v1/auth/sessions/nonexistent_token_0000000000000000")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "session_not_found"


def test_scan_session_transitions_status() -> None:
    create_res = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"})
    token = create_res.json()["session_token"]

    scan_res = client.post(
        f"/api/v1/auth/sessions/{token}/scan",
        json={"device_id": "device-scan-123"},
    )
    assert scan_res.status_code == 200
    assert scan_res.json()["status"] == "SCANNED"

    # Verify polling reflects scanned status
    status_res = client.get(f"/api/v1/auth/sessions/{token}")
    assert status_res.json()["status"] == "SCANNED"


def test_device_enrollment_full_lifecycle() -> None:
    # 1. Create enrollment session
    sess_res = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "ENROLLMENT"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert sess_res.status_code == 201
    sess_data = sess_res.json()
    token = sess_data["session_token"]
    qr = sess_data["qr_payload"]

    # 2. Key pair generation
    private_key, b64_pub = _generate_p256_keypair()

    # 3. Canonical payload & signing
    canonical_payload = build_canonical_payload(
        session_token=qr["session_token"],
        nonce=qr["nonce"],
        origin=qr["origin"],
        timestamp=qr["timestamp"],
    )
    sig_b64 = _sign_payload(private_key, canonical_payload)

    # 4. Register device
    device_id = f"dev-{uuid.uuid4().hex[:12]}"
    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": token,
            "device_id": device_id,
            "device_name": "Samsung Galaxy A54 5G",
            "model": "SM-A546B",
            "android_version": "16",
            "public_key_x509": b64_pub,
            "security_level": "TRUSTED_ENVIRONMENT",
            "canonical_payload": canonical_payload,
            "signature": sig_b64,
        },
    )
    assert reg_res.status_code == 201
    dev_data = reg_res.json()
    assert dev_data["device_id"] == device_id
    assert dev_data["status"] == "ACTIVE"
    assert len(dev_data["public_key_fingerprint"]) == 95

    # 5. Verify enrollment session is consumed (APPROVED)
    poll_res = client.get(f"/api/v1/auth/sessions/{token}")
    assert poll_res.json()["status"] == "APPROVED"


def test_device_registration_requires_enrollment_session() -> None:
    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    private_key, b64_pub = _generate_p256_keypair()
    qr = auth_sess["qr_payload"]
    canonical_payload = build_canonical_payload(
        session_token=qr["session_token"],
        nonce=qr["nonce"],
        origin=qr["origin"],
        timestamp=qr["timestamp"],
    )
    sig_b64 = _sign_payload(private_key, canonical_payload)

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": auth_sess["session_token"],
            "device_id": "dev-invalid-session-type",
            "device_name": "Test Phone",
            "model": "Pixel 7",
            "android_version": "14",
            "public_key_x509": b64_pub,
            "canonical_payload": canonical_payload,
            "signature": sig_b64,
        },
    )
    assert reg_res.status_code == 400
    assert reg_res.json()["error"]["code"] == "invalid_session_type"


def test_device_registration_rejects_tampered_canonical_payload() -> None:
    sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    private_key, b64_pub = _generate_p256_keypair()
    qr = sess["qr_payload"]
    canonical_payload = build_canonical_payload(
        session_token=qr["session_token"],
        nonce=qr["nonce"],
        origin=qr["origin"],
        timestamp=qr["timestamp"],
    )
    tampered_payload = canonical_payload + "_tampered"
    sig_b64 = _sign_payload(private_key, tampered_payload)

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": sess["session_token"],
            "device_id": "dev-tampered",
            "device_name": "Test Phone",
            "model": "Pixel 7",
            "android_version": "14",
            "public_key_x509": b64_pub,
            "canonical_payload": tampered_payload,
            "signature": sig_b64,
        },
    )
    assert reg_res.status_code == 400
    assert reg_res.json()["error"]["code"] == "invalid_canonical_payload"


def test_device_registration_rejects_invalid_signature() -> None:
    sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv_alice, _ = _generate_p256_keypair()
    _, b64_pub_bob = _generate_p256_keypair()

    qr = sess["qr_payload"]
    canonical_payload = build_canonical_payload(
        session_token=qr["session_token"],
        nonce=qr["nonce"],
        origin=qr["origin"],
        timestamp=qr["timestamp"],
    )
    # Alice signs, but Bob's public key is sent
    sig_b64 = _sign_payload(priv_alice, canonical_payload)

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": sess["session_token"],
            "device_id": "dev-invalid-sig",
            "device_name": "Test Phone",
            "model": "Pixel 7",
            "android_version": "14",
            "public_key_x509": b64_pub_bob,
            "canonical_payload": canonical_payload,
            "signature": sig_b64,
        },
    )
    assert reg_res.status_code == 401
    assert reg_res.json()["error"]["code"] == "signature_verification_failed"


def test_device_registration_replay_rejected() -> None:
    sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv, b64_pub = _generate_p256_keypair()
    qr = sess["qr_payload"]
    canonical_payload = build_canonical_payload(
        session_token=qr["session_token"],
        nonce=qr["nonce"],
        origin=qr["origin"],
        timestamp=qr["timestamp"],
    )
    sig_b64 = _sign_payload(priv, canonical_payload)

    # First attempt succeeds
    reg1 = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": sess["session_token"],
            "device_id": "dev-replay-1",
            "device_name": "Test Phone",
            "model": "Pixel 7",
            "android_version": "14",
            "public_key_x509": b64_pub,
            "canonical_payload": canonical_payload,
            "signature": sig_b64,
        },
    )
    assert reg1.status_code == 201

    # Second attempt with same enrollment session fails
    priv2, b64_pub2 = _generate_p256_keypair()
    sig_b64_2 = _sign_payload(priv2, canonical_payload)
    reg2 = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": sess["session_token"],
            "device_id": "dev-replay-2",
            "device_name": "Test Phone 2",
            "model": "Pixel 7",
            "android_version": "14",
            "public_key_x509": b64_pub2,
            "canonical_payload": canonical_payload,
            "signature": sig_b64_2,
        },
    )
    assert reg2.status_code == 400
    assert reg2.json()["error"]["code"] == "session_already_consumed"


def test_authentication_session_full_lifecycle() -> None:
    # 1. Enroll a device first
    enroll_sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv, b64_pub = _generate_p256_keypair()
    device_id = "device-auth-test-01"
    qr_enr = enroll_sess["qr_payload"]
    enr_payload = build_canonical_payload(
        session_token=qr_enr["session_token"],
        nonce=qr_enr["nonce"],
        origin=qr_enr["origin"],
        timestamp=qr_enr["timestamp"],
    )
    client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": enroll_sess["session_token"],
            "device_id": device_id,
            "device_name": "Primary Device",
            "model": "A54",
            "android_version": "16",
            "public_key_x509": b64_pub,
            "canonical_payload": enr_payload,
            "signature": _sign_payload(priv, enr_payload),
        },
    )

    # 2. Create AUTHENTICATION session
    auth_sess = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION"},
        headers={"Origin": "http://localhost:5173"},
    ).json()
    auth_token = auth_sess["session_token"]
    qr_auth = auth_sess["qr_payload"]

    # 3. Mobile scans QR
    scan_res = client.post(f"/api/v1/auth/sessions/{auth_token}/scan", json={"device_id": device_id})
    assert scan_res.status_code == 200
    assert scan_res.json()["status"] == "SCANNED"

    # 4. Sign canonical payload
    auth_payload = build_canonical_payload(
        session_token=qr_auth["session_token"],
        nonce=qr_auth["nonce"],
        origin=qr_auth["origin"],
        timestamp=qr_auth["timestamp"],
    )
    auth_sig = _sign_payload(priv, auth_payload)

    # 5. Verify signature
    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_token}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": auth_payload,
            "signature": auth_sig,
        },
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["status"] == "APPROVED"
    assert verify_data["device"]["device_id"] == device_id
    assert verify_data["access_token"] is not None

    # 6. Check poll status
    poll_res = client.get(f"/api/v1/auth/sessions/{auth_token}")
    assert poll_res.json()["status"] == "APPROVED"
    assert poll_res.json()["access_token"] is not None

    # 7. Replay attack rejection: same verify call fails
    replay_res = client.post(
        f"/api/v1/auth/sessions/{auth_token}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": auth_payload,
            "signature": auth_sig,
        },
    )
    assert replay_res.status_code == 400
    assert replay_res.json()["error"]["code"] == "session_already_consumed"


def test_authentication_rejects_unregistered_device() -> None:
    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    priv, _ = _generate_p256_keypair()
    qr = auth_sess["qr_payload"]
    payload = build_canonical_payload(qr["session_token"], qr["nonce"], qr["origin"], qr["timestamp"])

    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": "nonexistent-device",
            "canonical_payload": payload,
            "signature": _sign_payload(priv, payload),
        },
    )
    assert verify_res.status_code == 404
    assert verify_res.json()["error"]["code"] == "device_not_found"


def test_authentication_rejects_tampered_payload_and_signature() -> None:
    # Enroll device
    enroll_sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv, b64_pub = _generate_p256_keypair()
    device_id = "device-tamper-test"
    qr_enr = enroll_sess["qr_payload"]
    enr_payload = build_canonical_payload(qr_enr["session_token"], qr_enr["nonce"], qr_enr["origin"], qr_enr["timestamp"])
    client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": enroll_sess["session_token"],
            "device_id": device_id,
            "device_name": "Test Device",
            "model": "A54",
            "android_version": "16",
            "public_key_x509": b64_pub,
            "canonical_payload": enr_payload,
            "signature": _sign_payload(priv, enr_payload),
        },
    )

    # 1. Tampered payload
    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr_auth = auth_sess["qr_payload"]
    real_payload = build_canonical_payload(qr_auth["session_token"], qr_auth["nonce"], qr_auth["origin"], qr_auth["timestamp"])
    fake_payload = real_payload + "_tampered"

    res_tamper = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": fake_payload,
            "signature": _sign_payload(priv, fake_payload),
        },
    )
    assert res_tamper.status_code == 400
    assert res_tamper.json()["error"]["code"] == "invalid_canonical_payload"

    # 2. Tampered signature on valid payload
    res_badsig = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": real_payload,
            "signature": base64.b64encode(b"invalid_signature_der_bytes").decode("ascii"),
        },
    )
    assert res_badsig.status_code == 401
    assert res_badsig.json()["error"]["code"] == "invalid_signature"


def test_device_revocation_lifecycle() -> None:
    # 1. Enroll device
    enroll_sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv, b64_pub = _generate_p256_keypair()
    device_id = "device-to-revoke"
    qr_enr = enroll_sess["qr_payload"]
    enr_payload = build_canonical_payload(qr_enr["session_token"], qr_enr["nonce"], qr_enr["origin"], qr_enr["timestamp"])
    client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": enroll_sess["session_token"],
            "device_id": device_id,
            "device_name": "Revocable Device",
            "model": "A54",
            "android_version": "16",
            "public_key_x509": b64_pub,
            "canonical_payload": enr_payload,
            "signature": _sign_payload(priv, enr_payload),
        },
    )

    # 2. List devices
    list_res = client.get("/api/v1/auth/devices")
    assert list_res.status_code == 200
    assert any(d["device_id"] == device_id for d in list_res.json())

    # 3. Revoke device
    revoke_res = client.post(f"/api/v1/auth/devices/{device_id}/revoke")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"
    assert revoke_res.json()["revoked_at"] is not None

    # Idempotent revocation
    revoke_res2 = client.post(f"/api/v1/auth/devices/{device_id}/revoke")
    assert revoke_res2.status_code == 200
    assert revoke_res2.json()["status"] == "REVOKED"

    # 4. Attempt authentication with revoked device fails with 403
    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr_auth = auth_sess["qr_payload"]
    auth_payload = build_canonical_payload(qr_auth["session_token"], qr_auth["nonce"], qr_auth["origin"], qr_auth["timestamp"])
    auth_sig = _sign_payload(priv, auth_payload)

    auth_res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": auth_payload,
            "signature": auth_sig,
        },
    )
    assert auth_res.status_code == 403
    assert auth_res.json()["error"]["code"] == "device_revoked"


def test_session_expiration_enforcement() -> None:
    sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    token = sess["session_token"]

    # Manually expire the session in DB
    with SessionLocal() as db:
        record = db.scalar(select(AuthSession).where(AuthSession.session_token == token))
        assert record is not None
        record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.commit()

    # Polling should mark status as EXPIRED
    poll_res = client.get(f"/api/v1/auth/sessions/{token}")
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "EXPIRED"

    # Attempting to scan expired session fails
    scan_res = client.post(f"/api/v1/auth/sessions/{token}/scan")
    assert scan_res.status_code == 400
    assert scan_res.json()["error"]["code"] == "session_expired"

    # Attempting to verify expired session fails
    verify_res = client.post(
        f"/api/v1/auth/sessions/{token}/verify",
        json={
            "device_id": "any-device",
            "canonical_payload": "any-payload",
            "signature": "any-sig",
        },
    )
    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "session_expired"
