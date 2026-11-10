"""Tests for the bounded, one-shot integrity worker."""

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
import pytest

from app.db.base import Base
from app.models.asset import Asset
from app.services import asset_storage
from app.workers import integrity


@pytest.fixture
def worker_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'integrity-worker.sqlite'}",
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


def _add_asset(factory, storage: Path, content: bytes) -> uuid.UUID:
    asset_id = uuid.uuid4()
    storage_key = uuid.uuid4().hex
    (storage / storage_key).write_bytes(content)
    with factory.begin() as db:
        db.add(
            Asset(
                id=asset_id,
                device_id="worker-device",
                original_filename="worker.bin",
                storage_key=storage_key,
                content_type="application/octet-stream",
                size_bytes=len(content),
                nonce="dGVzdA==",
                sha256_hash=hashlib.sha256(content).hexdigest(),
                created_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
    return asset_id


def test_worker_scans_multiple_bounded_batches(worker_context):
    factory, storage = worker_context
    asset_ids = [_add_asset(factory, storage, f"payload-{i}".encode()) for i in range(5)]

    summary = integrity.run_integrity_scan(batch_size=2, session_factory=factory)

    assert summary.scanned == 5
    assert summary.skipped == 0
    assert summary.failed == 0
    assert summary.status_counts == {"VERIFIED": 5}
    assert summary.last_asset_id is not None
    with factory() as db:
        assert all(db.get(Asset, asset_id).integrity_status == "VERIFIED" for asset_id in asset_ids)


def test_worker_continues_after_per_asset_failure(worker_context, monkeypatch):
    factory, storage = worker_context
    asset_ids = [_add_asset(factory, storage, f"payload-{i}".encode()) for i in range(3)]
    original_verify = integrity.verify_asset_integrity

    def fail_one(asset_id, **kwargs):
        if asset_id == asset_ids[1]:
            raise OSError("private storage detail")
        return original_verify(asset_id, **kwargs)

    monkeypatch.setattr(integrity, "verify_asset_integrity", fail_one)

    summary = integrity.run_integrity_scan(batch_size=1, session_factory=factory)

    assert summary.scanned == 2
    assert summary.failed == 1
    assert summary.status_counts == {"VERIFIED": 2}


def test_equal_timestamp_and_during_scan_assets_are_found_on_next_run(
    worker_context, monkeypatch
):
    factory, storage = worker_context
    cutoff = datetime(2030, 1, 1, tzinfo=timezone.utc)
    before_cutoff = _add_asset(factory, storage, b"present before scan")
    equal_timestamp = _add_asset(factory, storage, b"same timestamp")
    with factory.begin() as db:
        db.get(Asset, before_cutoff).created_at = cutoff - timedelta(seconds=1)
        db.get(Asset, equal_timestamp).created_at = cutoff

    class FixedClockSession(Session):
        def scalar(self, statement, *args, **kwargs):
            if "now()" in str(statement).casefold():
                return self.info["snapshot_cutoff"]
            return super().scalar(statement, *args, **kwargs)

    def scan_factory(snapshot_cutoff):
        return sessionmaker(
            bind=factory.kw["bind"],
            class_=FixedClockSession,
            expire_on_commit=False,
            info={"snapshot_cutoff": snapshot_cutoff},
        )

    inserted_during_scan = uuid.uuid4()
    original_verify = integrity.verify_asset_integrity
    inserted = False

    def insert_while_checking(asset_id, **kwargs):
        nonlocal inserted
        result = original_verify(asset_id, **kwargs)
        if asset_id == before_cutoff and not inserted:
            inserted = True
            storage_key = uuid.uuid4().hex
            content = b"created while scan is running"
            (storage / storage_key).write_bytes(content)
            with factory.begin() as db:
                db.add(
                    Asset(
                        id=inserted_during_scan,
                        device_id="worker-device",
                        original_filename="during-scan.bin",
                        storage_key=storage_key,
                        content_type="application/octet-stream",
                        size_bytes=len(content),
                        nonce="dGVzdA==",
                        sha256_hash=hashlib.sha256(content).hexdigest(),
                        created_at=cutoff,
                    )
                )
        return result

    monkeypatch.setattr(integrity, "verify_asset_integrity", insert_while_checking)
    first = integrity.run_integrity_scan(batch_size=1, session_factory=scan_factory(cutoff))

    assert first.scanned == 1
    with factory() as db:
        assert db.get(Asset, equal_timestamp).integrity_status == "PENDING"
        assert db.get(Asset, inserted_during_scan).integrity_status == "PENDING"

    second_cutoff = cutoff + timedelta(seconds=1)
    second = integrity.run_integrity_scan(
        batch_size=1,
        session_factory=scan_factory(second_cutoff),
    )

    assert second.scanned == 3
    with factory() as db:
        assert db.get(Asset, equal_timestamp).integrity_status == "VERIFIED"
        assert db.get(Asset, inserted_during_scan).integrity_status == "VERIFIED"


@pytest.mark.parametrize("batch_size", [0, -1, 1001, True])
def test_worker_rejects_invalid_batch_size(batch_size):
    with pytest.raises(ValueError, match="batch_size"):
        integrity.run_integrity_scan(batch_size=batch_size, session_factory=lambda: None)
