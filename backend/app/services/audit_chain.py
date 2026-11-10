"""Deterministic SHA-256 append and verification services for audit chains."""

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import re
from typing import Any, Literal
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.audit import AuditChainHead, AuditEvent

AUDIT_DOMAIN = b"IPGUARD-AUDIT-V1\x00"
GENESIS_HASH = "0" * 64
ActorType = Literal["DEVICE", "SYSTEM"]

_EVENT_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_CHAIN_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_FORBIDDEN_PAYLOAD_KEYS = {
    "plaintext",
    "ciphertext",
    "token",
    "access_token",
    "session_token",
    "secret",
    "password",
    "key",
    "private_key",
    "encryption_key",
    "key_material",
    "signature",
    "storage_path",
    "path",
    "file_content",
    "content_bytes",
}


class AuditChainError(ValueError):
    """Raised when an audit event cannot be safely constructed or appended."""


@dataclass(frozen=True)
class AuditVerificationResult:
    valid: bool
    chain_id: str
    event_count: int
    verified_through_sequence: int
    mismatch_sequence: int | None = None
    reason_code: str | None = None


def canonicalize_payload(payload: Mapping[str, Any]) -> bytes:
    """Return UTF-8 canonical JSON bytes for allowlisted JSON-compatible data."""
    if not isinstance(payload, Mapping):
        raise AuditChainError("Audit payload must be a mapping.")
    _validate_payload_value(payload)
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise AuditChainError("Audit payload is not canonicalizable.") from exc


def _validate_payload_value(value: Any, parent_key: str | None = None) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise AuditChainError("Audit payload keys must be strings.")
            normalized_key = re.sub(r"[^a-z0-9]", "", key.casefold())
            forbidden_normalized = {
                re.sub(r"[^a-z0-9]", "", forbidden)
                for forbidden in _FORBIDDEN_PAYLOAD_KEYS
            }
            if normalized_key in forbidden_normalized or any(
                token in normalized_key
                for token in (
                    "plaintext",
                    "ciphertext",
                    "token",
                    "secret",
                    "privatekey",
                    "encryptionkey",
                    "keymaterial",
                    "signature",
                    "storagepath",
                    "filecontent",
                    "contentbytes",
                )
            ) or normalized_key.endswith("key"):
                raise AuditChainError("Audit payload contains a forbidden field.")
            _validate_payload_value(nested, normalized_key)
        return
    if isinstance(value, list):
        for nested in value:
            _validate_payload_value(nested, parent_key)
        return
    if value is None or isinstance(value, (str, bool, int)):
        return
    # Floats, bytes, dates, ORM values, and custom encoders make the wire format
    # ambiguous. Callers must pass already-normalized JSON primitives.
    raise AuditChainError("Audit payload contains a non-JSON or unsupported value.")


def _utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _canonical_event_bytes(
    *,
    chain_id: str,
    event_id: uuid.UUID,
    sequence: int,
    occurred_at: datetime,
    actor_type: str,
    actor_device_id: str | None,
    event_type: str,
    resource_type: str,
    resource_id: str | None,
    result: str,
    canonical_payload: bytes,
    prev_hash: str,
) -> bytes:
    envelope = {
        "actor": {"device_id": actor_device_id, "type": actor_type},
        "canonical_payload_b64": base64.b64encode(canonical_payload).decode("ascii"),
        "chain_id": chain_id,
        "event_id": str(event_id),
        "event_type": event_type,
        "occurred_at": _utc_timestamp(occurred_at),
        "prev_hash": prev_hash,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "result": result,
        "schema_version": 1,
        "sequence": sequence,
    }
    return json.dumps(
        envelope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _compute_event_hash(**event_fields: Any) -> str:
    serialized_event = _canonical_event_bytes(**event_fields)
    return hashlib.sha256(AUDIT_DOMAIN + serialized_event).hexdigest()


def _lock_or_create_head(db: Session, chain_id: str) -> AuditChainHead:
    head = db.scalar(
        select(AuditChainHead)
        .where(AuditChainHead.chain_id == chain_id)
        .with_for_update()
    )
    if head is not None:
        return head

    dialect = db.get_bind().dialect.name
    insert_factory = {
        "postgresql": postgres_insert,
        "sqlite": sqlite_insert,
    }.get(dialect)
    if insert_factory is None:
        raise AuditChainError("Audit chain head initialization requires PostgreSQL or SQLite.")

    # ON CONFLICT avoids a first-append race without a SAVEPOINT. That also
    # keeps SQLite's outer transaction atomic for isolated local tests.
    db.execute(
        insert_factory(AuditChainHead)
        .values(chain_id=chain_id, last_sequence=0, last_hash=GENESIS_HASH)
        .on_conflict_do_nothing(index_elements=[AuditChainHead.chain_id])
    )
    head = db.scalar(
        select(AuditChainHead)
        .where(AuditChainHead.chain_id == chain_id)
        .with_for_update()
    )
    if head is None:
        raise AuditChainError("Could not acquire or initialize audit chain head.")
    return head


def append_audit_event(
    db: Session,
    *,
    chain_id: str,
    event_type: str,
    resource_type: str,
    resource_id: str | None,
    result: str,
    payload: Mapping[str, Any],
    actor_type: ActorType = "SYSTEM",
    actor_device_id: str | None = None,
    occurred_at: datetime | None = None,
) -> AuditEvent:
    """Append one event in the caller's transaction; this function never commits."""
    if not db.in_transaction():
        raise AuditChainError("Audit append requires an active caller transaction.")
    if not isinstance(chain_id, str) or not _CHAIN_ID_RE.fullmatch(chain_id):
        raise AuditChainError("Invalid audit chain identifier.")
    if not isinstance(event_type, str) or not _EVENT_TYPE_RE.fullmatch(event_type):
        raise AuditChainError("Invalid audit event type.")
    if actor_type not in ("DEVICE", "SYSTEM"):
        raise AuditChainError("Invalid audit actor type.")
    if actor_type == "DEVICE" and not actor_device_id:
        raise AuditChainError("Device audit events require an actor device identifier.")
    if actor_type == "DEVICE" and actor_device_id != chain_id:
        raise AuditChainError("Device actor must match the per-device audit chain.")
    if actor_type == "SYSTEM" and actor_device_id is not None:
        raise AuditChainError("System audit events cannot include a device actor.")
    if actor_device_id is not None and (
        not isinstance(actor_device_id, str)
        or len(actor_device_id) > 64
        or not _IDENTIFIER_RE.fullmatch(actor_device_id)
    ):
        raise AuditChainError("Invalid actor device identifier.")
    if not isinstance(resource_type, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", resource_type):
        raise AuditChainError("Invalid audit resource type.")
    if resource_id is not None and (
        not isinstance(resource_id, str) or not _IDENTIFIER_RE.fullmatch(resource_id)
    ):
        raise AuditChainError("Invalid audit resource identifier.")
    if not isinstance(result, str) or not result or len(result) > 32:
        raise AuditChainError("Invalid audit event result.")

    canonical_payload = canonicalize_payload(payload)
    if len(canonical_payload) > 16 * 1024:
        raise AuditChainError("Audit payload exceeds the 16 KiB limit.")
    event_id = uuid.uuid4()
    occurred_at = _normalize_utc_datetime(occurred_at or datetime.now(timezone.utc))
    head = _lock_or_create_head(db, chain_id)
    sequence = head.last_sequence + 1
    prev_hash = head.last_hash
    fields = {
        "chain_id": chain_id,
        "event_id": event_id,
        "sequence": sequence,
        "occurred_at": occurred_at,
        "actor_type": actor_type,
        "actor_device_id": actor_device_id,
        "event_type": event_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "result": result,
        "canonical_payload": canonical_payload,
        "prev_hash": prev_hash,
    }
    event_hash = _compute_event_hash(**fields)
    event = AuditEvent(**fields, event_hash=event_hash)
    head.last_sequence = sequence
    head.last_hash = event_hash
    db.add(event)
    db.flush()
    return event


def verify_audit_chain(
    db: Session,
    chain_id: str,
    *,
    batch_size: int = 500,
) -> AuditVerificationResult:
    """Verify event metadata, payload bytes, sequence links, and persisted head."""
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer.")

    # Hold a shared row lock for a consistent full-chain read on PostgreSQL;
    # appenders take FOR UPDATE on this same row and wait until verification ends.
    head = db.scalar(
        select(AuditChainHead)
        .where(AuditChainHead.chain_id == chain_id)
        .with_for_update(read=True)
    )
    if head is None:
        return AuditVerificationResult(
            valid=False,
            chain_id=chain_id,
            event_count=0,
            verified_through_sequence=0,
            mismatch_sequence=0,
            reason_code="chain_head_missing",
        )

    expected_sequence = 1
    expected_prev_hash = GENESIS_HASH
    event_count = 0
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.chain_id == chain_id)
        .order_by(AuditEvent.sequence)
        .execution_options(yield_per=batch_size)
    )
    for event in db.scalars(stmt).yield_per(batch_size):
        if event.sequence != expected_sequence:
            return AuditVerificationResult(
                False,
                chain_id,
                event_count,
                expected_sequence - 1,
                mismatch_sequence=event.sequence,
                reason_code="sequence_gap_or_reorder",
            )
        if event.sequence > head.last_sequence:
            return AuditVerificationResult(
                False,
                chain_id,
                event_count,
                expected_sequence - 1,
                mismatch_sequence=event.sequence,
                reason_code="event_after_chain_head",
            )
        if not hmac.compare_digest(event.prev_hash, expected_prev_hash):
            return AuditVerificationResult(
                False,
                chain_id,
                event_count,
                expected_sequence - 1,
                mismatch_sequence=event.sequence,
                reason_code="previous_hash_mismatch",
            )

        try:
            recalculated = _compute_event_hash(
                chain_id=event.chain_id,
                event_id=event.event_id,
                sequence=event.sequence,
                occurred_at=event.occurred_at,
                actor_type=event.actor_type,
                actor_device_id=event.actor_device_id,
                event_type=event.event_type,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                result=event.result,
                canonical_payload=event.canonical_payload,
                prev_hash=event.prev_hash,
            )
        except (TypeError, ValueError, AttributeError):
            return AuditVerificationResult(
                False,
                chain_id,
                event_count,
                expected_sequence - 1,
                mismatch_sequence=event.sequence,
                reason_code="event_metadata_invalid",
            )
        if not hmac.compare_digest(recalculated, event.event_hash):
            return AuditVerificationResult(
                False,
                chain_id,
                event_count,
                expected_sequence - 1,
                mismatch_sequence=event.sequence,
                reason_code="event_hash_mismatch",
            )

        event_count += 1
        expected_sequence += 1
        expected_prev_hash = event.event_hash

    verified_sequence = expected_sequence - 1
    if verified_sequence != head.last_sequence:
        return AuditVerificationResult(
            False,
            chain_id,
            event_count,
            verified_sequence,
            mismatch_sequence=verified_sequence + 1,
            reason_code="chain_sequence_mismatch",
        )
    if not hmac.compare_digest(expected_prev_hash, head.last_hash):
        return AuditVerificationResult(
            False,
            chain_id,
            event_count,
            verified_sequence,
            mismatch_sequence=head.last_sequence,
            reason_code="chain_head_hash_mismatch",
        )

    return AuditVerificationResult(
        valid=True,
        chain_id=chain_id,
        event_count=event_count,
        verified_through_sequence=verified_sequence,
    )
