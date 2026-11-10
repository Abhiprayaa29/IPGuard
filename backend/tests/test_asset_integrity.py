"""Tests for persisted ciphertext integrity checks and safe storage paths."""

import hashlib
import importlib.util
import os
from pathlib import Path
import stat
import threading
from types import SimpleNamespace
import uuid

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.models.asset import Asset
from app.models.auth import Device
from app.services import asset_integrity, asset_storage
from app.services.asset_storage import StoragePathError


@pytest.fixture
def database(tmp_path):
    postgres_test_url = os.getenv("IPGUARD_TEST_POSTGRES_URL")
    if postgres_test_url:
        parsed_url = make_url(postgres_test_url)
        if not parsed_url.drivername.startswith("postgresql") or not (
            parsed_url.database and parsed_url.database.lower().endswith("_ipguard_test")
        ):
            pytest.fail(
                "IPGUARD_TEST_POSTGRES_URL must point to an isolated PostgreSQL database "
                "whose name ends with _ipguard_test."
            )
        engine = create_engine(postgres_test_url, pool_pre_ping=True)
        # The environment variable is an explicit opt-in to a disposable test DB.
        Base.metadata.drop_all(engine)
    else:
        engine = create_engine(
            f"sqlite:///{tmp_path / 'integrity-tests.sqlite'}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        if postgres_test_url:
            Base.metadata.drop_all(engine)
        engine.dispose()


def make_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(
        asset_storage,
        "get_settings",
        lambda: type("Settings", (), {"storage_directory": tmp_path})(),
    )
    return tmp_path


def add_asset(factory, storage_key: str, baseline: str) -> uuid.UUID:
    asset_id = uuid.uuid4()
    device_id = f"integrity-test-{uuid.uuid4().hex[:16]}"
    with factory.begin() as db:
        db.add(
            Device(
                device_id=device_id,
                device_name="Integrity test device",
                model="Test Device",
                android_version="14",
                public_key_x509="test-public-key",
                public_key_fingerprint=f"integrity-fp:{uuid.uuid4().hex}",
                status="ACTIVE",
            )
        )
        db.add(
            Asset(
                id=asset_id,
                device_id=device_id,
                original_filename="test.bin",
                storage_key=storage_key,
                content_type="application/octet-stream",
                size_bytes=10,
                nonce="dGVzdA==",
                sha256_hash=baseline,
            )
        )
    return asset_id


def read_asset(factory, asset_id: uuid.UUID) -> Asset:
    with factory() as db:
        return db.get(Asset, asset_id)


def test_new_asset_defaults_to_pending(database):
    _, factory = database
    asset_id = add_asset(factory, uuid.uuid4().hex, "a" * 64)

    asset = read_asset(factory, asset_id)

    assert asset.integrity_status == "PENDING"
    assert asset.last_checked_at is None
    assert asset.last_observed_sha256 is None


def test_migration_backfills_existing_assets_as_pending_and_preserves_baseline(tmp_path):
    migration_path = (
        Path(__file__).parents[1]
        / "app"
        / "db"
        / "migrations"
        / "versions"
        / "0007_asset_integrity_metadata.py"
    )
    spec = importlib.util.spec_from_file_location("asset_integrity_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine(f"sqlite:///{tmp_path / 'migration-test.sqlite'}")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE assets "
                    "(id INTEGER PRIMARY KEY, sha256_hash VARCHAR(64) NOT NULL)"
                )
            )
            baseline = "f" * 64
            connection.execute(
                text("INSERT INTO assets (id, sha256_hash) VALUES (1, :baseline)"),
                {"baseline": baseline},
            )
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()

            old_asset = connection.execute(
                text("SELECT sha256_hash, integrity_status FROM assets WHERE id = 1")
            ).one()
            assert old_asset.sha256_hash == baseline
            assert old_asset.integrity_status == "PENDING"

            connection.execute(
                text("INSERT INTO assets (id, sha256_hash) VALUES (2, :baseline)"),
                {"baseline": baseline},
            )
            new_asset = connection.execute(
                text("SELECT integrity_status FROM assets WHERE id = 2")
            ).scalar_one()
            assert new_asset == "PENDING"
    finally:
        engine.dispose()


def test_streaming_hash_matches_digest_for_multiple_chunks(tmp_path, monkeypatch):
    storage = make_storage(tmp_path, monkeypatch)
    storage_key = uuid.uuid4().hex
    ciphertext = b"ciphertext" * 4096
    (storage / storage_key).write_bytes(ciphertext)

    observed = asset_storage.hash_ciphertext_file(storage_key, chunk_size=257)

    assert observed == hashlib.sha256(ciphertext).hexdigest()


def test_hash_rejects_nonpositive_chunk_size():
    with pytest.raises(ValueError, match="positive"):
        asset_storage.hash_ciphertext_file(uuid.uuid4().hex, chunk_size=0)


def test_store_baseline_is_hashed_from_final_file_streaming(tmp_path, monkeypatch):
    storage = make_storage(tmp_path, monkeypatch)
    ciphertext = b"ciphertext persisted to final path"
    original_hash = asset_storage.hash_ciphertext_file
    calls = []

    def observe_final_file(storage_key, chunk_size=1024 * 1024):
        final_path = storage / storage_key
        assert final_path.is_file()
        assert not final_path.with_name(f"{storage_key}.tmp").exists()
        calls.append(storage_key)
        return original_hash(storage_key, chunk_size=chunk_size)

    monkeypatch.setattr(asset_storage, "hash_ciphertext_file", observe_final_file)

    stored = asset_storage.store_ciphertext_file(ciphertext)

    assert calls == [stored["storage_key"]]
    assert stored["sha256_hash"] == hashlib.sha256(ciphertext).hexdigest()


def test_hashing_failure_does_not_return_baseline_or_leave_final_file(tmp_path, monkeypatch):
    storage = make_storage(tmp_path, monkeypatch)

    def fail_hash(*args, **kwargs):
        raise PermissionError("storage read denied")

    monkeypatch.setattr(asset_storage, "hash_ciphertext_file", fail_hash)

    with pytest.raises(PermissionError):
        asset_storage.store_ciphertext_file(b"ciphertext")

    assert list(storage.iterdir()) == []


def test_integrity_hash_rejects_symlink_or_reparse_target_outside_storage(
    tmp_path, monkeypatch
):
    storage = make_storage(tmp_path / "storage", monkeypatch)
    storage.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside the asset directory")
    storage_key = uuid.uuid4().hex
    link = storage / storage_key
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlink creation is unavailable on this host: {exc}")

    with pytest.raises(StoragePathError):
        asset_storage.hash_ciphertext_file(storage_key)


def test_integrity_hash_rejects_windows_reparse_point_attribute(tmp_path, monkeypatch):
    storage = make_storage(tmp_path, monkeypatch)
    storage_key = uuid.uuid4().hex
    candidate = storage / storage_key
    candidate.write_bytes(b"test data")
    original_lstat = Path.lstat

    def lstat_with_reparse_flag(path):
        if path == candidate:
            return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat_with_reparse_flag)

    with pytest.raises(StoragePathError, match="reparse point"):
        asset_storage.hash_ciphertext_file(storage_key)


def test_integrity_hash_rejects_resolved_target_outside_storage(tmp_path, monkeypatch):
    storage = make_storage(tmp_path / "storage", monkeypatch)
    storage.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside storage")
    storage_key = uuid.uuid4().hex
    candidate = storage / storage_key
    candidate.write_bytes(b"placeholder")
    original_resolve = Path.resolve

    def resolve_outside(path, strict=False):
        if path == candidate:
            return outside
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_outside)

    with pytest.raises(StoragePathError, match="outside the storage"):
        asset_storage.hash_ciphertext_file(storage_key)


def test_verify_persists_verified_and_preserves_baseline(
    database, tmp_path, monkeypatch
):
    _, factory = database
    storage = make_storage(tmp_path, monkeypatch)
    storage_key = uuid.uuid4().hex
    ciphertext = b"stored encrypted bytes"
    baseline = hashlib.sha256(ciphertext).hexdigest()
    (storage / storage_key).write_bytes(ciphertext)
    asset_id = add_asset(factory, storage_key, baseline)

    result = asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    asset = read_asset(factory, asset_id)
    assert result.status == "VERIFIED"
    assert asset.integrity_status == "VERIFIED"
    assert asset.last_checked_at is not None
    assert asset.last_observed_sha256 == baseline
    assert asset.sha256_hash == baseline


def test_verify_persists_mismatch_and_preserves_baseline(
    database, tmp_path, monkeypatch
):
    _, factory = database
    storage = make_storage(tmp_path, monkeypatch)
    storage_key = uuid.uuid4().hex
    baseline = hashlib.sha256(b"original ciphertext").hexdigest()
    actual = b"modified ciphertext"
    observed = hashlib.sha256(actual).hexdigest()
    (storage / storage_key).write_bytes(actual)
    asset_id = add_asset(factory, storage_key, baseline)

    result = asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    asset = read_asset(factory, asset_id)
    assert result.status == "MISMATCH"
    assert asset.integrity_status == "MISMATCH"
    assert asset.last_observed_sha256 == observed
    assert asset.sha256_hash == baseline


def test_verify_persists_missing_and_preserves_baseline(database, tmp_path, monkeypatch):
    make_storage(tmp_path, monkeypatch)
    _, factory = database
    baseline = "0" * 64
    asset_id = add_asset(factory, uuid.uuid4().hex, baseline)

    result = asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    asset = read_asset(factory, asset_id)
    assert result.status == "MISSING"
    assert asset.integrity_status == "MISSING"
    assert asset.last_observed_sha256 is None
    assert asset.sha256_hash == baseline


def test_verify_persists_error_and_preserves_baseline(database, monkeypatch):
    _, factory = database
    baseline = "0" * 64
    asset_id = add_asset(factory, uuid.uuid4().hex, baseline)

    def raise_io_error(*args, **kwargs):
        raise PermissionError("storage access denied")

    monkeypatch.setattr(asset_integrity, "inspect_ciphertext_file", raise_io_error)

    result = asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    asset = read_asset(factory, asset_id)
    assert result.status == "ERROR"
    assert asset.integrity_status == "ERROR"
    assert asset.last_observed_sha256 is None
    assert asset.sha256_hash == baseline


def test_invalid_storage_key_is_error_and_preserves_baseline(database):
    _, factory = database
    baseline = "0" * 64
    asset_id = add_asset(factory, "invalid-storage-key", baseline)

    result = asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    asset = read_asset(factory, asset_id)
    assert result.status == "ERROR"
    assert asset.integrity_status == "ERROR"
    assert asset.last_observed_sha256 is None
    assert asset.sha256_hash == baseline


def test_concurrent_checks_cannot_overwrite_newer_result(
    database, tmp_path, monkeypatch
):
    _, factory = database
    storage = make_storage(tmp_path, monkeypatch)
    storage_key = uuid.uuid4().hex
    original = b"original ciphertext"
    baseline = hashlib.sha256(original).hexdigest()
    path = storage / storage_key
    path.write_bytes(b"tampered ciphertext")
    asset_id = add_asset(factory, storage_key, baseline)

    first_hash_ready = threading.Event()
    release_first_hash = threading.Event()
    call_lock = threading.Lock()
    call_count = 0
    normal_inspect = asset_storage.inspect_ciphertext_file

    def controlled_inspect(key, chunk_size=1024 * 1024, include_ciphertext=False):
        nonlocal call_count
        with call_lock:
            call_count += 1
            call_number = call_count
        if call_number == 1:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            first_hash_ready.set()
            assert release_first_hash.wait(timeout=10)
            return digest, None
        return normal_inspect(key, chunk_size=chunk_size, include_ciphertext=include_ciphertext)

    monkeypatch.setattr(asset_integrity, "inspect_ciphertext_file", controlled_inspect)
    results = {}
    failures = []

    def run_check(name):
        try:
            check = asset_integrity.verify_asset_integrity(
                asset_id, session_factory=factory
            )
            results[name] = (check.status, check.audit_recorded)
        except Exception as exc:  # surface worker-thread failures in the test
            failures.append(exc)

    first = threading.Thread(target=run_check, args=("first",))
    first.start()
    assert first_hash_ready.wait(timeout=10)

    path.write_bytes(original)
    second = threading.Thread(target=run_check, args=("second",))
    second.start()
    second.join(timeout=10)
    assert not second.is_alive()

    release_first_hash.set()
    first.join(timeout=10)
    assert not first.is_alive()
    assert failures == []
    assert results == {"first": ("MISMATCH", False), "second": ("VERIFIED", True)}

    asset = read_asset(factory, asset_id)
    assert asset.integrity_status == "VERIFIED"
    assert asset.last_observed_sha256 == baseline
    assert asset.sha256_hash == baseline


def test_integrity_service_does_not_commit_unrelated_caller_session_changes(
    database, tmp_path, monkeypatch
):
    _, factory = database
    storage = make_storage(tmp_path, monkeypatch)
    storage_key = uuid.uuid4().hex
    ciphertext = b"known ciphertext"
    baseline = hashlib.sha256(ciphertext).hexdigest()
    (storage / storage_key).write_bytes(ciphertext)
    asset_id = add_asset(factory, storage_key, baseline)

    caller_session = factory()
    pending_asset = Asset(
        id=uuid.uuid4(),
        device_id="unrelated-device",
        original_filename="pending.bin",
        storage_key=uuid.uuid4().hex,
        content_type="application/octet-stream",
        size_bytes=1,
        nonce="dGVzdA==",
        sha256_hash="1" * 64,
    )
    caller_session.add(pending_asset)

    asset_integrity.verify_asset_integrity(asset_id, session_factory=factory)

    assert pending_asset in caller_session.new
    with factory() as observer:
        assert observer.get(Asset, pending_asset.id) is None
    caller_session.rollback()
    caller_session.close()


