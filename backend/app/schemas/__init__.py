"""Pydantic request and response schemas."""

from app.schemas.auth import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceRevokeRequest,
    DeviceSummary,
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

__all__ = [
    "DatabaseHealthResponse",
    "DeviceRegisterRequest",
    "DeviceResponse",
    "DeviceRevokeRequest",
    "DeviceSummary",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "QRPayload",
    "SessionCreateRequest",
    "SessionResponse",
    "SessionScanRequest",
    "SessionStatusResponse",
    "SessionVerifyRequest",
    "SystemInfoResponse",
]
