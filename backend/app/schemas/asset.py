from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: str | None = None
    size_bytes: int
    sha256_hash: str
    encryption_version: str = "v1"
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
