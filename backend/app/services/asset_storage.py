"""
IPGuard Milestone 3 — Asset Storage Service.
Manages atomic disk storage, retrieval, and deletion of XChaCha20-Poly1305 encrypted asset binaries.
Enforces strict storage key sanitization, SHA-256 ciphertext integrity verification, and directory isolation.
"""

import hashlib
import hmac
import os
from pathlib import Path
import stat
import uuid

from app.core.config import get_settings


class StorageIntegrityError(ValueError):
    """Raised when ciphertext on disk fails SHA-256 integrity verification."""
    pass


class StorageNotFoundError(FileNotFoundError):
    """Raised when an encrypted asset binary is not found on disk."""
    pass


class StoragePathError(ValueError):
    """Raised when a stored asset path resolves through a link or outside storage."""
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

    stored = False
    try:
        temp_path.write_bytes(ciphertext)
        temp_path.replace(target_path)
        stored = True
        # Hash the committed file, not the in-memory input, so the baseline
        # represents the exact bytes available to subsequent integrity checks.
        sha256_digest = hash_ciphertext_file(storage_key)
    except Exception:
        if stored:
            try:
                target_path.unlink()
            except OSError:
                pass
        raise
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


def hash_ciphertext_file(storage_key: str, chunk_size: int = 1024 * 1024) -> str:
    """Calculate a stored ciphertext's SHA-256 digest using bounded memory."""
    digest, _ = inspect_ciphertext_file(storage_key, chunk_size=chunk_size)
    return digest


def inspect_ciphertext_file(
    storage_key: str,
    chunk_size: int = 1024 * 1024,
    include_ciphertext: bool = False,
) -> tuple[str, bytes | None]:
    """Hash a stored ciphertext in chunks, optionally returning those same bytes.

    Download uses the optional byte capture so it decrypts exactly the content
    that was hashed, avoiding a second read and a check-to-use race.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")

    target_path = _resolve_integrity_storage_path(storage_key)
    digest = hashlib.sha256()
    ciphertext_chunks: list[bytes] | None = [] if include_ciphertext else None

    try:
        with _open_storage_file_without_reparse(target_path) as ciphertext_file:
            while chunk := ciphertext_file.read(chunk_size):
                digest.update(chunk)
                if ciphertext_chunks is not None:
                    ciphertext_chunks.append(chunk)
    except FileNotFoundError as exc:
        raise StorageNotFoundError(
            f"Stored encrypted asset binary not found: {storage_key}"
        ) from exc

    ciphertext = b"".join(ciphertext_chunks) if ciphertext_chunks is not None else None
    return digest.hexdigest(), ciphertext


def _resolve_integrity_storage_path(storage_key: str) -> Path:
    """Resolve a UUID asset key and enforce containment within the storage root."""
    candidate = _resolve_storage_path(storage_key)
    try:
        storage_root = get_settings().storage_directory.resolve(strict=True)
        if _is_reparse_point(candidate):
            raise StoragePathError(
                "Asset storage path must not be a symlink or reparse point."
            )
        resolved_candidate = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise StorageNotFoundError(
            f"Stored encrypted asset binary not found: {storage_key}"
        ) from exc
    except RuntimeError as exc:
        raise StoragePathError("Storage path contains a resolution loop.") from exc

    try:
        resolved_candidate.relative_to(storage_root)
    except ValueError as exc:
        raise StoragePathError("Resolved asset path is outside the storage directory.") from exc

    # The final open also uses no-follow semantics where the platform supports them.
    return candidate


def _is_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows reparse points without following the entry."""
    try:
        path_stat = path.lstat()
    except FileNotFoundError as exc:
        raise StorageNotFoundError(f"Stored encrypted asset binary not found: {path.name}") from exc

    if stat.S_ISLNK(path_stat.st_mode):
        return True

    attributes = getattr(path_stat, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if attributes & reparse_flag:
        return True

    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _open_storage_file_without_reparse(path: Path):
    """Open a regular stored file without following a final-component link."""
    if os.name == "nt":
        return _open_windows_file_without_reparse(path)

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise StoragePathError("Asset storage entry is not a regular file.")
        return os.fdopen(descriptor, "rb")
    except Exception:
        os.close(descriptor)
        raise


def _open_windows_file_without_reparse(path: Path):
    """Open via a handle that identifies the reparse entry instead of following it."""
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    get_file_info = kernel32.GetFileInformationByHandleEx
    get_file_info.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    get_file_info.restype = wintypes.BOOL

    generic_read = 0x80000000
    share_all = 0x00000001 | 0x00000002 | 0x00000004
    open_existing = 3
    open_reparse_point = 0x00200000
    sequential_scan = 0x08000000
    handle = create_file(
        str(path), generic_read, share_all, None, open_existing,
        open_reparse_point | sequential_scan, None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())

    info = FileAttributeTagInfo()
    try:
        # FileAttributeTagInfo is value 9 in FILE_INFO_BY_HANDLE_CLASS.
        if not get_file_info(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if info.FileAttributes & 0x400:
            raise StoragePathError("Asset storage path is a Windows reparse point.")

        descriptor = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_BINARY)
        handle = None
        return os.fdopen(descriptor, "rb")
    finally:
        if handle is not None:
            close_handle(handle)


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
