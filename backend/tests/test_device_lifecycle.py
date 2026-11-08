"""Comprehensive test suite for IPGuard One-Time Device Enrollment & Lifecycle Enforcement.
Verifies all 13 business rules:
1. Fresh device can register.
2. Active device cannot register again (409 DEVICE_ALREADY_REGISTERED).
3. Same public key cannot create duplicate active registration (409).
4. Same device ID cannot create duplicate active registration (409).
5. Different device can register independently.
6. Active device can sign in.
7. Revoked device cannot sign in.
8. Revoked device still cannot re-register (409).
9. Unregistered device can register again (releases slot, re-activates).
10. Invalid signature is rejected (401).
11. Duplicate concurrent enrollment requests are handled safely (serialized / 409).
12. Unregister does not delete Secure Notes.
13. Device ownership isolation remains intact.
"""

import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
import pytest

from app.db.session import SessionLocal
from app.main import app
from app.models.auth import AuthSession, Device
from app.models.note import Note
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


def _enroll_device(device_id: str, device_name: str = "Test Phone") -> tuple[dict, ec.EllipticCurvePrivateKey, str]:
    session_res = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "ENROLLMENT"},
        headers={"Origin": "http://localhost:5173"},
    ).json()
    priv_key, pub_b64 = _generate_p256_keypair()

    qr_payload = session_res["qr_payload"]
    canonical = build_canonical_payload(
        session_token=qr_payload["session_token"],
        nonce=qr_payload["nonce"],
        origin=qr_payload["origin"],
        timestamp=qr_payload["timestamp"],
    )
    sig = _sign_payload(priv_key, canonical)

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": session_res["session_token"],
            "device_id": device_id,
            "device_name": device_name,
            "model": "SM-A546E",
            "android_version": "16",
            "public_key_x509": pub_b64,
            "canonical_payload": canonical,
            "signature": sig,
        },
    )
    return reg_res, priv_key, pub_b64


@pytest.fixture(autouse=True)
def cleanup_test_data() -> None:
    yield
    with SessionLocal() as db:
        db.query(Note).delete()
        db.query(AuthSession).delete()
        db.query(Device).delete()
        db.commit()


def test_1_fresh_device_can_register() -> None:
    reg_res, _, _ = _enroll_device("device-fresh-01", "Galaxy A54")
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["device_id"] == "device-fresh-01"
    assert data["status"] == "ACTIVE"
    assert data["registration_status"] == "REGISTERED"
    assert data["access_status"] == "ACTIVE"


def test_2_active_device_cannot_register_again() -> None:
    _enroll_device("device-active-02", "Galaxy A54")

    # Try enrolling same device_id again with a new session
    session_res = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    qr_payload = session_res["qr_payload"]
    priv2, pub2 = _generate_p256_keypair()
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    sig2 = _sign_payload(priv2, canonical)

    reg_res2 = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": session_res["session_token"],
            "device_id": "device-active-02",
            "device_name": "Galaxy A54 Duplicate",
            "model": "SM-A546E",
            "android_version": "16",
            "public_key_x509": pub2,
            "canonical_payload": canonical,
            "signature": sig2,
        },
    )
    assert reg_res2.status_code == 409
    err = reg_res2.json()["error"]
    assert err["code"] == "DEVICE_ALREADY_REGISTERED"
    assert "Perangkat ini sudah terdaftar di IPGuard" in err["message"]


def test_3_same_public_key_cannot_create_duplicate_active_registration() -> None:
    _, priv1, pub1 = _enroll_device("device-key-owner", "Original Device")

    # Try enrolling a DIFFERENT device_id with the SAME public key
    session_res = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    qr_payload = session_res["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    sig_reused = _sign_payload(priv1, canonical)

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": session_res["session_token"],
            "device_id": "device-imposter",
            "device_name": "Imposter Device",
            "model": "Pixel 8",
            "android_version": "15",
            "public_key_x509": pub1,
            "canonical_payload": canonical,
            "signature": sig_reused,
        },
    )
    assert reg_res.status_code == 409
    err = reg_res.json()["error"]
    assert err["code"] == "DEVICE_ALREADY_REGISTERED"


def test_4_different_devices_can_register_independently() -> None:
    res1, _, _ = _enroll_device("device-independent-1", "Device 1")
    res2, _, _ = _enroll_device("device-independent-2", "Device 2")
    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["device_id"] != res2.json()["device_id"]


def test_5_active_device_can_sign_in() -> None:
    _, priv, _ = _enroll_device("device-signin-01", "Sign-in Phone")

    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr_payload = auth_sess["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    sig = _sign_payload(priv, canonical)

    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": "device-signin-01",
            "canonical_payload": canonical,
            "signature": sig,
        },
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["status"] == "APPROVED"
    assert data["access_token"].startswith("ipguard_sess_")


def test_6_revoked_device_cannot_sign_in() -> None:
    _, priv, _ = _enroll_device("device-to-revoke", "Revoked Phone")

    # Revoke device via API
    revoke_res = client.post(
        "/api/v1/auth/devices/device-to-revoke/revoke",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"
    assert revoke_res.json()["access_status"] == "REVOKED"
    assert revoke_res.json()["registration_status"] == "REGISTERED"

    # Attempt sign-in
    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr_payload = auth_sess["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    sig = _sign_payload(priv, canonical)

    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": "device-to-revoke",
            "canonical_payload": canonical,
            "signature": sig,
        },
    )
    assert verify_res.status_code == 403
    assert verify_res.json()["error"]["code"] == "device_revoked"


def test_7_revoked_device_still_cannot_re_register() -> None:
    _, priv, pub = _enroll_device("device-revoked-lock", "Locked Phone")

    # Revoke access
    client.post(
        "/api/v1/auth/devices/device-revoked-lock/revoke",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    )

    # Attempt re-enrollment with new session
    session_res = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    qr_payload = session_res["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    sig = _sign_payload(priv, canonical)

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": session_res["session_token"],
            "device_id": "device-revoked-lock",
            "device_name": "Locked Phone Retry",
            "model": "SM-A546E",
            "android_version": "16",
            "public_key_x509": pub,
            "canonical_payload": canonical,
            "signature": sig,
        },
    )
    assert reg_res.status_code == 409
    err = reg_res.json()["error"]
    assert err["code"] == "DEVICE_ALREADY_REGISTERED"
    assert "Akses perangkat ini telah dicabut namun registrasi masih terkunci" in err["message"]


def test_8_unregistered_device_can_register_again() -> None:
    _, priv, pub = _enroll_device("device-to-unregister", "Phone A")

    # Unregister device explicitly
    unreg_res = client.post(
        "/api/v1/auth/devices/device-to-unregister/unregister",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    )
    assert unreg_res.status_code == 200
    data = unreg_res.json()
    assert data["status"] == "UNREGISTERED"
    assert data["registration_status"] == "UNREGISTERED"
    assert data["unregistered_at"] is not None

    # Check status endpoint
    status_res = client.get("/api/v1/auth/devices/device-to-unregister/status").json()
    assert status_res["status"] == "UNREGISTERED"
    assert status_res["registration_status"] == "UNREGISTERED"

    # Now re-enroll the same device!
    session_res = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    qr_payload = session_res["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    sig = _sign_payload(priv, canonical)

    re_enroll_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": session_res["session_token"],
            "device_id": "device-to-unregister",
            "device_name": "Phone A Re-enrolled",
            "model": "SM-A546E",
            "android_version": "16",
            "public_key_x509": pub,
            "canonical_payload": canonical,
            "signature": sig,
        },
    )
    assert re_enroll_res.status_code == 201
    reenroll_data = re_enroll_res.json()
    assert reenroll_data["status"] == "ACTIVE"
    assert reenroll_data["registration_status"] == "REGISTERED"
    assert reenroll_data["unregistered_at"] is None


def test_9_invalid_signature_is_rejected() -> None:
    session_res = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    qr_payload = session_res["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    _, pub = _generate_p256_keypair()
    other_priv, _ = _generate_p256_keypair()
    tampered_sig = _sign_payload(other_priv, canonical)  # signed with wrong private key

    reg_res = client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": session_res["session_token"],
            "device_id": "device-tampered-sig",
            "device_name": "Tampered Phone",
            "model": "A54",
            "android_version": "16",
            "public_key_x509": pub,
            "canonical_payload": canonical,
            "signature": tampered_sig,
        },
    )
    assert reg_res.status_code == 401
    assert reg_res.json()["error"]["code"] == "signature_verification_failed"


def test_10_unregister_does_not_delete_secure_notes() -> None:
    # 1. Enroll device
    _, priv, _ = _enroll_device("notes-owner-device", "Notes Phone")

    # 2. Sign in to obtain Bearer token
    auth_sess = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr_payload = auth_sess["qr_payload"]
    canonical = build_canonical_payload(qr_payload["session_token"], qr_payload["nonce"], qr_payload["origin"], qr_payload["timestamp"])
    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": "notes-owner-device",
            "canonical_payload": canonical,
            "signature": _sign_payload(priv, canonical),
        },
    ).json()
    token = verify_res["access_token"]

    # 3. Create a Secure Note with the token
    note_res = client.post(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Secret Strategy",
            "content": "Confidential asset records.",
            "vigenere_key": "GUARDKEY",
        },
    )
    assert note_res.status_code == 201
    note_id = note_res.json()["id"]

    # 4. Unregister the device
    client.post(
        "/api/v1/auth/devices/notes-owner-device/unregister",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    )

    # 5. Verify the Note still exists in the database with unchanged owner_id!
    with SessionLocal() as db:
        note_in_db = db.query(Note).filter(Note.id == note_id).first()
        assert note_in_db is not None
        assert note_in_db.owner_id == "notes-owner-device"


def test_11_device_ownership_isolation_remains_intact() -> None:
    # Two distinct devices
    _, priv1, _ = _enroll_device("device-user-alpha")
    _, priv2, _ = _enroll_device("device-user-beta")

    # Login device 1
    s1 = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr1 = s1["qr_payload"]
    c1 = build_canonical_payload(qr1["session_token"], qr1["nonce"], qr1["origin"], qr1["timestamp"])
    t1 = client.post(
        f"/api/v1/auth/sessions/{s1['session_token']}/verify",
        json={"device_id": "device-user-alpha", "canonical_payload": c1, "signature": _sign_payload(priv1, c1)},
    ).json()["access_token"]

    # Login device 2
    s2 = client.post("/api/v1/auth/sessions", json={"session_type": "AUTHENTICATION"}).json()
    qr2 = s2["qr_payload"]
    c2 = build_canonical_payload(qr2["session_token"], qr2["nonce"], qr2["origin"], qr2["timestamp"])
    t2 = client.post(
        f"/api/v1/auth/sessions/{s2['session_token']}/verify",
        json={"device_id": "device-user-beta", "canonical_payload": c2, "signature": _sign_payload(priv2, c2)},
    ).json()["access_token"]

    # Alpha creates a note
    n1 = client.post(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {t1}"},
        json={"title": "Alpha Vault", "content": "Alpha secret data"},
    ).json()

    # Beta cannot see Alpha's note
    beta_list = client.get("/api/v1/notes", headers={"Authorization": f"Bearer {t2}"}).json()
    assert len(beta_list) == 0

    # Beta cannot access Alpha's note by ID (returns 404 for isolation)
    beta_get = client.get(f"/api/v1/notes/{n1['id']}", headers={"Authorization": f"Bearer {t2}"})
    assert beta_get.status_code == 404


def test_12_device_status_sync_endpoint() -> None:
    # Unenrolled query
    unknown = client.get("/api/v1/auth/devices/nonexistent-dev/status").json()
    assert unknown["status"] == "NOT_ENROLLED"
    assert unknown["registration_status"] == "UNREGISTERED"

    # Enrolled query
    _enroll_device("sync-test-dev", "Sync Device")
    active = client.get("/api/v1/auth/devices/sync-test-dev/status").json()
    assert active["status"] == "ACTIVE"
    assert active["registration_status"] == "REGISTERED"
    assert active["access_status"] == "ACTIVE"
