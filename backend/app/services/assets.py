"""
IPGuard Milestone 3 — Asset Vault Service Layer.
Coordinates database persistence, XChaCha20-Poly1305 encryption, AAD context binding,
storage atomic writes, and owner isolation.
"""

import uuid
import logging
from collections.abc import Mapping

from fastapi import status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.asset import Asset
from app.services.asset_crypto import (
    AssetDecryptionError,
    ENCRYPTION_VERSION_LEGACY,
    ENCRYPTION_VERSION_V1,
    build_asset_aad,
    decrypt_asset_bytes,
    derive_asset_key,
    encrypt_asset_bytes,
)
from app.services.audit_chain import AuditChainError, append_audit_event
from app.services.asset_integrity import verify_asset_integrity
from app.services.asset_storage import delete_stored_file, store_ciphertext_file
from app.services.asset_validation import (
    AssetValidationError,
    detect_and_validate_file,
    sanitize_filename,
)

logger = logging.getLogger(__name__)


def _cleanup_uncommitted_ciphertext(asset_id: uuid.UUID, storage_key: str) -> None:
    """Remove a file whose metadata transaction definitely did not commit."""
    try:
        removed = delete_stored_file(storage_key)
    except Exception as exc:
        removed = False
        error_type = type(exc).__name__
    else:
        error_type = "CleanupReturnedFalse"

    if not removed:
        # The opaque key is needed to reconcile orphan files; do not log paths,
        # ciphertext, exception text, or cryptographic material.
        logger.error(
            "asset_upload_orphan_cleanup_failed asset_id=%s storage_key=%s error_type=%s",
            asset_id,
            storage_key,
            error_type,
        )


def create_asset(
    db: Session,
    device_id: str,
    filename: str,
    content_type: str | None,
    data: bytes,
    *,
    asset_id: uuid.UUID | None = None,
    source_asset_id: uuid.UUID | None = None,
    derivative_type: str | None = None,
    watermark_id: uuid.UUID | None = None,
    stego_format_version: int | None = None,
    audit_event_type: str | None = None,
    audit_payload: Mapping[str, object] | None = None,
) -> Asset:
    """
    Validate, encrypt with true XChaCha20-Poly1305 and per-device HKDF,
    persist ciphertext atomically to disk, and save asset metadata in PostgreSQL.
    """
    settings = get_settings()
    asset_id = asset_id or uuid.uuid4()
    is_derivative = source_asset_id is not None
    if is_derivative:
        if (
            derivative_type != "PNG_LSB"
            or watermark_id is None
            or stego_format_version is None
            or audit_event_type != "ASSET_STEGO_EMBEDDED"
            or audit_payload is None
        ):
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="invalid_derivative_metadata",
                message="PNG LSB derivative metadata and audit event are required.",
            )
        get_asset(db, source_asset_id, device_id)
    elif any(value is not None for value in (derivative_type, watermark_id, stego_format_version, audit_event_type, audit_payload)):
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_derivative_metadata",
            message="Derivative metadata requires a source asset.",
        )

    # 1. Size bounds check
    if not data or len(data) == 0:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="empty_file",
            message="Uploaded file cannot be empty (0 bytes).",
        )

    if len(data) > settings.asset_vault_max_file_size_bytes:
        max_mb = settings.asset_vault_max_file_size_bytes // (1024 * 1024)
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="file_too_large",
            message=f"File size exceeds the {max_mb} MB limit.",
        )

    # 2. Filename and magic byte validation
    try:
        sanitized_name = sanitize_filename(filename)
        trusted_mime = detect_and_validate_file(data, sanitized_name, content_type)
    except AssetValidationError as exc:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_file",
            message=str(exc),
        ) from exc

    # 3. Cryptographic derivation and encryption
    encryption_version = ENCRYPTION_VERSION_V1

    device_key = derive_asset_key(device_id)
    aad = build_asset_aad(asset_id, device_id, version=encryption_version)

    try:
        ciphertext, nonce_b64 = encrypt_asset_bytes(data, device_key, aad=aad)
    except Exception as exc:
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="encryption_failed",
            message="Failed to securely encrypt asset binary.",
        ) from exc

    # 4. Atomic disk storage
    try:
        stored = store_ciphertext_file(ciphertext)
    except Exception as exc:
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="storage_write_failed",
            message="Failed to store encrypted asset file on disk.",
        ) from exc

    # 5. Persist metadata. A flush failure is known to precede commit, so its
    # ciphertext can be cleaned up. A commit exception has an ambiguous outcome
    # and must leave the file in place for reconciliation.
    asset = Asset(
        id=asset_id,
        device_id=device_id,
        original_filename=sanitized_name,
        storage_key=stored["storage_key"],
        content_type=trusted_mime,
        size_bytes=len(data),
        nonce=nonce_b64,
        sha256_hash=stored["sha256_hash"],
        source_asset_id=source_asset_id,
        derivative_type=derivative_type,
        watermark_id=watermark_id,
        stego_format_version=stego_format_version,
        integrity_status="PENDING",
        last_checked_at=None,
        last_observed_sha256=None,
        encryption_version=encryption_version,
    )

    try:
        db.add(asset)
        db.flush()
        if audit_event_type is not None:
            append_audit_event(
                db,
                chain_id=device_id,
                actor_type="DEVICE",
                actor_device_id=device_id,
                event_type=audit_event_type,
                resource_type="asset",
                resource_id=str(asset_id),
                result="SUCCESS",
                payload=audit_payload or {},
            )
    except Exception as exc:
        try:
            db.rollback()
        except Exception as rollback_exc:
            logger.error(
                "asset_upload_precommit_rollback_failed asset_id=%s error_type=%s",
                asset_id,
                type(rollback_exc).__name__,
            )
        _cleanup_uncommitted_ciphertext(asset_id, stored["storage_key"])
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="database_commit_failed",
            message="Failed to save asset metadata in database.",
        ) from exc

    try:
        db.commit()
    except Exception as exc:
        try:
            db.rollback()
        except Exception as rollback_exc:
            logger.error(
                "asset_upload_commit_rollback_failed asset_id=%s error_type=%s",
                asset_id,
                type(rollback_exc).__name__,
            )
        logger.error(
            "asset_upload_commit_outcome_unknown asset_id=%s storage_key=%s error_type=%s",
            asset_id,
            stored["storage_key"],
            type(exc).__name__,
        )
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="database_commit_failed",
            message="Could not confirm asset metadata persistence. Check the asset list before retrying.",
        ) from exc

    # The transaction is known committed; a refresh failure must never delete
    # the ciphertext or imply that the upload was rolled back.
    try:
        db.refresh(asset)
    except Exception as exc:
        logger.error(
            "asset_upload_postcommit_refresh_failed asset_id=%s storage_key=%s error_type=%s",
            asset_id,
            stored["storage_key"],
            type(exc).__name__,
        )
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="asset_saved_refresh_failed",
            message="Asset was saved, but its response could not be prepared. Check the asset list before retrying.",
        ) from exc

    return asset


def list_assets(db: Session, device_id: str) -> list[Asset]:
    """Retrieve all digital assets owned by the authenticated device in descending order."""
    stmt = (
        select(Asset)
        .where(Asset.device_id == device_id)
        .order_by(desc(Asset.created_at))
    )
    return list(db.scalars(stmt).all())


def get_asset(db: Session, asset_id: uuid.UUID, device_id: str) -> Asset:
    """
    Retrieve one digital asset owned by the authenticated device.
    Fails closed with 404 if not found or belongs to another tenant.
    """
    stmt = select(Asset).where(
        Asset.id == asset_id,
        Asset.device_id == device_id,
    )
    asset = db.scalar(stmt)
    if not asset:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="asset_not_found",
            message="Digital asset not found or access denied.",
        )
    return asset


def download_asset(
    db: Session,
    asset_id: uuid.UUID,
    device_id: str,
) -> tuple[Asset, bytes]:
    """
    Retrieve, verify integrity, and decrypt an asset owned by the caller.
    Returns (Asset, plaintext_bytes).
    """
    asset = get_asset(db, asset_id, device_id)

    # Verify and capture the same ciphertext bytes before they can reach decryption.
    # A separate session keeps integrity writes isolated from caller transaction state.
    try:
        integrity = verify_asset_integrity(
            asset.id,
            session_factory=sessionmaker(bind=db.get_bind(), expire_on_commit=False),
            include_ciphertext=True,
            actor_device_id=device_id,
        )
    except LookupError as exc:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="asset_not_found",
            message="Digital asset not found or access denied.",
        ) from exc
    except (SQLAlchemyError, AuditChainError) as exc:
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="asset_integrity_unavailable",
            message="Asset integrity could not be verified. Please retry later.",
        ) from exc

    if integrity.status == "MISSING":
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="asset_file_missing",
            message="Encrypted asset binary not found on storage.",
        )
    if integrity.status == "MISMATCH":
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="integrity_check_failed",
            message="Stored asset failed its integrity check.",
        )
    if (
        integrity.status != "VERIFIED"
        or integrity.ciphertext is None
        or not integrity.audit_recorded
    ):
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="asset_integrity_unavailable",
            message="Asset integrity could not be verified. Please retry later.",
        )

    ciphertext = integrity.ciphertext

    # Derive owner key only after the exact ciphertext was verified.
    device_key = derive_asset_key(device_id)

    # 3. Determine AAD context based on version
    if asset.encryption_version == ENCRYPTION_VERSION_V1:
        aad = build_asset_aad(asset.id, device_id, version=asset.encryption_version)
    else:
        # Legacy fallback without AAD
        aad = None

    # 4. Decrypt via XChaCha20-Poly1305 and verify Poly1305 tag
    try:
        plaintext = decrypt_asset_bytes(
            ciphertext,
            asset.nonce,
            device_key,
            aad=aad,
        )
    except AssetDecryptionError as exc:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="decryption_failed",
            message=f"Cryptographic authentication failed: {exc}",
        ) from exc

    return asset, plaintext


def rename_asset(
    db: Session,
    asset_id: uuid.UUID,
    device_id: str,
    new_filename: str,
) -> Asset:
    """
    Safely rename an asset without modifying its encrypted binary contents.
    Updates original_filename and refreshed updated_at timestamp.
    """
    try:
        sanitized_name = sanitize_filename(new_filename)
    except AssetValidationError as exc:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_filename",
            message=str(exc),
        ) from exc

    asset = get_asset(db, asset_id, device_id)
    asset.original_filename = sanitized_name

    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(
    db: Session,
    asset_id: uuid.UUID,
    device_id: str,
) -> bool:
    """
    Delete an asset metadata record from PostgreSQL and unlink its binary from disk.
    Guarantees consistent state without orphaned metadata.
    """
    asset = get_asset(db, asset_id, device_id)
    storage_key = asset.storage_key

    has_derivatives = db.scalar(
        select(Asset.id).where(Asset.source_asset_id == asset_id).limit(1)
    )
    if has_derivatives is not None:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="asset_has_derivatives",
            message="Delete linked derivative assets before deleting this source asset.",
        )

    db.delete(asset)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="asset_has_derivatives",
            message="Delete linked derivative assets before deleting this source asset.",
        ) from exc

    # Unlink binary from storage after successful database deletion
    delete_stored_file(storage_key)
    return True
