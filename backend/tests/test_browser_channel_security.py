import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.auth import AuthSession
from app.services.crypto import build_canonical_payload

client = TestClient(app)


def _generate_p256_keypair():
    import base64
    private_key = ec.generate_private_key(ec.SECP256R1())
    der_pub = private_key.public_key().public_bytes(
        encoding=Encoding.DER,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    b64_pub = base64.b64encode(der_pub).decode("utf-8")
    return private_key, b64_pub


def _sign_payload(private_key, payload: str) -> str:
    import base64
    der_sig = private_key.sign(payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(der_sig).decode("utf-8")


def test_browser_channel_token_generated_and_excluded_from_qr() -> None:
    res = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert res.status_code == 201
    data = res.json()

    # 1. Returned in response body
    channel_token = data.get("browser_channel_token")
    assert channel_token is not None
    assert len(channel_token) == 64  # 32 bytes hex = 64 chars

    # 2. Excluded from QR payload (Anti QR-Jacking / Shoulder-Surfing boundary)
    qr = data.get("qr_payload")
    assert qr is not None
    assert "browser_channel_token" not in qr
    assert "token" not in qr
    assert set(qr.keys()) == {"version", "type", "session_token", "nonce", "origin", "timestamp"}

    # 3. Backend stores SHA-256 hash in database
    token = data["session_token"]
    expected_hash = hashlib.sha256(channel_token.encode("utf-8")).hexdigest()
    with SessionLocal() as db:
        session_row = db.scalar(select(AuthSession).where(AuthSession.session_token == token))
        assert session_row is not None
        assert session_row.browser_channel_token_hash == expected_hash


def test_unauthorized_polling_rejected_missing_header() -> None:
    res = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"})
    token = res.json()["session_token"]

    poll_res = client.get(f"/api/v1/auth/sessions/{token}")
    assert poll_res.status_code == 403
    err = poll_res.json()
    assert err["error"]["code"] == "invalid_or_missing_browser_channel_token"


def test_unauthorized_polling_rejected_invalid_token() -> None:
    res = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"})
    token = res.json()["session_token"]

    poll_res = client.get(
        f"/api/v1/auth/sessions/{token}",
        headers={"X-Browser-Channel-Token": "0" * 64},
    )
    assert poll_res.status_code == 403
    err = poll_res.json()
    assert err["error"]["code"] == "invalid_or_missing_browser_channel_token"


def test_authorized_polling_succeeds() -> None:
    res = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"})
    data = res.json()
    token = data["session_token"]
    channel_token = data["browser_channel_token"]

    poll_res = client.get(
        f"/api/v1/auth/sessions/{token}",
        headers={"X-Browser-Channel-Token": channel_token},
    )
    assert poll_res.status_code == 200
    body = poll_res.json()
    assert body["session_token"] == token
    assert body["status"] == "PENDING"


def test_approved_session_delivers_token_only_to_authorized_browser() -> None:
    # 1. Register device
    private_key, b64_pub = _generate_p256_keypair()
    device_id = f"dev-channel-test-{uuid.uuid4().hex[:8]}"

    enroll_res = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "ENROLLMENT"},
        headers={"Origin": "http://localhost:5173"},
    )
    enroll_token = enroll_res.json()["session_token"]
    enroll_qr = enroll_res.json()["qr_payload"]
    enroll_payload = build_canonical_payload(
        session_token=enroll_qr["session_token"],
        nonce=enroll_qr["nonce"],
        origin=enroll_qr["origin"],
        timestamp=enroll_qr["timestamp"],
    )
    enroll_sig = _sign_payload(private_key, enroll_payload)

    client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": enroll_token,
            "device_id": device_id,
            "device_name": "Channel Test Device",
            "model": "Model-Sec",
            "android_version": "15",
            "public_key_x509": b64_pub,
            "security_level": "TRUSTED_ENVIRONMENT",
            "canonical_payload": enroll_payload,
            "signature": enroll_sig,
        },
    )

    # 2. Initiate authentication session
    auth_res = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION"},
        headers={"Origin": "http://localhost:5173"},
    )
    auth_data = auth_res.json()
    auth_token = auth_data["session_token"]
    legit_channel_token = auth_data["browser_channel_token"]
    auth_qr = auth_data["qr_payload"]

    # 3. Mobile authenticator scans and verifies
    client.post(f"/api/v1/auth/sessions/{auth_token}/scan", json={"device_id": device_id})
    auth_payload = build_canonical_payload(
        session_token=auth_qr["session_token"],
        nonce=auth_qr["nonce"],
        origin=auth_qr["origin"],
        timestamp=auth_qr["timestamp"],
    )
    auth_sig = _sign_payload(private_key, auth_payload)
    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_token}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": auth_payload,
            "signature": auth_sig,
        },
    )
    assert verify_res.status_code == 200

    # 4. Attacker attempts to poll without token or with forged token
    unauth_poll = client.get(f"/api/v1/auth/sessions/{auth_token}")
    assert unauth_poll.status_code == 403

    attacker_poll = client.get(
        f"/api/v1/auth/sessions/{auth_token}",
        headers={"X-Browser-Channel-Token": "bad_attacker_token_hex_string_12345678"},
    )
    assert attacker_poll.status_code == 403

    # 5. Legitimate browser polls with legitimate channel token
    legit_poll = client.get(
        f"/api/v1/auth/sessions/{auth_token}",
        headers={"X-Browser-Channel-Token": legit_channel_token},
    )
    assert legit_poll.status_code == 200
    poll_body = legit_poll.json()
    assert poll_body["status"] == "APPROVED"
    assert poll_body["device"]["device_id"] == device_id
    assert poll_body["access_token"] is not None
    assert poll_body["access_token"].startswith("ipguard_sess_")


def test_expired_session_requires_valid_channel_token_to_poll() -> None:
    res = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"})
    data = res.json()
    token = data["session_token"]
    channel_token = data["browser_channel_token"]

    with SessionLocal() as db:
        record = db.scalar(select(AuthSession).where(AuthSession.session_token == token))
        assert record is not None
        record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        db.commit()

    # Unauthorized poller cannot trigger or observe expiration
    unauth_poll = client.get(f"/api/v1/auth/sessions/{token}")
    assert unauth_poll.status_code == 403

    # Authorized poller gets EXPIRED
    auth_poll = client.get(
        f"/api/v1/auth/sessions/{token}",
        headers={"X-Browser-Channel-Token": channel_token},
    )
    assert auth_poll.status_code == 200
    assert auth_poll.json()["status"] == "EXPIRED"
