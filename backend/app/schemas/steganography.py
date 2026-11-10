from datetime import datetime
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field

from app.schemas.asset import AssetResponse


class StegoEncodeRequest(BaseModel):
    copyright: str | None = Field(
        default=None,
        max_length=200,
        description="Optional copyright or ownership attribution text.",
    )
    license: str | None = Field(
        default=None,
        max_length=120,
        description="Optional license identifier (e.g., Proprietary, CC-BY-NC).",
    )
    note: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional non-sensitive watermark description or note.",
    )


class StegoEncodeResponse(BaseModel):
    derivative: AssetResponse
    watermark_id: uuid.UUID
    format_version: int
    embedded_payload: dict[str, Any]


class StegoCapacityResponse(BaseModel):
    asset_id: uuid.UUID
    filename: str
    width: int
    height: int
    mode: str
    total_pixels: int
    total_capacity_bytes: int
    header_overhead_bytes: int
    max_payload_bytes: int
    source_sha256: str


InspectorStatus = Literal[
    "VALID",
    "INVALID_SIGNATURE",
    "CORRUPTED",
    "NO_WATERMARK",
    "UNKNOWN_SIGNER",
    "UNSUPPORTED_VERSION",
]


class WatermarkInspectResponse(BaseModel):
    status: InspectorStatus
    watermark_detected: bool
    signature_valid: bool
    framing_valid: bool
    checksum_valid: bool
    format: str | None = None
    version: int | None = None
    watermark_id: str | None = None
    asset_reference: str | None = None
    derivative_asset_id: str | None = None
    owner_reference: str | None = None
    created_at: str | None = None
    source_sha256: str | None = None
    signature_algorithm: str | None = None
    signing_key_id: str | None = None
    inspected_image_sha256: str
    source_digest_matches: bool | None = None
    metadata: dict[str, Any] | None = None
    raw_payload_preview: str | None = None
    verified_at: datetime
    warnings: list[str] = Field(default_factory=list)
    input_mode: Literal["EXTERNAL_UPLOAD", "ASSET_VAULT"]


class AssetInspectRequest(BaseModel):
    expected_source_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="Optional expected SHA-256 hex digest of the original image.",
    )
