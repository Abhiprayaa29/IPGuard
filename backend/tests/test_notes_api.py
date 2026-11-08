"""
Comprehensive integration tests for IPGuard Milestone 3 Secure Notes API.
Tests M2 hardware session validation, CRUD workflows, multi-owner isolation, and database ciphertext.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.db.session import SessionLocal
from app.main import app
from app.models.auth import AuthSession, Device
from app.models.note import Note

client = TestClient(app)


def _seed_device_and_session(
    db,
    device_id: str,
    device_name: str = "Samsung Galaxy A54",
    status: str = "APPROVED",
    device_status: str = "ACTIVE",
    is_expired: bool = False,
) -> tuple[Device, AuthSession]:
    """Helper to seed active enrolled device and associated auth session."""
    now = datetime.now(timezone.utc)
    expires_at = (now - timedelta(minutes=5)) if is_expired else (now + timedelta(minutes=30))

    device = Device(
        device_id=device_id,
        device_name=device_name,
        model="SM-A546E",
        android_version="16",
        public_key_x509="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEtestpublickey...",
        public_key_fingerprint=f"fp-{uuid.uuid4().hex[:16]}",
        security_level="TRUSTED_ENVIRONMENT",
        status=device_status,
        enrolled_at=now,
        last_used_at=now,
    )
    db.add(device)
    db.flush()

    session_token = uuid.uuid4().hex + uuid.uuid4().hex  # 64-char hex
    auth_session = AuthSession(
        session_token=session_token,
        challenge_nonce=uuid.uuid4().hex,
        session_type="AUTHENTICATION",
        status=status,
        client_origin="http://localhost:5173",
        device_id=device.id,
        created_at=now,
        expires_at=expires_at,
        signed_at=now if status == "APPROVED" else None,
    )
    db.add(auth_session)
    db.commit()
    db.refresh(device)
    db.refresh(auth_session)

    return device, auth_session


@pytest.fixture(autouse=True)
def cleanup_database():
    """Ensure clean database state before and after each test."""
    with SessionLocal() as db:
        db.query(Note).delete()
        db.query(AuthSession).delete()
        db.query(Device).delete()
        db.commit()
    yield
    with SessionLocal() as db:
        db.query(Note).delete()
        db.query(AuthSession).delete()
        db.query(Device).delete()
        db.commit()


# --- Security & Authentication Tests ---


def test_notes_missing_authorization_header_returns_401():
    """Verify request without Authorization header fails closed with 401."""
    res = client.get("/api/v1/notes")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "unauthorized"


def test_notes_malformed_token_returns_401():
    """Verify non-hex or malformed token string is rejected."""
    res = client.get(
        "/api/v1/notes",
        headers={"Authorization": "Bearer not-a-valid-hex-token"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_token_format"


def test_notes_unapproved_session_returns_401():
    """Verify session in PENDING state cannot access notes."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-pending", status="PENDING")
        token = session.session_token

    res = client.get(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "session_not_approved"


def test_notes_expired_session_returns_401():
    """Verify session past its expires_at is rejected."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-exp", is_expired=True)
        token = session.session_token

    res = client.get(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "session_expired"


def test_notes_revoked_device_returns_403():
    """Verify session from revoked device is rejected with 403 Forbidden."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-rev", device_status="REVOKED")
        token = session.session_token

    res = client.get(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "device_revoked"


# --- CRUD & Multi-Tenant Tests ---


def test_create_and_get_note_success():
    """Verify successful note creation and retrieval with full 64-hex token."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-user-1")
        token = session.session_token

    create_res = client.post(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Master Crypto Plan", "content": "Keep private keys in Secure Element."},
    )
    assert create_res.status_code == 201
    note_data = create_res.json()
    assert note_data["title"] == "Master Crypto Plan"
    assert note_data["content"] == "Keep private keys in Secure Element."
    note_id = note_data["id"]

    # Retrieve note
    get_res = client.get(
        f"/api/v1/notes/{note_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Master Crypto Plan"


def test_access_token_prefix_support():
    """Verify that M2 access_token format (ipguard_sess_<24_hex>) is supported."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-user-prefix")
        access_token = f"ipguard_sess_{session.session_token[:24]}"

    res = client.post(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"title": "Prefix Token Note", "content": "Authenticated via 24-char prefix."},
    )
    assert res.status_code == 201
    assert res.json()["title"] == "Prefix Token Note"


def test_list_notes_owner_isolation():
    """Verify Owner 1 only sees their notes, and Owner 2 only sees theirs."""
    with SessionLocal() as db:
        _, session1 = _seed_device_and_session(db, "device-1")
        _, session2 = _seed_device_and_session(db, "device-2")
        token1 = session1.session_token
        token2 = session2.session_token

    # Owner 1 creates 2 notes
    client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token1}"}, json={"title": "Note 1A", "content": "Content 1A"})
    client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token1}"}, json={"title": "Note 1B", "content": "Content 1B"})

    # Owner 2 creates 1 note
    client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token2}"}, json={"title": "Note 2A", "content": "Content 2A"})

    # Verify Owner 1 list
    res1 = client.get("/api/v1/notes", headers={"Authorization": f"Bearer {token1}"})
    assert res1.status_code == 200
    titles1 = [n["title"] for n in res1.json()]
    assert len(titles1) == 2
    assert "Note 1A" in titles1
    assert "Note 1B" in titles1
    assert "Note 2A" not in titles1

    # Verify Owner 2 list
    res2 = client.get("/api/v1/notes", headers={"Authorization": f"Bearer {token2}"})
    assert res2.status_code == 200
    titles2 = [n["title"] for n in res2.json()]
    assert len(titles2) == 1
    assert titles2 == ["Note 2A"]


def test_get_and_update_other_owner_note_returns_404():
    """Verify fail-closed: attempting to get or update another owner's note returns 404."""
    with SessionLocal() as db:
        _, session1 = _seed_device_and_session(db, "device-1")
        _, session2 = _seed_device_and_session(db, "device-2")
        token1 = session1.session_token
        token2 = session2.session_token

    # Owner 1 creates note
    res = client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token1}"}, json={"title": "Secret 1", "content": "Pass 1"})
    note_id = res.json()["id"]

    # Owner 2 tries GET
    res_get = client.get(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token2}"})
    assert res_get.status_code == 404
    assert res_get.json()["error"]["code"] == "note_not_found"

    # Owner 2 tries PUT
    res_put = client.put(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token2}"}, json={"title": "Hacked"})
    assert res_put.status_code == 404

    # Owner 2 tries DELETE
    res_del = client.delete(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token2}"})
    assert res_del.status_code == 404


def test_update_note_success():
    """Verify update re-encrypts fields properly."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-update")
        token = session.session_token

    created = client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token}"}, json={"title": "Original Title", "content": "Original Content"}).json()
    note_id = created["id"]

    # Update only title
    updated = client.put(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token}"}, json={"title": "New Title"}).json()
    assert updated["title"] == "New Title"
    assert updated["content"] == "Original Content"

    # Update only content
    updated2 = client.put(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token}"}, json={"content": "New Content"}).json()
    assert updated2["title"] == "New Title"
    assert updated2["content"] == "New Content"


def test_delete_note_success():
    """Verify permanent deletion."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-delete")
        token = session.session_token

    created = client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token}"}, json={"title": "To Delete", "content": "Delete me"}).json()
    note_id = created["id"]

    del_res = client.delete(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 204

    # Should now be 404
    get_res = client.get(f"/api/v1/notes/{note_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 404


def test_database_ciphertext_verification():
    """Verify direct SQL inspect: database stores ONLY ciphertext starting with v1$."""
    with SessionLocal() as db:
        _, session = _seed_device_and_session(db, "device-sql-check")
        token = session.session_token

    secret_title = "Secret Vault Passphrase"
    secret_content = "SuperSensitiveData12345"

    res = client.post("/api/v1/notes", headers={"Authorization": f"Bearer {token}"}, json={"title": secret_title, "content": secret_content})
    note_id = res.json()["id"]

    # Query PostgreSQL directly
    with SessionLocal() as db:
        row = db.execute(text("SELECT id, owner_id, title_enc, content_enc FROM notes WHERE id = :id"), {"id": note_id}).fetchone()
        assert row is not None
        _, owner_id, title_enc, content_enc = row

        assert owner_id == "device-sql-check"
        assert title_enc.startswith("v1$")
        assert content_enc.startswith("v1$")
        assert secret_title not in title_enc
        assert secret_content not in content_enc
