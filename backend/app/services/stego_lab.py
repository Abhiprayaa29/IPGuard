"""
IPGuard Steganography Lab Orchestration Service.

Coordinates canonical watermark payload encoding into Asset Vault PNGs (producing
XChaCha20-Poly1305 encrypted derived assets) and read-only watermark inspection
for both external PNG uploads and existing Asset Vault PNGs.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any
import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.asset import Asset
from app.services.assets import create_asset, download_asset, get_asset
from app.services.png_steganography import (
    FRAME_VERSION,
    PngCapacityInfo,
    PngSteganographyError,
    WatermarkInspectionResult,
    calculate_png_capacity,
    embed_png,
    inspect_png_bytes,
    load_signing_key,
)
from app.services.stego_payload import (
    SIGNATURE_ALGORITHM,
    WATERMARK_FORMAT,
    build_canonical_watermark_payload,
    parse_watermark_payload,
)


def _map_stego_error(exc: PngSteganographyError) -> AppError:
    key_unavailable = exc.code in {
        "SIGNING_KEY_UNAVAILABLE",
        "SIGNING_KEY_CONFIGURATION_INVALID",
    }
    unsupported_type = exc.code == "UNSUPPORTED_PNG_MODE"
    if key_unavailable:
        code = status.HTTP_503_SERVICE_UNAVAILABLE
        err_code = "steganography_signing_unavailable"
        msg = "Steganography signing or verification keys are not configured correctly."
    elif unsupported_type:
        code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        err_code = exc.code.lower()
        msg = str(exc)
    else:
        code = status.HTTP_400_BAD_REQUEST
        err_code = exc.code.lower()
        msg = str(exc)
    return AppError(status_code=code, code=err_code, message=msg)


def _build_inspect_response_dict(
    result: WatermarkInspectionResult,
    *,
    input_mode: str,
    expected_source_sha256: str | None = None,
    asset: Asset | None = None,
    actual_source_sha256: str | None = None,
) -> dict[str, Any]:
    """
    Assemble a safe, complete inspector response dictionary.
    Partial or unverified payload metadata is never exposed as valid data.
    """
    warnings = list(result.warnings)
    parsed_dict: dict[str, Any] | None = None
    is_canonical = False
    raw_preview: str | None = None

    # Only extract and expose payload metadata after checksum & signature succeed.
    if result.status == "VALID" and result.payload is not None:
        parsed_dict, is_canonical = parse_watermark_payload(result.payload)
        if parsed_dict is None:
            try:
                raw_preview = result.payload.decode("utf-8")
            except UnicodeDecodeError:
                raw_preview = f"<binary payload: {len(result.payload)} bytes>"

    format_name: str | None = None
    version: int | None = result.version
    watermark_id_str = str(result.watermark_id) if result.watermark_id else None
    asset_reference: str | None = str(result.source_asset_id) if result.source_asset_id else None
    derivative_asset_id_str = str(result.derivative_asset_id) if result.derivative_asset_id else None
    owner_reference: str | None = None
    created_at: str | None = None
    source_sha256: str | None = None
    signature_algorithm: str | None = result.signature_algorithm
    signing_key_id: str | None = result.signing_key_id
    custom_metadata: dict[str, Any] | None = None

    if result.status == "VALID":
        if is_canonical and parsed_dict is not None:
            format_name = str(parsed_dict.get("format") or WATERMARK_FORMAT)
            watermark_id_str = str(parsed_dict.get("watermark_id") or watermark_id_str)
            asset_reference = str(parsed_dict.get("asset_reference") or asset_reference)
            owner_reference = parsed_dict.get("owner_reference")
            created_at = parsed_dict.get("created_at")
            source_sha256 = parsed_dict.get("source_sha256")
            signature_algorithm = str(parsed_dict.get("signature_algorithm") or SIGNATURE_ALGORITHM)
            signing_key_id = str(parsed_dict.get("signing_key_id") or signing_key_id)
            if isinstance(parsed_dict.get("metadata"), dict):
                custom_metadata = parsed_dict["metadata"]
        elif parsed_dict is not None:
            # Backward-compatible Asset Vault legacy JSON metadata
            format_name = "IPGUARD_ASSET_VAULT_JSON"
            owner_reference = str(parsed_dict.get("owner_id")) if parsed_dict.get("owner_id") else None
            created_at = str(parsed_dict.get("timestamp")) if parsed_dict.get("timestamp") else None
            custom_metadata = {
                k: v
                for k, v in parsed_dict.items()
                if k not in {"owner_id", "timestamp"} and v is not None
            } or None
        else:
            format_name = "IPGUARD_RAW_PAYLOAD"

        # Lineage & digest cross-checks if context is available
        if asset is not None and asset.derivative_type == "PNG_LSB":
            if asset.id != result.derivative_asset_id:
                warnings.append("Embedded derivative UUID does not match this Asset Vault record ID.")
            if asset.source_asset_id and asset.source_asset_id != result.source_asset_id:
                warnings.append("Embedded source asset UUID does not match database parent lineage.")
            if asset.watermark_id and asset.watermark_id != result.watermark_id:
                warnings.append("Embedded watermark UUID does not match database metadata.")

        reference_digest = (
            expected_source_sha256.strip().lower()
            if expected_source_sha256 and expected_source_sha256.strip()
            else actual_source_sha256
        )
        source_digest_matches: bool | None = None
        if reference_digest and source_sha256:
            source_digest_matches = reference_digest == source_sha256.lower()
            if not source_digest_matches:
                warnings.append("Source image SHA-256 in watermark does not match the provided/parent source digest.")
    else:
        source_digest_matches = None

    return {
        "status": result.status,
        "watermark_detected": result.watermark_detected,
        "signature_valid": result.signature_valid,
        "framing_valid": result.framing_valid,
        "checksum_valid": result.checksum_valid,
        "format": format_name,
        "version": version,
        "watermark_id": watermark_id_str,
        "asset_reference": asset_reference,
        "derivative_asset_id": derivative_asset_id_str,
        "owner_reference": owner_reference,
        "created_at": created_at,
        "source_sha256": source_sha256,
        "signature_algorithm": signature_algorithm,
        "signing_key_id": signing_key_id,
        "inspected_image_sha256": result.inspected_image_sha256,
        "source_digest_matches": source_digest_matches,
        "metadata": custom_metadata,
        "raw_payload_preview": raw_preview,
        "verified_at": datetime.now(timezone.utc),
        "warnings": warnings,
        "input_mode": input_mode,
    }


def get_asset_png_capacity(
    db: Session,
    *,
    asset_id: uuid.UUID,
    device_id: str,
) -> tuple[Asset, PngCapacityInfo]:
    """Decrypt owned PNG asset in memory and compute its LSB capacity."""
    asset = get_asset(db, asset_id, device_id)
    if asset.content_type != "image/png":
        raise AppError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="png_required",
            message="PNG LSB steganography requires an image/png asset.",
        )

    _, plaintext = download_asset(db, asset_id, device_id)
    settings = get_settings()
    try:
        cap = calculate_png_capacity(plaintext, settings=settings)
    except PngSteganographyError as exc:
        raise _map_stego_error(exc) from exc
    return asset, cap


def encode_canonical_asset_watermark(
    db: Session,
    *,
    source_asset_id: uuid.UUID,
    device_id: str,
    copyright_notice: str | None = None,
    license_info: str | None = None,
    note: str | None = None,
) -> tuple[Asset, uuid.UUID, dict[str, Any]]:
    """
    Create a canonical signed IPGUARD_WATERMARK v1 payload, embed it via RGB LSB
    into an owned PNG asset, and persist the result as an XChaCha20-Poly1305 encrypted
    derived asset while leaving the original asset unchanged.
    """
    source = get_asset(db, source_asset_id, device_id)
    if source.content_type != "image/png":
        raise AppError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="png_required",
            message="PNG LSB watermarking requires a PNG source asset.",
        )

    _, source_png = download_asset(db, source_asset_id, device_id)
    settings = get_settings()
    try:
        cap = calculate_png_capacity(source_png, settings=settings)
        _, active_key_id, _ = load_signing_key(settings)
    except PngSteganographyError as exc:
        raise _map_stego_error(exc) from exc

    watermark_id = uuid.uuid4()
    derivative_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)

    payload_bytes = build_canonical_watermark_payload(
        watermark_id=watermark_id,
        source_asset_id=source.id,
        device_id=device_id,
        source_sha256=cap.source_sha256,
        signing_key_id=active_key_id,
        created_at=created_at,
        copyright_notice=copyright_notice,
        license_info=license_info,
        note=note,
    )

    if len(payload_bytes) > cap.max_payload_bytes:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="payload_exceeds_capacity",
            message=(
                f"Watermark payload ({len(payload_bytes)} bytes) exceeds carrier image "
                f"capacity ({cap.max_payload_bytes} usable bytes available)."
            ),
        )

    try:
        derivative_png = embed_png(
            source_png,
            payload_bytes,
            source_asset_id=source.id,
            derivative_asset_id=derivative_id,
            watermark_id=watermark_id,
            settings=settings,
        )
    except PngSteganographyError as exc:
        raise _map_stego_error(exc) from exc

    stem = Path(source.original_filename).stem[:230] or "asset"
    derivative = create_asset(
        db=db,
        device_id=device_id,
        filename=f"{stem}.watermarked.png",
        content_type="image/png",
        data=derivative_png,
        asset_id=derivative_id,
        source_asset_id=source.id,
        derivative_type="PNG_LSB",
        watermark_id=watermark_id,
        stego_format_version=FRAME_VERSION,
        audit_event_type="ASSET_STEGO_EMBEDDED",
        audit_payload={
            "source_asset_id": str(source.id),
            "derivative_asset_id": str(derivative_id),
            "watermark_id": str(watermark_id),
            "format_version": FRAME_VERSION,
            "result": "SUCCESS",
        },
    )

    parsed_payload, _ = parse_watermark_payload(payload_bytes)
    return derivative, watermark_id, parsed_payload or {}


def inspect_external_png(
    png_bytes: bytes,
    *,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """
    Read-only inspection of an externally uploaded PNG.
    Never saves files to storage or database.
    """
    settings = get_settings()
    if not png_bytes:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="empty_file",
            message="Uploaded PNG file cannot be empty.",
        )

    try:
        result = inspect_png_bytes(png_bytes, settings=settings)
    except PngSteganographyError as exc:
        raise _map_stego_error(exc) from exc

    return _build_inspect_response_dict(
        result,
        input_mode="EXTERNAL_UPLOAD",
        expected_source_sha256=expected_source_sha256,
    )


def inspect_vault_asset_png(
    db: Session,
    *,
    asset_id: uuid.UUID,
    device_id: str,
    expected_source_sha256: str | None = None,
) -> tuple[Asset, dict[str, Any]]:
    """
    Read-only inspection of a PNG stored in Asset Vault.
    Decrypts in-memory and never modifies the stored asset.
    """
    asset = get_asset(db, asset_id, device_id)
    if asset.content_type != "image/png":
        raise AppError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="png_required",
            message="Watermark inspection requires an image/png asset.",
        )

    _, plaintext = download_asset(db, asset_id, device_id)

    actual_source_sha256: str | None = None
    if asset.source_asset_id is not None and not expected_source_sha256:
        try:
            _, parent_plaintext = download_asset(db, asset.source_asset_id, device_id)
            actual_source_sha256 = hashlib.sha256(parent_plaintext).hexdigest()
        except AppError:
            actual_source_sha256 = None

    settings = get_settings()
    try:
        result = inspect_png_bytes(plaintext, settings=settings)
    except PngSteganographyError as exc:
        raise _map_stego_error(exc) from exc

    response = _build_inspect_response_dict(
        result,
        input_mode="ASSET_VAULT",
        expected_source_sha256=expected_source_sha256,
        asset=asset,
        actual_source_sha256=actual_source_sha256,
    )
    return asset, response
