from datetime import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: str | None = None
    size_bytes: int
    sha256_hash: str
    encryption_version: str = "v1"
    source_asset_id: uuid.UUID | None = None
    derivative_type: str | None = None
    watermark_id: uuid.UUID | None = None
    stego_format_version: int | None = None
    created_at: datetime
    updated_at: datetime
    encryption_status: str = Field(
        default="ENCRYPTED_XCHACHA20_POLY1305",
        description="Active encryption status and cipher identifier.",
    )


class AssetRenameRequest(BaseModel):
    filename: str = Field(
        min_length=1,
        max_length=255,
        description="New sanitized filename for the digital asset.",
    )


class AssetIntegrityResponse(BaseModel):
    asset_id: uuid.UUID
    integrity_status: Literal["PENDING", "VERIFIED", "MISMATCH", "MISSING", "ERROR"]
    last_checked_at: datetime | None = None


class StegoEmbedRequest(BaseModel):
    payload_b64: str = Field(max_length=5_592_408, description="Watermark payload, Base64 encoded (maximum 4 MiB).")


class StegoEmbedResponse(BaseModel):
    derivative: AssetResponse
    watermark_id: uuid.UUID
    format_version: int


class WatermarkVerifyResponse(BaseModel):
    verified: bool
    status: str
    watermark_id: uuid.UUID | None = None
    source_asset_id: uuid.UUID | None = None
    derivative_asset_id: uuid.UUID | None = None
    format_version: int | None = None


class WatermarkExtractResponse(WatermarkVerifyResponse):
    payload_b64: str
