"""Transaction and event integration tests for Asset Integrity Audit events."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.models.asset import Asset
from app.models.audit import AuditEvent
from app.models.auth import Device
from app.services import asset_integrity, asset_storage
from app.services.audit_chain import AuditChainError, verify_audit_chain


@pytest.fixture
def integrity_audit_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'integrity-audit.sqlite'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setattr(
        asset_storage,
        "get_settings",
        lambda: type("Settings", (), {"storage_directory": storage})(),
    )
    try:
        yield factory, storage
    finally:
        engine.dispose()


def _add_asset(factory, storage: Path, *, stored: bytes | None, baseline: bytes) -> tuple[uuid.UUID, str]:
    device_id = f"integrity-audit-{uuid.uuid4().hex[:16]}"
    storage_key = uuid.uuid4().hex
    if stored is not None:
        (storage / storage_key).write_bytes(stored)
    asset_id = uuid.uuid4()
    with factory.begin() as db:
        db.add(
            Device(
                device_id=device_id,
                device_name="Integrity audit test device",
                model="Test Device",
                android_version="14",
                public_key_x509="test-public-key",
                public_key_fingerprint=f"integrity-audit-fp:{uuid.uuid4().hex}",
                status="ACTIVE",
            )
        )
        db.add(
            Asset(
                id=asset_id,
                device_id=device_id,
                original_filename="audit-fixture.bin",
                storage_key=storage_key,
                content_type="application/octet-stream",
                size_bytes=len(baseline),
                nonce="dGVzdA==",
                sha256_hash=hashlib.sha256(baseline).hexdigest(),
            )
        )
    return asset_id, device_id


@pytest.mark.parametrize(
    ("status", "stored", "expected_event"),
    [
        ("VERIFIED", b"ciphertext", "INTEGRITY_CHECK_PASSED"),
        ("MISMATCH", b"changed", "ASSET_TAMPERED"),
        ("MISSING", None, "ASSET_MISSING"),
        ("ERROR", b"ciphertext", "INTEGRITY_CHECK_ERROR"),
    ],
)
def test_integrity_status_and_audit_event_commit_together(
    integrity_audit_context, monkeypatch, status, stored, expected_event
):
    factory, storage = integrity_audit_context
    baseline = b"ciphertext"
    asset_id, device_id = _add_asset(
        factory, storage, stored=None if status == "MISSING" else stored, baseline=baseline
    )
    if status == "ERROR":
        monkeypatch.setattr(
            asset_integrity,
            "inspect_ciphertext_file",
            lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("not logged")),
        )

    result = asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    assert result.status == status
    assert result.audit_recorded is True
    with factory() as db:
        asset = db.get(Asset, asset_id)
        event = db.scalar(
            select(AuditEvent).where(
                AuditEvent.chain_id == device_id,
                AuditEvent.event_type == expected_event,
            )
        )
        chain_result = verify_audit_chain(db, device_id)
    assert asset.integrity_status == status
    assert asset.sha256_hash == hashlib.sha256(baseline).hexdigest()
    assert event.event_type == expected_event
    assert event.result == status
    assert chain_result.valid is True

    payload = json.loads(event.canonical_payload.decode("utf-8"))
    assert payload["integrity_status"] == status
    assert "path" not in payload
    assert "ciphertext" not in payload
    assert "not logged" not in event.canonical_payload.decode("utf-8")


def test_final_append_failure_keeps_only_audited_pending_claim(
    integrity_audit_context, monkeypatch
):
    factory, storage = integrity_audit_context
    baseline = b"known ciphertext"
    asset_id, device_id = _add_asset(factory, storage, stored=baseline, baseline=baseline)
    prior_checked_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with factory.begin() as db:
        asset = db.get(Asset, asset_id)
        asset.integrity_status = "MISMATCH"
        asset.last_checked_at = prior_checked_at
        asset.last_observed_sha256 = "a" * 64

    append_calls = 0

    def fail_final_append(*args, **kwargs):
        nonlocal append_calls
        append_calls += 1
        if append_calls == 2:
            raise AuditChainError("append unavailable")
        return original_append(*args, **kwargs)

    original_append = asset_integrity.append_audit_event
    monkeypatch.setattr(asset_integrity, "append_audit_event", fail_final_append)

    with pytest.raises(AuditChainError):
        asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    with factory() as db:
        asset = db.get(Asset, asset_id)
        assert asset.integrity_status == "PENDING"
        assert asset.last_observed_sha256 is None
        assert asset.sha256_hash == hashlib.sha256(baseline).hexdigest()
        events = list(db.scalars(select(AuditEvent).where(AuditEvent.chain_id == device_id)))
        assert len(events) == 1
        assert events[0].event_type == "INTEGRITY_CHECK_STARTED"
        assert events[0].result == "PENDING"


def test_claim_append_failure_preserves_previous_integrity_state(
    integrity_audit_context, monkeypatch
):
    factory, storage = integrity_audit_context
    baseline = b"known ciphertext"
    asset_id, device_id = _add_asset(factory, storage, stored=baseline, baseline=baseline)
    prior_checked_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with factory.begin() as db:
        asset = db.get(Asset, asset_id)
        asset.integrity_status = "VERIFIED"
        asset.last_checked_at = prior_checked_at
        asset.last_observed_sha256 = hashlib.sha256(baseline).hexdigest()

    def fail_append(*args, **kwargs):
        raise AuditChainError("append unavailable")

    monkeypatch.setattr(asset_integrity, "append_audit_event", fail_append)

    with pytest.raises(AuditChainError):
        asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    with factory() as db:
        asset = db.get(Asset, asset_id)
        assert asset.integrity_status == "VERIFIED"
        persisted_checked_at = asset.last_checked_at
        if persisted_checked_at.tzinfo is None:
            persisted_checked_at = persisted_checked_at.replace(tzinfo=timezone.utc)
        assert persisted_checked_at == prior_checked_at
        assert asset.last_observed_sha256 == hashlib.sha256(baseline).hexdigest()
        assert asset.sha256_hash == hashlib.sha256(baseline).hexdigest()
        assert db.scalar(select(AuditEvent).where(AuditEvent.chain_id == device_id)) is None


def test_crashed_pending_check_is_retried_by_next_worker_scan(
    integrity_audit_context, monkeypatch
):
    from app.workers import integrity

    factory, storage = integrity_audit_context
    baseline = b"known ciphertext"
    asset_id, device_id = _add_asset(factory, storage, stored=baseline, baseline=baseline)
    # Model a process crash after the atomic PENDING + STARTED transaction.
    with factory.begin() as db:
        asset = db.get(Asset, asset_id)
        asset.integrity_status = "PENDING"
        asset.last_checked_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        from app.services.audit_chain import append_audit_event

        append_audit_event(
            db,
            chain_id=device_id,
            event_type="INTEGRITY_CHECK_STARTED",
            resource_type="asset",
            resource_id=str(asset_id),
            result="PENDING",
            payload={"integrity_status": "PENDING", "baseline_sha256": hashlib.sha256(baseline).hexdigest()},
        )

    summary = integrity.run_integrity_scan(session_factory=factory)

    assert summary.scanned == 1
    assert summary.status_counts == {"VERIFIED": 1}
    with factory() as db:
        asset = db.get(Asset, asset_id)
        assert asset.integrity_status == "VERIFIED"
        events = list(db.scalars(select(AuditEvent).where(AuditEvent.chain_id == device_id)))
        assert [event.event_type for event in events] == [
            "INTEGRITY_CHECK_STARTED",
            "INTEGRITY_CHECK_STARTED",
            "INTEGRITY_CHECK_PASSED",
        ]
