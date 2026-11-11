"""Unit and isolated-database integration tests for Audit Hash Chain."""

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import uuid

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, delete, func, select, text, update
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.models.audit import AuditChainHead, AuditEvent
from app.services.audit_chain import (
    AuditChainError,
    GENESIS_HASH,
    append_audit_event,
    canonicalize_payload,
    verify_audit_chain,
)


@pytest.fixture
def audit_db(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'audit-chain.sqlite'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        engine.dispose()


def _append(factory, *, chain_id="audit-device-1", **overrides):
    fields = {
        "chain_id": chain_id,
        "actor_type": "DEVICE",
        "actor_device_id": "audit-device-1",
        "event_type": "ASSET_UPLOADED",
        "resource_type": "asset",
        "resource_id": str(uuid.uuid4()),
        "result": "SUCCESS",
        "payload": {"byte_count": 32, "status": "stored"},
        "occurred_at": datetime(2026, 11, 9, 10, 11, 12, 123456, tzinfo=timezone.utc),
    }
    fields.update(overrides)
    with factory() as db:
        with db.begin():
            return append_audit_event(db, **fields)


def test_payload_canonicalization_is_deterministic_and_retains_utf8_bytes():
    first = canonicalize_payload({"z": 3, "nested": {"b": "ü", "a": 1}})
    second = canonicalize_payload({"nested": {"a": 1, "b": "ü"}, "z": 3})

    assert first == second
    assert first.decode("utf-8") == '{"nested":{"a":1,"b":"ü"},"z":3}'


@pytest.mark.parametrize(
    "payload",
    [
        {"token": "sensitive"},
        {"nested": {"private_key": "sensitive"}},
        {"file content": "sensitive"},
        {"float": 1.25},
        {"bytes": b"not JSON"},
    ],
)
def test_payload_rejects_secrets_and_noncanonical_values(payload):
    with pytest.raises(AuditChainError):
        canonicalize_payload(payload)


def test_append_starts_at_genesis_links_events_and_verifies(audit_db):
    _, factory = audit_db
    first = _append(factory)
    second = _append(factory, event_type="ASSET_RENAMED", result="SUCCESS")

    assert first.sequence == 1
    assert first.prev_hash == GENESIS_HASH
    assert second.sequence == 2
    assert second.prev_hash == first.event_hash
    assert isinstance(first.canonical_payload, bytes)
    assert first.canonical_payload == b'{"byte_count":32,"status":"stored"}'

    with factory() as db:
        result = verify_audit_chain(db, "audit-device-1")

    assert result.valid is True
    assert result.event_count == 2
    assert result.verified_through_sequence == 2


def test_append_requires_caller_transaction(audit_db):
    _, factory = audit_db
    with factory() as db:
        with pytest.raises(AuditChainError, match="active caller transaction"):
            append_audit_event(
                db,
                chain_id="audit-device-1",
                event_type="ASSET_UPLOADED",
                resource_type="asset",
                resource_id="asset-1",
                result="SUCCESS",
                payload={},
            )


def test_append_rollback_removes_event_and_head(audit_db):
    _, factory = audit_db
    with factory() as db:
        with pytest.raises(RuntimeError, match="force rollback"):
            with db.begin():
                append_audit_event(
                    db,
                    chain_id="rolled-back-device",
                    event_type="ASSET_UPLOADED",
                    resource_type="asset",
                    resource_id="asset-1",
                    result="SUCCESS",
                    payload={},
                )
                raise RuntimeError("force rollback")

    with factory() as db:
        assert db.get(AuditChainHead, "rolled-back-device") is None
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.chain_id == "rolled-back-device"
            )
        ) == 0


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("event_type", "ASSET_DELETED"),
        ("occurred_at", datetime(2026, 11, 9, 10, 11, 13, tzinfo=timezone.utc)),
        ("actor_type", "SYSTEM"),
        ("actor_device_id", "another-device"),
        ("resource_type", "device"),
        ("resource_id", "other-resource"),
        ("result", "FAILURE"),
        ("canonical_payload", b'{"byte_count":99,"status":"stored"}'),
        ("prev_hash", "f" * 64),
        ("event_hash", "e" * 64),
        ("event_id", uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")),
        ("sequence", 2),
    ],
)
def test_verifier_detects_mutated_immutable_event_metadata(audit_db, column, replacement):
    _, factory = audit_db
    event = _append(factory)
    with factory.begin() as db:
        if column == "chain_id":
            db.add(AuditChainHead(chain_id="other-chain", last_sequence=0, last_hash=GENESIS_HASH))
            db.flush()
        db.execute(
            update(AuditEvent)
            .where(AuditEvent.event_id == event.event_id)
            .values({column: replacement})
        )

    with factory() as db:
        result = verify_audit_chain(db, "audit-device-1")
    assert result.valid is False
    assert result.reason_code is not None


def test_verifier_detects_chain_id_mutation(audit_db):
    _, factory = audit_db
    event = _append(factory)
    with factory.begin() as db:
        db.add(AuditChainHead(chain_id="other-chain", last_sequence=0, last_hash=GENESIS_HASH))
        db.flush()
        db.execute(
            update(AuditEvent)
            .where(AuditEvent.event_id == event.event_id)
            .values(chain_id="other-chain")
        )

    with factory() as db:
        source_result = verify_audit_chain(db, "audit-device-1")
        target_result = verify_audit_chain(db, "other-chain")
    assert source_result.valid is False
    assert target_result.valid is False


def test_verifier_detects_deleted_event(audit_db):
    _, factory = audit_db
    event = _append(factory)
    with factory.begin() as db:
        db.execute(delete(AuditEvent).where(AuditEvent.event_id == event.event_id))

    with factory() as db:
        result = verify_audit_chain(db, "audit-device-1")
    assert result.valid is False
    assert result.reason_code == "chain_sequence_mismatch"


def test_verifier_detects_reordered_events(audit_db):
    _, factory = audit_db
    first = _append(factory, event_type="ASSET_UPLOADED", result="SUCCESS")
    second = _append(factory, event_type="ASSET_DOWNLOADED", result="SUCCESS")
    with factory.begin() as db:
        # Temporarily move sequence 1 aside so we can swap sequences 1 and 2 cleanly
        db.execute(update(AuditEvent).where(AuditEvent.event_id == first.event_id).values(sequence=999))
        db.execute(update(AuditEvent).where(AuditEvent.event_id == second.event_id).values(sequence=1))
        db.execute(update(AuditEvent).where(AuditEvent.event_id == first.event_id).values(sequence=2))

    with factory() as db:
        result = verify_audit_chain(db, "audit-device-1")
    assert result.valid is False
    assert result.reason_code in ("previous_hash_mismatch", "event_hash_mismatch", "sequence_gap_or_reorder")


def test_orm_service_layer_rejects_event_update_and_delete(audit_db):
    _, factory = audit_db
    event = _append(factory)

    with factory() as db:
        loaded = db.get(AuditEvent, event.event_id)
        loaded.result = "ALTERED"
        with pytest.raises(RuntimeError, match="append-only"):
            db.flush()
        db.rollback()

    with factory() as db:
        loaded = db.get(AuditEvent, event.event_id)
        db.delete(loaded)
        with pytest.raises(RuntimeError, match="append-only"):
            db.flush()
        db.rollback()


def test_migration_0008_is_incremental_and_seeds_existing_device_heads(tmp_path):
    migration_path = (
        Path(__file__).parents[1]
        / "app"
        / "db"
        / "migrations"
        / "versions"
        / "0008_audit_hash_chain.py"
    )
    spec = importlib.util.spec_from_file_location("audit_chain_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.down_revision == "0007_asset_integrity_metadata"

    engine = create_engine(f"sqlite:///{tmp_path / 'audit-migration.sqlite'}")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE devices (device_id VARCHAR(64) PRIMARY KEY)"))
            connection.execute(text("INSERT INTO devices (device_id) VALUES ('legacy-device')"))
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()
            seeded = connection.execute(
                text("SELECT last_sequence, last_hash FROM audit_chain_heads WHERE chain_id='legacy-device'")
            ).one()
            assert seeded.last_sequence == 0
            assert seeded.last_hash == GENESIS_HASH
    finally:
        engine.dispose()
