"""Streaming integrity checks for encrypted Asset Vault files."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hmac
from typing import Literal
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.audit_chain import append_audit_event
from app.models.asset import Asset
from app.services.asset_storage import StorageNotFoundError, inspect_ciphertext_file

IntegrityStatus = Literal["VERIFIED", "MISMATCH", "MISSING", "ERROR"]
SessionFactory = Callable[[], Session]


@dataclass(frozen=True)
class IntegrityCheckResult:
    status: IntegrityStatus
    checked_at: datetime
    observed_sha256: str | None
    ciphertext: bytes | None = None
    audit_recorded: bool = False


def verify_asset_integrity(
    asset_id: uuid.UUID,
    session_factory: SessionFactory | None = None,
    chunk_size: int = 1024 * 1024,
    include_ciphertext: bool = False,
    actor_device_id: str | None = None,
) -> IntegrityCheckResult:
    """Check an asset and persist its result in isolated, ordered transactions.

    A short row-locked transaction records the PENDING claim and its audit event
    together. Hashing happens outside a transaction; a conditional result
    update prevents an older, slower check from overwriting a newer check. Each
    transaction uses a fresh session so unrelated caller changes cannot be
    committed by this service. If a process crashes while hashing, PENDING is
    backed by its started event and the next scheduled scan retries the asset.
    """
    if session_factory is None:
        from app.db.session import SessionLocal

        session_factory = SessionLocal

    checked_at = datetime.now(timezone.utc)
    audit_recorded = False
    with session_factory() as db:
        with db.begin():
            asset = db.scalar(
                select(Asset)
                .where(Asset.id == asset_id)
                .with_for_update()
            )
            if asset is None:
                raise LookupError("Asset not found.")

            previous_check = asset.last_checked_at
            if previous_check is not None:
                if previous_check.tzinfo is None:
                    previous_check = previous_check.replace(tzinfo=timezone.utc)
                if checked_at <= previous_check:
                    checked_at = previous_check + timedelta(microseconds=1)

            storage_key = asset.storage_key
            baseline_sha256 = asset.sha256_hash
            asset.integrity_status = "PENDING"
            asset.last_checked_at = checked_at
            asset.last_observed_sha256 = None
            db.flush()
            append_audit_event(
                db,
                chain_id=asset.device_id,
                actor_type="DEVICE" if actor_device_id else "SYSTEM",
                actor_device_id=actor_device_id,
                event_type="INTEGRITY_CHECK_STARTED",
                resource_type="asset",
                resource_id=str(asset_id),
                result="PENDING",
                payload={"integrity_status": "PENDING", "baseline_sha256": baseline_sha256},
            )

    observed_sha256: str | None = None
    ciphertext: bytes | None = None
    try:
        observed_sha256, ciphertext = inspect_ciphertext_file(
            storage_key,
            chunk_size=chunk_size,
            include_ciphertext=include_ciphertext,
        )
        status: IntegrityStatus = (
            "VERIFIED"
            if hmac.compare_digest(observed_sha256, baseline_sha256)
            else "MISMATCH"
        )
    except StorageNotFoundError:
        status = "MISSING"
    except Exception:
        # Storage or system failures are not proof of tampering.
        status = "ERROR"

    with session_factory() as db:
        with db.begin():
            checked_asset = db.scalar(
                select(Asset)
                .where(
                    Asset.id == asset_id,
                    Asset.last_checked_at == checked_at,
                )
                .with_for_update()
            )
            if checked_asset is not None:
                checked_asset.integrity_status = status
                checked_asset.last_observed_sha256 = observed_sha256
                db.flush()

                event_type, event_result = {
                    "VERIFIED": ("INTEGRITY_CHECK_PASSED", "VERIFIED"),
                    "MISMATCH": ("ASSET_TAMPERED", "MISMATCH"),
                    "MISSING": ("ASSET_MISSING", "MISSING"),
                    "ERROR": ("INTEGRITY_CHECK_ERROR", "ERROR"),
                }[status]
                event_payload = {
                    "integrity_status": status,
                    "baseline_sha256": baseline_sha256,
                }
                if observed_sha256 is not None:
                    event_payload["observed_sha256"] = observed_sha256

                append_audit_event(
                    db,
                    chain_id=checked_asset.device_id,
                    actor_type="DEVICE" if actor_device_id else "SYSTEM",
                    actor_device_id=actor_device_id,
                    event_type=event_type,
                    resource_type="asset",
                    resource_id=str(asset_id),
                    result=event_result,
                    payload=event_payload,
                )
                audit_recorded = True

    return IntegrityCheckResult(
        status=status,
        checked_at=checked_at,
        observed_sha256=observed_sha256,
        ciphertext=ciphertext,
        audit_recorded=audit_recorded,
    )
