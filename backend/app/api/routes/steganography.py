"""
IPGuard Milestone 4 — Steganography Lab API Routes.

Provides M2-authenticated endpoints for:
- External PNG watermark inspection (read-only, zero persistence)
- Existing Asset Vault PNG watermark inspection (read-only)
- Canonical signed watermark encoding into Asset Vault PNGs (creating XChaCha20-Poly1305 encrypted derived assets)
- PNG LSB carrier capacity inspection
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.auth import Device
from app.schemas.asset import AssetResponse
from app.schemas.common import ErrorResponse
from app.schemas.steganography import (
    AssetInspectRequest,
    StegoCapacityResponse,
    StegoEncodeRequest,
    StegoEncodeResponse,
    WatermarkInspectResponse,
)
from app.services import stego_lab

router = APIRouter()

STANDARD_ERRORS = {
    400: {"model": ErrorResponse, "description": "Bad Request. Invalid PNG, capacity exceeded, or bad payload."},
    401: {"model": ErrorResponse, "description": "Unauthorized. Missing, invalid, or expired session token."},
    403: {"model": ErrorResponse, "description": "Forbidden. Authenticator device is revoked or unregistered."},
    415: {"model": ErrorResponse, "description": "Unsupported Media Type. Only 8-bit RGB/RGBA PNGs are supported."},
}


@router.post(
    "/inspect",
    response_model=WatermarkInspectResponse,
    summary="Inspect an external PNG image for an IPGuard LSB watermark (read-only)",
    responses=STANDARD_ERRORS,
)
def inspect_external_png_upload(
    file: UploadFile = File(...),
    expected_source_sha256: str | None = Form(default=None),
    _device: Device = Depends(get_current_authenticated_device),
) -> WatermarkInspectResponse:
    """
    Read-only inspection of an externally uploaded PNG file.
    Does not save the uploaded file to Asset Vault or disk, and clears memory immediately.
    """
    settings = get_settings()
    max_bytes = min(settings.stego_max_image_bytes, 50 * 1024 * 1024)
    try:
        raw_bytes = file.file.read(max_bytes + 1)
    finally:
        file.file.close()

    if len(raw_bytes) > max_bytes:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="image_too_large",
            message="Uploaded PNG exceeds the maximum allowed size limit.",
        )

    result = stego_lab.inspect_external_png(
        raw_bytes,
        expected_source_sha256=expected_source_sha256,
    )
    return WatermarkInspectResponse(**result)


@router.get(
    "/assets/{asset_id}/capacity",
    response_model=StegoCapacityResponse,
    summary="Calculate PNG LSB embedding capacity for an owned Asset Vault PNG",
    responses=STANDARD_ERRORS | {404: {"model": ErrorResponse, "description": "Asset not found."}},
)
def get_asset_stego_capacity(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> StegoCapacityResponse:
    asset, cap = stego_lab.get_asset_png_capacity(
        db,
        asset_id=asset_id,
        device_id=device.device_id,
    )
    return StegoCapacityResponse(
        asset_id=asset.id,
        filename=asset.original_filename,
        width=cap.width,
        height=cap.height,
        mode=cap.mode,
        total_pixels=cap.total_pixels,
        total_capacity_bytes=cap.total_capacity_bytes,
        header_overhead_bytes=cap.header_overhead_bytes,
        max_payload_bytes=cap.max_payload_bytes,
        source_sha256=cap.source_sha256,
    )


@router.post(
    "/assets/{asset_id}/encode",
    response_model=StegoEncodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Encode a signed canonical IPGuard watermark into an owned PNG asset",
    responses=STANDARD_ERRORS | {404: {"model": ErrorResponse, "description": "Asset not found."}},
)
def encode_asset_watermark(
    asset_id: uuid.UUID,
    payload: StegoEncodeRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> StegoEncodeResponse:
    derivative, watermark_id, embedded_payload = stego_lab.encode_canonical_asset_watermark(
        db,
        source_asset_id=asset_id,
        device_id=device.device_id,
        copyright_notice=payload.copyright,
        license_info=payload.license,
        note=payload.note,
    )
    return StegoEncodeResponse(
        derivative=AssetResponse.model_validate(derivative),
        watermark_id=watermark_id,
        format_version=derivative.stego_format_version or 1,
        embedded_payload=embedded_payload,
    )


@router.post(
    "/assets/{asset_id}/inspect",
    response_model=WatermarkInspectResponse,
    summary="Inspect an existing Asset Vault PNG for an IPGuard watermark (read-only)",
    responses=STANDARD_ERRORS | {404: {"model": ErrorResponse, "description": "Asset not found."}},
)
def inspect_vault_asset(
    asset_id: uuid.UUID,
    body: AssetInspectRequest | None = None,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> WatermarkInspectResponse:
    _, result = stego_lab.inspect_vault_asset_png(
        db,
        asset_id=asset_id,
        device_id=device.device_id,
        expected_source_sha256=body.expected_source_sha256 if body else None,
    )
    return WatermarkInspectResponse(**result)
