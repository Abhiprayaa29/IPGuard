from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str = Field(description="Unique device identifier")
    device_name: str = Field(description="User-friendly name of the device")
    model: str = Field(description="Hardware device model")
    android_version: str = Field(description="Android OS version")
    public_key_fingerprint: str = Field(description="SHA-256 fingerprint of the device public key")
    security_level: str = Field(description="Keymaster / KeyMint hardware security level")


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: str
    device_name: str
    model: str
    android_version: str
    public_key_fingerprint: str
    security_level: str
    status: str
    enrolled_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class SessionCreateRequest(BaseModel):
    session_type: Literal["AUTHENTICATION", "ENROLLMENT"] = Field(
        default="AUTHENTICATION",
        description="Type of session: AUTHENTICATION for sign-in or ENROLLMENT for new device binding",
    )
    origin: str | None = Field(
        default=None,
        description="Explicit web origin if different from HTTP request headers",
    )


class QRPayload(BaseModel):
    version: str = "1.0"
    type: Literal["AUTHENTICATION", "ENROLLMENT"]
    session_token: str
    nonce: str
    origin: str
    timestamp: int


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_token: str
    challenge_nonce: str
    session_type: str
    status: str
    client_origin: str
    qr_payload: QRPayload
    created_at: datetime
    expires_at: datetime
    poll_interval_ms: int = 1500


class SessionStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_token: str
    session_type: str
    status: str
    expires_at: datetime
    device: DeviceSummary | None = None
    access_token: str | None = None


class SessionScanRequest(BaseModel):
    device_id: str | None = Field(
        default=None,
        description="Optional device ID reporting the QR code scan",
    )


class SessionVerifyRequest(BaseModel):
    device_id: str = Field(description="Device ID performing authentication")
    canonical_payload: str = Field(description="Exact canonical string signed by the device")
    signature: str = Field(description="Base64 ASN.1 DER ECDSA P-256 signature")


class DeviceRegisterRequest(BaseModel):
    session_token: str = Field(description="Active ENROLLMENT session token")
    device_id: str = Field(description="Unique device identifier")
    device_name: str = Field(description="Human-readable device name")
    model: str = Field(description="Hardware model")
    android_version: str = Field(description="Android OS version")
    public_key_x509: str = Field(description="Base64 X.509 SubjectPublicKeyInfo DER")
    security_level: str = Field(
        default="TRUSTED_ENVIRONMENT",
        description="STRONGBOX, TRUSTED_ENVIRONMENT, or SOFTWARE",
    )
    canonical_payload: str = Field(description="Canonical challenge string from enrollment session")
    signature: str = Field(description="Signature authorizing enrollment")


class DeviceRevokeRequest(BaseModel):
    reason: str | None = Field(default=None, description="Reason for device revocation")
