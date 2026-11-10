"""
IPGuard Milestone 3 — Asset Vault API Routes.
Provides hardware-authenticated endpoints for uploading, listing, downloading,
renaming, and deleting XChaCha20-Poly1305 encrypted digital assets.
"""

import base64
import binascii
import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.db.session import get_db
from app.models.auth import Device
from app.schemas.asset import (
    AssetIntegrityResponse,
    AssetRenameRequest,
    AssetResponse,
    StegoEmbedRequest,
    StegoEmbedResponse,
    WatermarkExtractResponse,
    WatermarkVerifyResponse,
)
from app.schemas.steganography import (
    AssetInspectRequest,
    StegoEncodeRequest,
    StegoEncodeResponse,
    WatermarkInspectResponse,
)
from app.schemas.common import ErrorResponse
from app.services import assets as assets_service
from app.services import stego_lab
from app.services import steganography as stego_service
from app.core.config import get_settings
from app.core.errors import AppError

router = APIRouter()

STANDARD_ERRORS = {
    400: {"model": ErrorResponse, "description": "Bad Request. File size exceeded, empty file, or invalid filename."},
    401: {"model": ErrorResponse, "description": "Unauthorized. Missing, invalid, or expired session token."},
    403: {"model": ErrorResponse, "description": "Forbidden. Authenticator device is revoked or unregistered."},
}

NOT_FOUND_ERRORS = {
    **STANDARD_ERRORS,
    404: {"model": ErrorResponse, "description": "Asset not found or access denied for this device."},
    409: {"model": ErrorResponse, "description": "Conflict. Cryptographic integrity check or decryption failed."},
}

DOWNLOAD_ERRORS = {
    **NOT_FOUND_ERRORS,
    503: {"model": ErrorResponse, "description": "Asset integrity verification is temporarily unavailable."},
}


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and encrypt a digital asset",
    responses=STANDARD_ERRORS,
)
def upload_asset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> AssetResponse:
    """
    Encrypt and store a digital asset.
    Uses true XChaCha20-Poly1305 AEAD with per-device HKDF key derivation.
    Ciphertext is stored on disk and metadata is persisted in PostgreSQL.
    """
    data = file.file.read()
    raw_filename = file.filename or ""

    asset = assets_service.create_asset(
        db=db,
        device_id=device.device_id,
        filename=raw_filename,
        content_type=file.content_type,
        data=data,
    )
    return AssetResponse.model_validate(asset)


@router.get(
    "",
    response_model=list[AssetResponse],
    summary="List all digital assets owned by authenticated device",
    responses=STANDARD_ERRORS,
)
def list_all_assets(
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> list[AssetResponse]:
    """Retrieve metadata for all digital assets owned by the calling device."""
    assets = assets_service.list_assets(db=db, device_id=device.device_id)
    return [AssetResponse.model_validate(a) for a in assets]


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Get details of a digital asset",
    responses=NOT_FOUND_ERRORS,
)
def get_asset_detail(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> AssetResponse:
    """Retrieve metadata for a specific asset owned by the calling device."""
    asset = assets_service.get_asset(db=db, asset_id=asset_id, device_id=device.device_id)
    return AssetResponse.model_validate(asset)


@router.get(
    "/{asset_id}/integrity",
    response_model=AssetIntegrityResponse,
    summary="Get the latest integrity status of an asset",
    responses=STANDARD_ERRORS | {
        404: {"model": ErrorResponse, "description": "Asset not found or access denied for this device."}
    },
)
def get_asset_integrity_status(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> AssetIntegrityResponse:
    """Return integrity metadata only for an asset owned by the authenticated device."""
    asset = assets_service.get_asset(db=db, asset_id=asset_id, device_id=device.device_id)
    return AssetIntegrityResponse(
        asset_id=asset.id,
        integrity_status=asset.integrity_status,
        last_checked_at=asset.last_checked_at,
    )


@router.get(
    "/{asset_id}/download",
    summary="Download and decrypt a digital asset",
    responses=DOWNLOAD_ERRORS,
)
def download_asset_file(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> Response:
    """
    Verify SHA-256 integrity, decrypt XChaCha20-Poly1305 ciphertext in memory,
    and return the original binary file.
    """
    asset, plaintext = assets_service.download_asset(
        db=db,
        asset_id=asset_id,
        device_id=device.device_id,
    )

    mime_type = asset.content_type or "application/octet-stream"
    safe_filename = asset.original_filename.replace('"', '\\"')

    return Response(
        content=plaintext,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Content-Length": str(len(plaintext)),
            "X-Asset-ID": str(asset.id),
            "X-Encryption-Version": asset.encryption_version,
        },
    )


@router.post(
    "/{asset_id}/steganography/embed",
    response_model=StegoEmbedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Embed a signed PNG LSB watermark as a derivative asset",
    responses=DOWNLOAD_ERRORS | {415: {"model": ErrorResponse, "description": "Source asset must be a PNG."}},
)
def embed_png_watermark(
    asset_id: uuid.UUID,
    payload: StegoEmbedRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> StegoEmbedResponse:
    try:
        payload_bytes = base64.b64decode(payload.payload_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_payload_encoding",
            message="Watermark payload must be valid Base64.",
        ) from exc
    if len(payload_bytes) > get_settings().stego_max_payload_bytes:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="payload_too_large",
            message="Watermark payload exceeds the configured limit.",
        )

    derivative, watermark_id = stego_service.embed_asset_watermark(
        db,
        source_asset_id=asset_id,
        device_id=device.device_id,
        payload=payload_bytes,
    )
    return StegoEmbedResponse(
        derivative=AssetResponse.model_validate(derivative),
        watermark_id=watermark_id,
        format_version=derivative.stego_format_version or 1,
    )


@router.post(
    "/{asset_id}/steganography/verify",
    response_model=WatermarkVerifyResponse,
    summary="Verify a PNG LSB watermark and its asset lineage",
    responses=DOWNLOAD_ERRORS,
)
def verify_png_watermark(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> WatermarkVerifyResponse:
    _, result = stego_service.verify_asset_watermark(
        db,
        asset_id=asset_id,
        device_id=device.device_id,
    )
    return WatermarkVerifyResponse(
        verified=result.verified,
        status=result.status,
        watermark_id=result.watermark_id,
        source_asset_id=result.source_asset_id,
        derivative_asset_id=result.derivative_asset_id,
        format_version=result.format_version,
    )


@router.post(
    "/{asset_id}/steganography/extract",
    response_model=WatermarkExtractResponse,
    summary="Extract a payload only after watermark verification",
    responses=DOWNLOAD_ERRORS | {409: {"model": ErrorResponse, "description": "Watermark could not be verified."}},
)
def extract_png_watermark(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> WatermarkExtractResponse:
    _, result = stego_service.extract_asset_watermark(
        db,
        asset_id=asset_id,
        device_id=device.device_id,
    )
    assert result.payload is not None
    return WatermarkExtractResponse(
        verified=True,
        status=result.status,
        watermark_id=result.watermark_id,
        source_asset_id=result.source_asset_id,
        derivative_asset_id=result.derivative_asset_id,
        format_version=result.format_version,
        payload_b64=base64.b64encode(result.payload).decode("ascii"),
    )


@router.post(
    "/{asset_id}/watermark",
    response_model=StegoEncodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Encode a signed canonical IPGuard watermark into an owned PNG asset",
    responses=DOWNLOAD_ERRORS | {415: {"model": ErrorResponse, "description": "Source asset must be a PNG."}},
)
def watermark_asset(
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
    "/{asset_id}/watermark/inspect",
    response_model=WatermarkInspectResponse,
    summary="Inspect an existing Asset Vault PNG for an IPGuard watermark (read-only)",
    responses=DOWNLOAD_ERRORS | {415: {"model": ErrorResponse, "description": "Asset must be a PNG."}},
)
def inspect_asset_watermark(
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


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Rename a digital asset",
    responses=NOT_FOUND_ERRORS,
)
def rename_asset_file(
    asset_id: uuid.UUID,
    payload: AssetRenameRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> AssetResponse:
    """Rename a digital asset without altering its encrypted binary file."""
    asset = assets_service.rename_asset(
        db=db,
        asset_id=asset_id,
        device_id=device.device_id,
        new_filename=payload.filename,
    )
    return AssetResponse.model_validate(asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a digital asset and its encrypted binary",
    responses=NOT_FOUND_ERRORS,
)
def delete_asset_file(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_authenticated_device),
) -> Response:
    """Delete asset metadata from database and unlink its ciphertext from disk."""
    assets_service.delete_asset(db=db, asset_id=asset_id, device_id=device.device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
