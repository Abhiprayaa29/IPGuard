"""Pydantic request and response schemas."""

from app.schemas.asset import (
    AssetRenameRequest,
    AssetResponse,
)
from app.schemas.auth import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceRevokeRequest,
    DeviceStatusCheckResponse,
    DeviceSummary,
    DeviceUnregisterRequest,
    QRPayload,
    SessionCreateRequest,
    SessionResponse,
    SessionScanRequest,
    SessionStatusResponse,
    SessionVerifyRequest,
)
from app.schemas.common import (
    DatabaseHealthResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    SystemInfoResponse,
)
from app.schemas.note import (
    NoteCreateRequest,
    NoteResponse,
    NoteUpdateRequest,
)

__all__ = [
    "AssetRenameRequest",
    "AssetResponse",
    "DatabaseHealthResponse",
    "DeviceRegisterRequest",
    "DeviceResponse",
    "DeviceRevokeRequest",
    "DeviceStatusCheckResponse",
    "DeviceSummary",
    "DeviceUnregisterRequest",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "NoteCreateRequest",
    "NoteResponse",
    "NoteUpdateRequest",
    "QRPayload",
    "SessionCreateRequest",
    "SessionResponse",
    "SessionScanRequest",
    "SessionStatusResponse",
    "SessionVerifyRequest",
    "SystemInfoResponse",
]
