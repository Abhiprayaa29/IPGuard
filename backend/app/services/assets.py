"""
IPGuard Milestone 3 — Asset Vault Service Layer.
Coordinates database persistence, XChaCha20-Poly1305 encryption, AAD context binding,
storage atomic writes, and owner isolation.
"""

from pathlib import Path
import uuid

from fastapi import status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

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
from app.services.asset_storage import (
    StorageIntegrityError,
    StorageNotFoundError,
    delete_stored_file,
    load_ciphertext_file,
    store_ciphertext_file,
)
from app.services.asset_validation import (
    AssetValidationError,
    detect_and_validate_file,
    sanitize_filename,
)


def create_asset(
    db: Session,
    device_id: str,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> Asset:
    """
    Validate, encrypt with true XChaCha20-Poly1305 and per-device HKDF,
    persist ciphertext atomically to disk, and save asset metadata in PostgreSQL.
    """
    settings = get_settings()

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
    asset_id = uuid.uuid4()
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

    # 5. Database metadata persistence with automatic disk cleanup on failure
    asset = Asset(
        id=asset_id,
        device_id=device_id,
        original_filename=sanitized_name,
        storage_key=stored["storage_key"],
        content_type=trusted_mime,
        size_bytes=len(data),
        nonce=nonce_b64,
        sha256_hash=stored["sha256_hash"],
        encryption_version=encryption_version,
    )

    try:
        db.add(asset)
        db.commit()
        db.refresh(asset)
    except Exception as exc:
        db.rollback()
        delete_stored_file(stored["storage_key"])
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="database_commit_failed",
            message="Failed to save asset metadata in database.",
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

    # 1. Load ciphertext and verify SHA-256 baseline digest
    try:
        ciphertext = load_ciphertext_file(
            asset.storage_key,
            expected_hash=asset.sha256_hash,
        )
    except StorageNotFoundError as exc:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="asset_file_missing",
            message="Encrypted asset binary not found on storage.",
        ) from exc
    except StorageIntegrityError as exc:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="integrity_check_failed",
            message=str(exc),
        ) from exc

    # 2. Derive owner key
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

    db.delete(asset)
    db.commit()

    # Unlink binary from storage after successful database deletion
    delete_stored_file(storage_key)
    return True
