from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


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
    account_id: str
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
    unregistered_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def registration_status(self) -> str:
        if self.status == "UNREGISTERED":
            return "UNREGISTERED"
        return "REGISTERED"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def access_status(self) -> str:
        if self.status == "ACTIVE":
            return "ACTIVE"
        return "REVOKED"


class DeviceLifecycleSummaryResponse(BaseModel):
    account_id: str
    registered_slots: int
    max_slots: int = 1
    current_device: DeviceResponse | None = None
    history: list[DeviceResponse] = Field(default_factory=list)


class DeviceStatusCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    account_id: str | None = None
    status: str  # "ACTIVE", "REVOKED", "UNREGISTERED", or "NOT_ENROLLED"
    registration_status: str
    access_status: str
    public_key_fingerprint: str | None = None
    enrolled_at: datetime | None = None


class SessionCreateRequest(BaseModel):
    session_type: Literal["AUTHENTICATION", "ENROLLMENT"] = Field(
        default="AUTHENTICATION",
        description="Type of session: AUTHENTICATION for sign-in or ENROLLMENT for new device binding",
    )
    origin: str | None = Field(
        default=None,
        description="Explicit web origin if different from HTTP request headers",
    )
    account_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Canonical account identifier binding device enrollment slots (defaults to primary account).",
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
    browser_channel_token: str | None = Field(
        default=None,
        description='Secure channel token for the browser session to authorize polling and prevent QR-jacking',
    )


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


class DeviceRestoreRequest(BaseModel):
    reason: str | None = Field(default=None, description="Reason for restoring revoked device access")


class DeviceUnregisterRequest(BaseModel):
    reason: str | None = Field(default=None, description="Reason for device unregistration")
