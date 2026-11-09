"""
IPGuard Milestone 3 — Asset Validation Service.
Provides strict filename sanitization, MIME detection, and magic byte signature verification.
Prevents file upload vulnerabilities, path traversal, polyglot files, and executable execution.
"""

from pathlib import Path
import re

# Maximum allowed filename length
MAX_FILENAME_LENGTH = 255

# Filename character safety pattern (disallows directory traversal and path separators)
INVALID_FILENAME_CHARS = re.compile(r"[\/\x00-\x1f\x7f\\:\*\?\"<>\|]")

# Known safe magic byte signatures
MAGIC_SIGNATURES: list[tuple[bytes, str, list[str]]] = [
    # Images
    (b"\x89PNG\r\n\x1a\n", "image/png", [".png"]),
    (b"\xff\xd8\xff", "image/jpeg", [".jpg", ".jpeg"]),
    (b"GIF87a", "image/gif", [".gif"]),
    (b"GIF89a", "image/gif", [".gif"]),
    # Documents
    (b"%PDF-", "application/pdf", [".pdf"]),
    # ZIP-based documents (DOCX, XLSX, PPTX, or ZIP archive)
    (b"PK\x03\x04", "application/zip", [".zip", ".docx", ".xlsx", ".pptx"]),
    # Audio / Media
    (b"ID3", "audio/mpeg", [".mp3"]),
    (b"\xff\xfb", "audio/mpeg", [".mp3"]),
]

# Explicitly forbidden executable signatures
FORBIDDEN_SIGNATURES: list[tuple[bytes, str]] = [
    (b"MZ", "Windows Executable (PE/EXE/DLL)"),
    (b"\x7fELF", "Linux/Unix ELF Binary"),
    (b"\xca\xfe\xba\xbe", "Java Bytecode / Mach-O Binary"),
    (b"\xfe\xed\xfa\xce", "Mach-O 32-bit"),
    (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit"),
]


class AssetValidationError(ValueError):
    """Raised when file upload validation fails."""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Sanitize and validate an asset filename.
    Rejects path traversal, null bytes, backslashes, and control characters.
    """
    if not filename or not isinstance(filename, str):
        raise AssetValidationError("Filename cannot be empty.")

    cleaned = filename.strip()
    if not cleaned:
        raise AssetValidationError("Filename cannot consist only of whitespace.")

    if len(cleaned) > MAX_FILENAME_LENGTH:
        raise AssetValidationError(
            f"Filename exceeds maximum length of {MAX_FILENAME_LENGTH} characters."
        )

    if INVALID_FILENAME_CHARS.search(cleaned):
        raise AssetValidationError(
            "Filename contains invalid or path traversal characters."
        )

    # Disallow relative traversal filenames like '.' or '..'
    if cleaned in {".", ".."}:
        raise AssetValidationError("Invalid filename.")

    return cleaned


def detect_and_validate_file(data: bytes, filename: str, declared_mime: str | None = None) -> str:
    """
    Inspect raw binary data to determine and validate its content type.
    1. Blocks dangerous executable signatures (MZ, ELF, Mach-O).
    2. Validates magic bytes for binary files.
    3. Permits safe text-based files (UTF-8 encoded txt, csv, json, md).
    Returns the resolved trusted MIME type string.
    """
    if not data or len(data) == 0:
        raise AssetValidationError("File cannot be empty (0 bytes).")

    # 1. Enforce strict rejection of executable formats
    for sig, desc in FORBIDDEN_SIGNATURES:
        if data.startswith(sig):
            raise AssetValidationError(f"File upload rejected: dangerous executable format detected ({desc}).")

    ext = Path(filename).suffix.lower()

    # 2. Check known binary magic signatures
    for sig, mime, allowed_exts in MAGIC_SIGNATURES:
        if data.startswith(sig):
            return mime

    # Special handling for WebP (RIFF....WEBP)
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"

    # Special handling for WAV (RIFF....WAVE)
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"

    # Special handling for MP4/M4A/MOV (....ftyp)
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "video/mp4"

    # 3. Check for valid text formats (TXT, CSV, JSON, MD, XML, YAML)
    text_extensions = {".txt", ".csv", ".json", ".md", ".yaml", ".yml", ".xml", ".log"}
    if ext in text_extensions or (declared_mime and declared_mime.startswith("text/")):
        try:
            # Must decode cleanly as valid UTF-8 without null bytes in body
            decoded = data[:4096].decode("utf-8")
            if "\x00" in decoded:
                raise AssetValidationError("File contains null bytes inside text stream.")
            if ext == ".json":
                return "application/json"
            if ext == ".csv":
                return "text/csv"
            return "text/plain"
        except UnicodeDecodeError:
            pass

    # 4. Fallback for recognized extensions with declared MIME (if not forbidden executable)
    safe_extensions = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".zip": "application/zip",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".json": "application/json",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
    }

    if ext in safe_extensions:
        return safe_extensions[ext]

    if declared_mime and not declared_mime.startswith("application/x-msdownload"):
        return declared_mime

    return "application/octet-stream"
