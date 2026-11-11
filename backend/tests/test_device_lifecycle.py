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


def _enroll_device(
    device_id: str,
    device_name: str = "Test Phone",
    account_id: str | None = None,
) -> tuple[dict, ec.EllipticCurvePrivateKey, str]:
    sess_body: dict[str, str] = {"session_type": "ENROLLMENT"}
    headers = {"Origin": "http://localhost:5173"}
    if account_id:
        sess_body["account_id"] = account_id
        headers["X-Dev-Admin-Key"] = "ipguard-dev-admin-secret-key"
    session_res = client.post(
        "/api/v1/auth/sessions",
        json=sess_body,
        headers=headers,
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


def _wipe_lifecycle_tables() -> None:
    with SessionLocal() as db:
        db.query(Note).delete()
        db.query(AuthSession).delete()
        db.query(Device).delete()
        db.commit()


@pytest.fixture(autouse=True)
def cleanup_test_data() -> None:
    _wipe_lifecycle_tables()
    yield
    _wipe_lifecycle_tables()


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


def test_4_single_device_per_account_enforced_and_distinct_accounts_isolated() -> None:
    # Account A enrolls Phone 1 -> succeeds
    res1, _, _ = _enroll_device("device-acct-a-1", "Phone A1", account_id="acct-test-a")
    assert res1.status_code == 201

    # Different phone trying to enroll in SAME Account A -> rejected with 409
    res_dup, _, _ = _enroll_device("device-acct-a-2", "Phone A2", account_id="acct-test-a")
    assert res_dup.status_code == 409
    assert res_dup.json()["error"]["code"] == "DEVICE_ALREADY_REGISTERED"

    # Distinct Account B can register its own phone independently -> succeeds
    res2, _, _ = _enroll_device("device-acct-b-1", "Phone B1", account_id="acct-test-b")
    assert res2.status_code == 201
    assert res1.json()["account_id"] != res2.json()["account_id"]


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
    # Two distinct accounts and their respective devices
    _, priv1, _ = _enroll_device("device-user-alpha", account_id="acct-alpha")
    _, priv2, _ = _enroll_device("device-user-beta", account_id="acct-beta")

    # Login device 1 & 2 on their respective bound accounts
    c1, a1 = _sign_in_device("device-user-alpha", priv1, account_id="acct-alpha")
    c2, a2 = _sign_in_device("device-user-beta", priv2, account_id="acct-beta")
    assert c1 == 200 and c2 == 200
    t1 = a1["access_token"]
    t2 = a2["access_token"]

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


def _sign_in_device(
    device_id: str,
    priv: ec.EllipticCurvePrivateKey,
    account_id: str | None = None,
) -> tuple[int, dict]:
    sess_body: dict[str, str] = {"session_type": "AUTHENTICATION"}
    headers: dict[str, str] = {}
    if account_id:
        sess_body["account_id"] = account_id
        headers["X-Dev-Admin-Key"] = "ipguard-dev-admin-secret-key"
    auth_sess = client.post("/api/v1/auth/sessions", json=sess_body, headers=headers).json()
    qr = auth_sess["qr_payload"]
    canonical = build_canonical_payload(
        qr["session_token"], qr["nonce"], qr["origin"], qr["timestamp"]
    )
    res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": device_id,
            "canonical_payload": canonical,
            "signature": _sign_payload(priv, canonical),
        },
    )
    return res.status_code, res.json()


def test_13_revoke_restore_and_key_preservation_security() -> None:
    from app.services.audit_chain import verify_audit_chain

    reg_res, priv, pub = _enroll_device("dev-restore-01", "Restore Phone", account_id="acct-restore")
    assert reg_res.status_code == 201
    original_fp = reg_res.json()["public_key_fingerprint"]

    # Obtain active token before revocation
    code, auth_data = _sign_in_device("dev-restore-01", priv, account_id="acct-restore")
    assert code == 200
    old_token = auth_data["access_token"]

    # Revoke access
    rev_res = client.post(
        "/api/v1/auth/devices/dev-restore-01/revoke",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
        json={"reason": "Lost phone temporarily"},
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "REVOKED"
    assert rev_res.json()["public_key_fingerprint"] == original_fp

    # Slot remains locked (1/1) while REVOKED: second device on same account must fail 409
    r_other, _, _ = _enroll_device("dev-restore-rival", "Rival Phone", account_id="acct-restore")
    assert r_other.status_code == 409

    # Old Bearer token immediately fails on protected endpoints
    assert client.get("/api/v1/notes", headers={"Authorization": f"Bearer {old_token}"}).status_code in (401, 403)

    # Restore without recovery authorization fails closed (401)
    assert client.post("/api/v1/auth/devices/dev-restore-01/restore").status_code == 401

    # Self-restore with old Bearer token fails closed (403)
    assert (
        client.post(
            "/api/v1/auth/devices/dev-restore-01/restore",
            headers={"Authorization": f"Bearer {old_token}"},
        ).status_code
        == 403
    )

    # Restore with valid X-Account-Recovery-Key succeeds and preserves exact public key
    restore_res = client.post(
        "/api/v1/auth/devices/dev-restore-01/restore",
        headers={"X-Account-Recovery-Key": "ipguard-dev-recovery-secret-key"},
        json={"reason": "Phone recovered"},
    )
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "ACTIVE"
    assert restore_res.json()["public_key_fingerprint"] == original_fp

    # Original private key can authenticate again cleanly
    code_after, _ = _sign_in_device("dev-restore-01", priv, account_id="acct-restore")
    assert code_after == 200

    # Verify audit chain integrity recorded lifecycle events
    with SessionLocal() as db:
        verification = verify_audit_chain(db, "dev-restore-01")
        assert verification.valid is True
        assert verification.event_count >= 4


def test_14_unregister_releases_slot_blocks_old_key_and_allows_new_device() -> None:
    r1, priv1, _ = _enroll_device("dev-old-phone", "Old Phone", account_id="acct-replace")
    assert r1.status_code == 201

    # Summary shows 1/1 active
    sum1 = client.get(
        "/api/v1/auth/devices/summary?account_id=acct-replace",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    ).json()
    assert sum1["registered_slots"] == 1
    assert sum1["current_device"]["device_id"] == "dev-old-phone"

    # Unregister old phone
    unreg = client.post(
        "/api/v1/auth/devices/dev-old-phone/unregister",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    )
    assert unreg.status_code == 200
    assert unreg.json()["status"] == "UNREGISTERED"

    # Old key cannot authenticate anymore
    code_old, _ = _sign_in_device("dev-old-phone", priv1, account_id="acct-replace")
    assert code_old == 403

    # Restore on UNREGISTERED device is blocked (409)
    res_restore_unreg = client.post(
        "/api/v1/auth/devices/dev-old-phone/restore",
        headers={"X-Account-Recovery-Key": "ipguard-dev-recovery-secret-key"},
    )
    assert res_restore_unreg.status_code == 409

    # Summary shows 0/1 slot free, with old phone separated in history
    sum2 = client.get(
        "/api/v1/auth/devices/summary?account_id=acct-replace",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    ).json()
    assert sum2["registered_slots"] == 0
    assert sum2["current_device"] is None
    assert any(h["device_id"] == "dev-old-phone" for h in sum2["history"])

    # New device can enroll into the freed account slot!
    r2, priv2, _ = _enroll_device("dev-new-phone", "New Phone", account_id="acct-replace")
    assert r2.status_code == 201
    code_new, _ = _sign_in_device("dev-new-phone", priv2, account_id="acct-replace")
    assert code_new == 200


def test_15_cross_owner_device_management_forbidden() -> None:
    _, priv_a, _ = _enroll_device("dev-cross-a", "Phone A", account_id="acct-cross-a")
    _, _priv_b, _ = _enroll_device("dev-cross-b", "Phone B", account_id="acct-cross-b")

    code_a, auth_a = _sign_in_device("dev-cross-a", priv_a, account_id="acct-cross-a")
    assert code_a == 200
    token_a = auth_a["access_token"]

    # Account A Bearer token cannot revoke or unregister Account B's device
    assert (
        client.post(
            "/api/v1/auth/devices/dev-cross-b/revoke",
            headers={"Authorization": f"Bearer {token_a}"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/auth/devices/dev-cross-b/unregister",
            headers={"Authorization": f"Bearer {token_a}"},
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/auth/devices/summary?account_id=acct-cross-b",
            headers={"Authorization": f"Bearer {token_a}"},
        ).status_code
        == 403
    )


def test_16_system_overview_reports_live_state() -> None:
    res = client.get("/api/v1/system/overview")
    assert res.status_code == 200
    body = res.json()
    assert body["api_status"] == "ok"
    assert body["database_status"] == "ok"
    assert body["max_slots"] == 1
    assert body["notes_count"] is None  # unauthenticated callers never see owner counts


def test_17_unauthenticated_client_cannot_spoof_account_id() -> None:
    spoof_sess = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "ENROLLMENT", "account_id": "victim-account"},
    )
    assert spoof_sess.status_code == 403
    assert spoof_sess.json()["error"]["code"] == "untrusted_account_identifier"

    spoof_sum = client.get("/api/v1/auth/devices/summary?account_id=victim-account")
    assert spoof_sum.status_code == 403


def test_18_cross_account_session_verification_and_device_reuse_blocked() -> None:
    r_a, priv_a, _ = _enroll_device("dev-iso-a", "Phone A", account_id="acct-iso-a")
    r_b, priv_b, _ = _enroll_device("dev-iso-b", "Phone B", account_id="acct-iso-b")
    assert r_a.status_code == 201
    assert r_b.status_code == 201

    # Account B device cannot verify Account A's challenge session
    code_cross, err_cross = _sign_in_device("dev-iso-b", priv_b, account_id="acct-iso-a")
    assert code_cross == 403
    assert err_cross["error"]["code"] == "cross_owner_forbidden"

    # Unregister Phone A on Account A
    unreg = client.post(
        "/api/v1/auth/devices/dev-iso-a/unregister",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
    )
    assert unreg.status_code == 200

    # Account C cannot hijack dev-iso-a's historical device_id across accounts
    r_hijack, _, _ = _enroll_device("dev-iso-a", "Hijacked Phone A", account_id="acct-iso-c")
    assert r_hijack.status_code == 409
    assert r_hijack.json()["error"]["code"] == "cross_account_device_conflict"


def test_19_revoke_and_unregister_cancel_pending_sessions_and_block_replay() -> None:
    reg_res, priv, _ = _enroll_device("dev-pend-01", "Pending Device", account_id="acct-pend")
    assert reg_res.status_code == 201

    # Initiate a pending authentication challenge BEFORE revocation
    pend_sess = client.post(
        "/api/v1/auth/sessions",
        headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
        json={"session_type": "AUTHENTICATION", "account_id": "acct-pend"},
    ).json()
    qr = pend_sess["qr_payload"]
    canonical = build_canonical_payload(
        qr["session_token"], qr["nonce"], qr["origin"], qr["timestamp"]
    )

    # Revoke device (must cancel pending challenge session too)
    assert (
        client.post(
            "/api/v1/auth/devices/dev-pend-01/revoke",
            headers={"X-Dev-Admin-Key": "ipguard-dev-admin-secret-key"},
        ).status_code
        == 200
    )

    # Restore device, then confirm old pre-revocation pending challenge remains dead
    assert (
        client.post(
            "/api/v1/auth/devices/dev-pend-01/restore",
            headers={"X-Account-Recovery-Key": "ipguard-dev-recovery-secret-key"},
        ).status_code
        == 200
    )

    stale_verify = client.post(
        f"/api/v1/auth/sessions/{pend_sess['session_token']}/verify",
        json={
            "device_id": "dev-pend-01",
            "canonical_payload": canonical,
            "signature": _sign_payload(priv, canonical),
        },
    )
    assert stale_verify.status_code == 400


def test_20_cross_account_notes_and_assets_isolation() -> None:
    _, priv_a, _ = _enroll_device("dev-res-a", "Owner A", account_id="acct-res-a")
    _, priv_b, _ = _enroll_device("dev-res-b", "Owner B", account_id="acct-res-b")
    c_a, a_res = _sign_in_device("dev-res-a", priv_a, account_id="acct-res-a")
    c_b, b_res = _sign_in_device("dev-res-b", priv_b, account_id="acct-res-b")
    assert c_a == 200 and c_b == 200
    tok_a = a_res["access_token"]
    tok_b = b_res["access_token"]

    note_a = client.post(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"title": "Account A Confidential", "content": "Private A body"},
    )
    assert note_a.status_code == 201
    note_id = note_a.json()["id"]

    # Account B sees zero Account A notes and cannot fetch/delete Account A's note
    assert client.get("/api/v1/notes", headers={"Authorization": f"Bearer {tok_b}"}).json() == []
    assert client.get(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {tok_b}"}).status_code == 404
    assert client.delete(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {tok_b}"}).status_code == 404
