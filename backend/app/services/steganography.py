"""Asset Vault orchestration for signed PNG LSB watermarks."""

from pathlib import Path
import uuid

from fastapi import status
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.asset import Asset
from app.services.audit_chain import append_audit_event
from app.services.assets import create_asset, download_asset, get_asset
from app.services.png_steganography import (
    FRAME_VERSION,
    PngSteganographyError,
    WatermarkVerification,
    embed_png,
    verify_png_watermark,
)


def _record_verification(
    db: Session,
    *,
    asset: Asset,
    device_id: str,
    result: WatermarkVerification,
    operation: str,
) -> None:
    """Write only non-sensitive operation metadata in an isolated transaction."""
    event_type = "STEGO_WATERMARK_VERIFIED" if result.verified else "STEGO_WATERMARK_REJECTED"
    safe_payload = {
        "operation": operation,
        "verification_status": result.status,
        "format_version": result.format_version,
        "source_asset_id": str(asset.source_asset_id) if asset.source_asset_id else None,
        "derivative_asset_id": str(asset.id),
        "watermark_id": str(result.watermark_id) if result.watermark_id else None,
    }
    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    try:
        with factory() as audit_db:
            with audit_db.begin():
                append_audit_event(
                    audit_db,
                    chain_id=device_id,
                    actor_type="DEVICE",
                    actor_device_id=device_id,
                    event_type=event_type,
                    resource_type="asset",
                    resource_id=str(asset.id),
                    result="VERIFIED" if result.verified else result.status[:32],
                    payload=safe_payload,
                )
    except Exception as exc:
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="audit_unavailable",
            message="Watermark verification could not be recorded.",
        ) from exc


def _record_embed_failure(db: Session, *, asset: Asset, device_id: str, error_code: str) -> None:
    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    try:
        with factory() as audit_db:
            with audit_db.begin():
                append_audit_event(
                    audit_db,
                    chain_id=device_id,
                    actor_type="DEVICE",
                    actor_device_id=device_id,
                    event_type="ASSET_STEGO_EMBED_FAILED",
                    resource_type="asset",
                    resource_id=str(asset.id),
                    result="FAILED",
                    payload={
                        "operation": "EMBED",
                        "result": "FAILED",
                        "error_code": error_code[:64],
                        "source_asset_id": str(asset.id),
                    },
                )
    except Exception as exc:
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="audit_unavailable",
            message="Watermark embedding failure could not be recorded.",
        ) from exc


def embed_asset_watermark(
    db: Session,
    *,
    source_asset_id: uuid.UUID,
    device_id: str,
    payload: bytes,
) -> tuple[Asset, uuid.UUID]:
    """Verify/decrypt an owned source, embed a signed frame, and persist a derivative."""
    source = get_asset(db, source_asset_id, device_id)
    if source.content_type != "image/png":
        _record_embed_failure(db, asset=source, device_id=device_id, error_code="PNG_REQUIRED")
        raise AppError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="png_required",
            message="PNG LSB watermarking requires a PNG source asset.",
        )

    try:
        _, source_png = download_asset(db, source_asset_id, device_id)
    except AppError:
        raise

    derivative_id = uuid.uuid4()
    watermark_id = uuid.uuid4()
    settings = get_settings()
    try:
        derivative_png = embed_png(
            source_png,
            payload,
            source_asset_id=source_asset_id,
            derivative_asset_id=derivative_id,
            watermark_id=watermark_id,
            settings=settings,
        )
    except PngSteganographyError as exc:
        _record_embed_failure(db, asset=source, device_id=device_id, error_code=exc.code)
        key_unavailable = exc.code in {
            "SIGNING_KEY_UNAVAILABLE",
            "SIGNING_KEY_CONFIGURATION_INVALID",
        }
        raise AppError(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
                if key_unavailable
                else status.HTTP_400_BAD_REQUEST
            ),
            code="steganography_signing_unavailable" if key_unavailable else exc.code.lower(),
            message=(
                "Steganography signing is not configured correctly."
                if key_unavailable
                else str(exc)
            ),
        ) from exc

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
    return derivative, watermark_id


def verify_asset_watermark(
    db: Session,
    *,
    asset_id: uuid.UUID,
    device_id: str,
    operation: str = "VERIFY",
) -> tuple[Asset, WatermarkVerification]:
    """Verify frame signature and bind embedded IDs to database asset lineage."""
    asset = get_asset(db, asset_id, device_id)
    if asset.derivative_type != "PNG_LSB" or asset.source_asset_id is None:
        result = WatermarkVerification(False, "NOT_STEGO_DERIVATIVE")
        _record_verification(db, asset=asset, device_id=device_id, result=result, operation=operation)
        return asset, result

    _, image_bytes = download_asset(db, asset_id, device_id)
    result = verify_png_watermark(
        image_bytes,
        expected_source_asset_id=asset.source_asset_id,
        expected_derivative_asset_id=asset.id,
        expected_watermark_id=asset.watermark_id,
        settings=get_settings(),
    )
    _record_verification(db, asset=asset, device_id=device_id, result=result, operation=operation)
    return asset, result


def extract_asset_watermark(
    db: Session,
    *,
    asset_id: uuid.UUID,
    device_id: str,
) -> tuple[Asset, WatermarkVerification]:
    """Return payload only after a valid signature and successful audit append."""
    asset, result = verify_asset_watermark(
        db,
        asset_id=asset_id,
        device_id=device_id,
        operation="EXTRACT",
    )
    if not result.verified or result.payload is None:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="watermark_verification_failed",
            message="Watermark framing or signature verification failed.",
        )

    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    try:
        with factory() as audit_db:
            with audit_db.begin():
                append_audit_event(
                    audit_db,
                    chain_id=device_id,
                    actor_type="DEVICE",
                    actor_device_id=device_id,
                    event_type="STEGO_PAYLOAD_EXTRACTED",
                    resource_type="asset",
                    resource_id=str(asset.id),
                    result="SUCCESS",
                    payload={
                        "source_asset_id": str(asset.source_asset_id),
                        "derivative_asset_id": str(asset.id),
                        "watermark_id": str(result.watermark_id),
                        "format_version": result.format_version,
                    },
                )
    except Exception as exc:
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="audit_unavailable",
            message="Payload extraction could not be recorded.",
        ) from exc
    return asset, result
