import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _sign(private_key: ec.EllipticCurvePrivateKey, payload: str) -> str:
    sig = private_key.sign(payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode("ascii")


@pytest.fixture(autouse=True)
def cleanup_test_data() -> None:
    yield
    with SessionLocal() as db:
        db.query(AuthSession).delete()
        db.query(Device).delete()
        db.commit()


def test_concurrent_verification_exact_single_winner() -> None:
    """
    Test SEC-01: Two concurrent requests attempting to verify the same authentication challenge.
    With SELECT FOR UPDATE row-level locking:
    - Exactly one request must succeed (HTTP 200, status APPROVED).
    - The other request must be rejected (HTTP 400, session_already_consumed).
    - Database state must remain consistent with exactly one APPROVED session.
    """
    # 1. Enroll device
    enroll_sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv, b64_pub = _generate_p256_keypair()
    device_id = f"concurrent-dev-{uuid.uuid4().hex[:8]}"
    qr_enr = enroll_sess["qr_payload"]
    enr_payload = build_canonical_payload(qr_enr["session_token"], qr_enr["nonce"], qr_enr["origin"], qr_enr["timestamp"])
    client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": enroll_sess["session_token"],
            "device_id": device_id,
            "device_name": "Concurrent Test Device",
            "model": "SM-A546B",
            "android_version": "16",
            "public_key_x509": b64_pub,
            "canonical_payload": enr_payload,
            "signature": _sign(priv, enr_payload),
        },
    )

    # 2. Create AUTHENTICATION session
    auth_sess = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION"},
    ).json()
    token = auth_sess["session_token"]
    qr = auth_sess["qr_payload"]

    canonical_payload = build_canonical_payload(
        token, qr["nonce"], qr["origin"], qr["timestamp"]
    )
    sig_b64 = _sign(priv, canonical_payload)

    verify_body = {
        "device_id": device_id,
        "canonical_payload": canonical_payload,
        "signature": sig_b64,
    }

    # 3. Fire concurrent requests to /verify simultaneously
    def send_verify() -> tuple[int, dict]:
        # Use separate thread client instance to ensure isolated connections
        t_client = TestClient(app)
        res = t_client.post(f"/api/v1/auth/sessions/{token}/verify", json=verify_body)
        return res.status_code, res.json()

    concurrency = 4
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_verify) for _ in range(concurrency)]
        for f in as_completed(futures):
            results.append(f.result())

    # 4. Assert exactly one succeeded (200 APPROVED) and all others failed (400 session_already_consumed)
    successes = [r for r in results if r[0] == 200]
    failures = [r for r in results if r[0] == 400]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(failures) == concurrency - 1, f"Expected {concurrency - 1} failures, got {len(failures)}: {results}"

    success_data = successes[0][1]
    assert success_data["status"] == "APPROVED"
    assert success_data["access_token"] is not None

    for fail in failures:
        assert fail[1]["error"]["code"] == "session_already_consumed"

    # 5. Verify database integrity
    with SessionLocal() as db:
        session_record = db.scalar(
            select(AuthSession).where(AuthSession.session_token == token)
        )
        assert session_record is not None
        assert session_record.status == "APPROVED"
        assert session_record.signature == sig_b64


def test_concurrent_device_registration_single_winner() -> None:
    """
    Test SEC-01 on enrollment: Two concurrent attempts to register devices using the same enrollment session.
    - Exactly one registration succeeds (HTTP 201).
    - The other is rejected (HTTP 400, session_already_consumed).
    """
    enroll_sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    token = enroll_sess["session_token"]
    qr = enroll_sess["qr_payload"]

    payload = build_canonical_payload(token, qr["nonce"], qr["origin"], qr["timestamp"])

    def send_registration(worker_id: int) -> tuple[int, dict]:
        priv, b64_pub = _generate_p256_keypair()
        sig = _sign(priv, payload)
        t_client = TestClient(app)
        res = t_client.post(
            "/api/v1/auth/devices/register",
            json={
                "session_token": token,
                "device_id": f"device-race-{worker_id}-{uuid.uuid4().hex[:6]}",
                "device_name": f"Device {worker_id}",
                "model": "Pixel 8",
                "android_version": "15",
                "public_key_x509": b64_pub,
                "canonical_payload": payload,
                "signature": sig,
            },
        )
        return res.status_code, res.json()

    concurrency = 4
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_registration, i) for i in range(concurrency)]
        for f in as_completed(futures):
            results.append(f.result())

    successes = [r for r in results if r[0] == 201]
    failures = [r for r in results if r[0] == 400]

    assert len(successes) == 1, f"Expected 1 registration winner, got {len(successes)}: {results}"
    assert len(failures) == concurrency - 1
    for fail in failures:
        assert fail[1]["error"]["code"] == "session_already_consumed"
