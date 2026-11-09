"""
IPGuard Milestone 3 — Asset Vault API Routes.
Provides hardware-authenticated endpoints for uploading, listing, downloading,
renaming, and deleting XChaCha20-Poly1305 encrypted digital assets.
"""

import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.db.session import get_db
from app.models.auth import Device
from app.schemas.asset import AssetRenameRequest, AssetResponse
from app.schemas.common import ErrorResponse
from app.services import assets as assets_service

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
    "/{asset_id}/download",
    summary="Download and decrypt a digital asset",
    responses=NOT_FOUND_ERRORS,
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
