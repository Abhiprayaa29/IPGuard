"""
Canonical IPGuard Watermark Payload Serialization & Parsing (M4 Steganography).

Note on Security & Privacy:
LSB watermarking hides structured metadata inside PNG pixel least-significant bits,
which is obfuscation / steganographic embedding—NOT encryption. Anyone who inspects
the public LSB packet format can extract the embedded payload bytes. Therefore,
never embed master keys, derived keys, private signing keys, session tokens,
passwords, or unnecessary PII inside the watermark payload.
"""

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any
import uuid


WATERMARK_FORMAT = "IPGUARD_WATERMARK"
WATERMARK_PAYLOAD_VERSION = 1
SIGNATURE_ALGORITHM = "Ed25519"
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def derive_opaque_owner_reference(device_id: str) -> str:
    """Derive a deterministic, non-PII opaque owner identifier from a device ID."""
    digest = hashlib.sha256(f"IPGUARD-OWNER-REF-V1|{device_id}".encode("utf-8")).hexdigest()
    return f"owner-{digest[:20]}"


def sanitize_metadata_text(value: str | None, *, max_length: int) -> str | None:
    """Strip control characters and trim whitespace from optional metadata fields."""
    if value is None:
        return None
    cleaned = _CONTROL_CHARS_RE.sub("", value).strip()
    if not cleaned:
        return None
    return cleaned[:max_length]


def build_canonical_watermark_payload(
    *,
    watermark_id: uuid.UUID,
    source_asset_id: uuid.UUID,
    device_id: str,
    source_sha256: str,
    signing_key_id: str,
    created_at: datetime | None = None,
    copyright_notice: str | None = None,
    license_info: str | None = None,
    note: str | None = None,
) -> bytes:
    """
    Build a deterministically serialized canonical JSON watermark payload.
    All keys are sorted and whitespace-free so signatures are reproducible.
    """
    ts = created_at or datetime.now(timezone.utc)
    iso_ts = ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload_dict: dict[str, Any] = {
        "format": WATERMARK_FORMAT,
        "version": WATERMARK_PAYLOAD_VERSION,
        "watermark_id": str(watermark_id),
        "asset_reference": str(source_asset_id),
        "owner_reference": derive_opaque_owner_reference(device_id),
        "created_at": iso_ts,
        "source_sha256": source_sha256,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "signing_key_id": signing_key_id,
    }

    extra_meta: dict[str, str] = {}
    clean_copyright = sanitize_metadata_text(copyright_notice, max_length=200)
    clean_license = sanitize_metadata_text(license_info, max_length=120)
    clean_note = sanitize_metadata_text(note, max_length=1000)

    if clean_copyright:
        extra_meta["copyright"] = clean_copyright
    if clean_license:
        extra_meta["license"] = clean_license
    if clean_note:
        extra_meta["note"] = clean_note

    if extra_meta:
        payload_dict["metadata"] = extra_meta

    return json.dumps(
        payload_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def parse_watermark_payload(payload_bytes: bytes) -> tuple[dict[str, Any] | None, bool]:
    """
    Attempt to parse extracted payload bytes as JSON.
    Returns (parsed_dict_or_none, is_canonical_ipguard_format).
    """
    if not payload_bytes:
        return None, False
    try:
        decoded = payload_bytes.decode("utf-8")
        obj = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, False

    if not isinstance(obj, dict):
        return None, False

    is_canonical = (
        obj.get("format") == WATERMARK_FORMAT
        and isinstance(obj.get("version"), int)
        and isinstance(obj.get("watermark_id"), str)
        and isinstance(obj.get("asset_reference"), str)
        and isinstance(obj.get("owner_reference"), str)
    )
    return obj, is_canonical
