"""
IPGuard Milestone 3 — Asset Storage Service.
Manages atomic disk storage, retrieval, and deletion of XChaCha20-Poly1305 encrypted asset binaries.
Enforces strict storage key sanitization, SHA-256 ciphertext integrity verification, and directory isolation.
"""

import hashlib
import hmac
from pathlib import Path
import uuid

from app.core.config import get_settings


class StorageIntegrityError(ValueError):
    """Raised when ciphertext on disk fails SHA-256 integrity verification."""
    pass


class StorageNotFoundError(FileNotFoundError):
    """Raised when an encrypted asset binary is not found on disk."""
    pass


def _resolve_storage_path(storage_key: str) -> Path:
    """Validate storage key format strictly to prevent path traversal."""
    try:
        safe_key = uuid.UUID(hex=storage_key).hex
    except (ValueError, AttributeError) as exc:
        raise ValueError("Invalid storage key format.") from exc

    storage_dir = get_settings().storage_directory
    return storage_dir / safe_key


def store_ciphertext_file(ciphertext: bytes) -> dict:
    """
    Atomically write ciphertext to disk using a temporary file.
    Returns metadata dict: {storage_key, sha256_hash, ciphertext_size_bytes}.
    """
    storage_dir = get_settings().storage_directory
    storage_key = uuid.uuid4().hex
    target_path = storage_dir / storage_key
    temp_path = storage_dir / f"{storage_key}.tmp"

    sha256_digest = hashlib.sha256(ciphertext).hexdigest()

    try:
        temp_path.write_bytes(ciphertext)
        temp_path.replace(target_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    return {
        "storage_key": storage_key,
        "sha256_hash": sha256_digest,
        "ciphertext_size_bytes": len(ciphertext),
    }


def load_ciphertext_file(storage_key: str, expected_hash: str | None = None) -> bytes:
    """
    Read ciphertext binary from disk and optionally verify SHA-256 digest.
    Raises StorageNotFoundError if file is missing.
    Raises StorageIntegrityError if SHA-256 hash does not match expected_hash.
    """
    target_path = _resolve_storage_path(storage_key)

    if not target_path.is_file():
        raise StorageNotFoundError(f"Stored encrypted asset binary not found: {storage_key}")

    ciphertext = target_path.read_bytes()

    if expected_hash:
        actual_hash = hashlib.sha256(ciphertext).hexdigest()
        if not hmac.compare_digest(actual_hash, expected_hash):
            raise StorageIntegrityError(
                f"Asset integrity verification failed: expected hash {expected_hash}, got {actual_hash}."
            )

    return ciphertext


def delete_stored_file(storage_key: str) -> bool:
    """
    Safely delete an encrypted asset binary from disk.
    Returns True if deleted or already absent, False if removal encountered an error.
    """
    try:
        target_path = _resolve_storage_path(storage_key)
        if target_path.is_file():
            target_path.unlink()
        return True
    except (ValueError, OSError):
        return False
