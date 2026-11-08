from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Literal
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.auth import AuthSession, Device
from app.schemas.auth import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceStatusCheckResponse,
    DeviceSummary,
    QRPayload,
    SessionCreateRequest,
    SessionResponse,
    SessionStatusResponse,
    SessionVerifyRequest,
)
from app.services.crypto import (
    build_canonical_payload,
    compute_public_key_fingerprint,
    generate_secure_token,
    parse_and_validate_public_key,
    verify_ecdsa_signature,
)
from app.services.origin import validate_and_resolve_origin

CHALLENGE_TIMEOUT_SECONDS = 60
AUTHENTICATED_SESSION_LIFETIME_SECONDS = 3600
DEFAULT_POLL_INTERVAL_MS = 1500


def create_auth_session(
    db: Session,
    request: SessionCreateRequest,
    candidate_origin: str | None = None,
    client_user_agent: str | None = None,
    client_ip: str | None = None,
) -> SessionResponse:
    """
    Create a new authentication or enrollment session with a cryptographically
    secure nonce, normalized and whitelisted trusted origin, and strict 60-second expiration.
    """
    settings = get_settings()
    effective_origin = validate_and_resolve_origin(
        candidate_origin=request.origin or candidate_origin,
        trusted_origins=settings.trusted_origin_list,
    )
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=CHALLENGE_TIMEOUT_SECONDS)

    session_token = generate_secure_token(32)
    challenge_nonce = generate_secure_token(32)
    browser_channel_token = generate_secure_token(32)
    browser_channel_token_hash = hashlib.sha256(browser_channel_token.encode("utf-8")).hexdigest()

    session = AuthSession(
        session_token=session_token,
        challenge_nonce=challenge_nonce,
        browser_channel_token_hash=browser_channel_token_hash,
        session_type=request.session_type,
        status="PENDING",
        client_origin=effective_origin,
        client_user_agent=client_user_agent,
        client_ip=client_ip,
        created_at=now,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    qr_payload = QRPayload(
        version="1.0",
        type=session.session_type,  # type: ignore[arg-type]
        session_token=session.session_token,
        nonce=session.challenge_nonce,
        origin=session.client_origin,
        timestamp=int(session.created_at.timestamp()),
    )

    return SessionResponse(
        session_token=session.session_token,
        challenge_nonce=session.challenge_nonce,
        session_type=session.session_type,
        status=session.status,
        client_origin=session.client_origin,
        qr_payload=qr_payload,
        created_at=session.created_at,
        expires_at=session.expires_at,
        poll_interval_ms=DEFAULT_POLL_INTERVAL_MS,
        browser_channel_token=browser_channel_token,
    )


def get_auth_session_status(
    db: Session,
    session_token: str,
    browser_channel_token: str | None = None,
) -> SessionStatusResponse:
    """
    Retrieve session state with lazy expiration checking and SEC-02 Anti QR-Jacking authorization.
    Uses non-locking read for polling efficiency.
    """
    session = db.scalar(
        select(AuthSession).where(AuthSession.session_token == session_token)
    )
    if not session:
        raise AppError(
            status_code=404,
            code="session_not_found",
            message="Authentication session not found.",
        )

    # SEC-02 Anti QR-Jacking / Shoulder-Surfing: Validate browser channel authorization
    if session.browser_channel_token_hash:
        if not browser_channel_token:
            raise AppError(
                status_code=403,
                code="invalid_or_missing_browser_channel_token",
                message="Valid X-Browser-Channel-Token header is required to poll this session.",
            )
        presented_hash = hashlib.sha256(browser_channel_token.encode("utf-8")).hexdigest()
        if not secrets.compare_digest(presented_hash, session.browser_channel_token_hash):
            raise AppError(
                status_code=403,
                code="invalid_or_missing_browser_channel_token",
                message="Valid X-Browser-Channel-Token header is required to poll this session.",
            )

    now = datetime.now(timezone.utc)
    if session.status in ("PENDING", "SCANNED") and now > session.expires_at:
        session.status = "EXPIRED"
        db.commit()
        db.refresh(session)

    device_summary: DeviceSummary | None = None
    access_token: str | None = None

    if session.status == "APPROVED" and session.device:
        device_summary = DeviceSummary.model_validate(session.device)
        access_token = f"ipguard_sess_{session.session_token[:24]}"

    return SessionStatusResponse(
        session_token=session.session_token,
        session_type=session.session_type,
        status=session.status,
        expires_at=session.expires_at,
        device=device_summary,
        access_token=access_token,
    )


def mark_session_scanned(
    db: Session,
    session_token: str,
    device_id: str | None = None,
) -> SessionStatusResponse:
    """
    Signal that the mobile authenticator scanned the QR code.
    Fails closed if the session is expired or not pending.
    Uses row-level lock (SELECT FOR UPDATE) to ensure atomic state transition.
    """
    session = db.scalar(
        select(AuthSession)
        .where(AuthSession.session_token == session_token)
        .with_for_update()
    )
    if not session:
        raise AppError(
            status_code=404,
            code="session_not_found",
            message="Authentication session not found.",
        )

    now = datetime.now(timezone.utc)
    if now > session.expires_at or session.status == "EXPIRED":
        session.status = "EXPIRED"
        db.commit()
        raise AppError(
            status_code=400,
            code="session_expired",
            message="Authentication session has expired.",
        )

    if session.status == "APPROVED":
        raise AppError(
            status_code=400,
            code="session_already_approved",
            message="Session has already been approved.",
        )

    if session.status != "SCANNED":
        session.status = "SCANNED"
        db.commit()
        db.refresh(session)

    return SessionStatusResponse(
        session_token=session.session_token,
        session_type=session.session_type,
        status=session.status,
        expires_at=session.expires_at,
    )


def register_device(db: Session, request: DeviceRegisterRequest) -> DeviceResponse:
    """
    Register a mobile device with its Android Keystore ECDSA P-256 public key.
    Enforces One-Time Device Enrollment:
    - Fresh device or explicitly UNREGISTERED device: enrollment accepted.
    - ACTIVE device: rejected with HTTP 409 DEVICE_ALREADY_REGISTERED.
    - REVOKED device: rejected with HTTP 409 DEVICE_ALREADY_REGISTERED (must be explicitly uninstalled/unregistered first).
    - Re-enrollment of an UNREGISTERED device re-activates existing identity without losing note ownership.
    - Pessimistic row-level locking guarantees concurrency protection.
    """
    # 1. Validate the enrollment session with exclusive row lock
    session = db.scalar(
        select(AuthSession)
        .where(AuthSession.session_token == request.session_token)
        .with_for_update()
    )
    if not session:
        raise AppError(
            status_code=404,
            code="session_not_found",
            message="Enrollment session not found.",
        )

    if session.session_type != "ENROLLMENT":
        raise AppError(
            status_code=400,
            code="invalid_session_type",
            message="Device registration requires an ENROLLMENT session.",
        )

    now = datetime.now(timezone.utc)
    if now > session.expires_at or session.status == "EXPIRED":
        session.status = "EXPIRED"
        db.commit()
        raise AppError(
            status_code=400,
            code="session_expired",
            message="Enrollment session has expired.",
        )

    if session.status == "APPROVED":
        raise AppError(
            status_code=400,
            code="session_already_consumed",
            message="Enrollment session challenge has already been consumed.",
        )

    # 2. Check for duplicate device ID or existing active/revoked device
    existing_device = db.scalar(
        select(Device).where(Device.device_id == request.device_id).with_for_update()
    )
    if existing_device:
        if existing_device.status == "ACTIVE":
            raise AppError(
                status_code=409,
                code="DEVICE_ALREADY_REGISTERED",
                message="Perangkat ini sudah terdaftar di IPGuard. Silakan gunakan Sign In untuk melanjutkan.",
            )
        elif existing_device.status == "REVOKED":
            raise AppError(
                status_code=409,
                code="DEVICE_ALREADY_REGISTERED",
                message="Akses perangkat ini telah dicabut namun registrasi masih terkunci. Silakan lakukan Unregister Device melalui web console untuk mendaftarkan ulang.",
            )

    # 3. Cryptographically validate the public key (EC NIST P-256)
    public_key, der_bytes = parse_and_validate_public_key(request.public_key_x509)
    fingerprint = compute_public_key_fingerprint(der_bytes)

    existing_key = db.scalar(
        select(Device).where(Device.public_key_fingerprint == fingerprint).with_for_update()
    )
    if existing_key:
        if existing_device and existing_key.id == existing_device.id:
            if existing_key.status == "ACTIVE":
                raise AppError(
                    status_code=409,
                    code="DEVICE_ALREADY_REGISTERED",
                    message="Perangkat ini sudah terdaftar di IPGuard. Silakan gunakan Sign In untuk melanjutkan.",
                )
            elif existing_key.status == "REVOKED":
                raise AppError(
                    status_code=409,
                    code="DEVICE_ALREADY_REGISTERED",
                    message="Akses perangkat ini telah dicabut namun registrasi masih terkunci. Silakan lakukan Unregister Device melalui web console untuk mendaftarkan ulang.",
                )
        elif existing_key.status in ("ACTIVE", "REVOKED"):
            raise AppError(
                status_code=409,
                code="DEVICE_ALREADY_REGISTERED",
                message="Public signing key ini sudah terdaftar pada perangkat lain yang aktif atau terkunci.",
            )

    # 4. Verify canonical payload matches session parameters exactly
    expected_canonical_payload = build_canonical_payload(
        session_token=session.session_token,
        nonce=session.challenge_nonce,
        origin=session.client_origin,
        timestamp=int(session.created_at.timestamp()),
    )
    if request.canonical_payload != expected_canonical_payload:
        raise AppError(
            status_code=400,
            code="invalid_canonical_payload",
            message="Canonical payload does not match enrollment challenge parameters.",
        )

    # 5. Verify cryptographic signature using the provided public key
    is_valid = verify_ecdsa_signature(
        public_key=public_key,
        canonical_payload=request.canonical_payload,
        signature_b64=request.signature,
    )
    if not is_valid:
        raise AppError(
            status_code=401,
            code="signature_verification_failed",
            message="ECDSA signature verification failed for enrollment authorization.",
        )

    # 6. Create new device or re-activate previously UNREGISTERED device
    if existing_device:
        device = existing_device
        device.device_name = request.device_name
        device.model = request.model
        device.android_version = request.android_version
        device.public_key_x509 = request.public_key_x509
        device.public_key_fingerprint = fingerprint
        device.security_level = request.security_level
        device.status = "ACTIVE"
        device.enrolled_at = now
        device.last_used_at = now
        device.revoked_at = None
        device.unregistered_at = None
    else:
        device = Device(
            device_id=request.device_id,
            device_name=request.device_name,
            model=request.model,
            android_version=request.android_version,
            public_key_x509=request.public_key_x509,
            public_key_fingerprint=fingerprint,
            security_level=request.security_level,
            status="ACTIVE",
            enrolled_at=now,
            last_used_at=now,
        )
        db.add(device)
        db.flush()

    # 7. Atomically consume the enrollment session
    session.status = "APPROVED"
    session.device_id = device.id
    session.canonical_payload = request.canonical_payload
    session.signature = request.signature
    session.signed_at = now
    session.expires_at = now + timedelta(seconds=AUTHENTICATED_SESSION_LIFETIME_SECONDS)

    db.commit()
    db.refresh(device)

    return DeviceResponse.model_validate(device)


def verify_session_signature(
    db: Session,
    session_token: str,
    request: SessionVerifyRequest,
) -> SessionStatusResponse:
    """
    Verify ECDSA P-256 signature for an authentication session.
    Uses row-level pessimistic locking (SELECT FOR UPDATE) to guarantee atomic single-use challenge consumption.
    Fails closed on any discrepancy: expiration, replay, payload mismatch,
    revoked device, or invalid cryptographic signature.
    """
    # 1. Retrieve session with exclusive row lock
    session = db.scalar(
        select(AuthSession)
        .where(AuthSession.session_token == session_token)
        .with_for_update()
    )
    if not session:
        raise AppError(
            status_code=404,
            code="session_not_found",
            message="Authentication session not found.",
        )

    if session.session_type != "AUTHENTICATION":
        raise AppError(
            status_code=400,
            code="invalid_session_type",
            message="Session is not an AUTHENTICATION session.",
        )

    now = datetime.now(timezone.utc)
    if now > session.expires_at or session.status == "EXPIRED":
        session.status = "EXPIRED"
        db.commit()
        raise AppError(
            status_code=400,
            code="session_expired",
            message="Authentication session has expired.",
        )

    if session.status == "APPROVED":
        raise AppError(
            status_code=400,
            code="session_already_consumed",
            message="Authentication session challenge has already been consumed.",
        )

    # 2. Retrieve and check device
    device = db.scalar(
        select(Device).where(Device.device_id == request.device_id)
    )
    if not device:
        raise AppError(
            status_code=404,
            code="device_not_found",
            message=f"Device '{request.device_id}' is not enrolled.",
        )

    if device.status != "ACTIVE":
        raise AppError(
            status_code=403,
            code="device_revoked",
            message=f"Device '{request.device_id}' is revoked or inactive and cannot authenticate.",
        )

    # 3. Canonical payload check (must match trusted origin bound to the session)
    expected_canonical_payload = build_canonical_payload(
        session_token=session.session_token,
        nonce=session.challenge_nonce,
        origin=session.client_origin,
        timestamp=int(session.created_at.timestamp()),
    )
    if request.canonical_payload != expected_canonical_payload:
        raise AppError(
            status_code=400,
            code="invalid_canonical_payload",
            message="Canonical payload does not match expected session challenge.",
        )

    # 4. Cryptographic signature check
    public_key, _ = parse_and_validate_public_key(device.public_key_x509)
    is_valid = verify_ecdsa_signature(
        public_key=public_key,
        canonical_payload=request.canonical_payload,
        signature_b64=request.signature,
    )
    if not is_valid:
        session.status = "REJECTED"
        db.commit()
        raise AppError(
            status_code=401,
            code="invalid_signature",
            message="ECDSA signature verification failed.",
        )

    # 5. Transition session to APPROVED atomically in the locked transaction
    session.status = "APPROVED"
    session.device_id = device.id
    session.canonical_payload = request.canonical_payload
    session.signature = request.signature
    session.signed_at = now
    session.expires_at = now + timedelta(seconds=AUTHENTICATED_SESSION_LIFETIME_SECONDS)

    device.last_used_at = now

    db.commit()
    db.refresh(session)

    device_summary = DeviceSummary.model_validate(device)
    access_token = f"ipguard_sess_{session.session_token[:24]}"

    return SessionStatusResponse(
        session_token=session.session_token,
        session_type=session.session_type,
        status="APPROVED",
        expires_at=session.expires_at,
        device=device_summary,
        access_token=access_token,
    )


def revoke_device(db: Session, device_id: str) -> DeviceResponse:
    """
    Revoke an active device, preventing any future authentications.
    Does NOT release the registration lock (cannot re-enroll while REVOKED).
    Invalidates all active sessions for this device.
    Uses row-level lock to ensure safe revocation.
    """
    device = db.scalar(
        select(Device).where(Device.device_id == device_id).with_for_update()
    )
    if not device:
        raise AppError(
            status_code=404,
            code="device_not_found",
            message=f"Device '{device_id}' not found.",
        )

    now = datetime.now(timezone.utc)
    if device.status != "REVOKED":
        device.status = "REVOKED"
        device.revoked_at = now

    # Invalidate all active approved sessions for this device
    active_sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.device_id == device.id,
            AuthSession.status == "APPROVED",
        ).with_for_update()
    ).all()
    for s in active_sessions:
        s.status = "REVOKED"
        s.expires_at = now

    db.commit()
    db.refresh(device)

    return DeviceResponse.model_validate(device)


def unregister_device(db: Session, device_id: str) -> DeviceResponse:
    """
    Explicitly unregister a device, ending its registration binding.
    Transitions registration lifecycle to UNREGISTERED.
    Invalidates all active sessions for this device.
    Allows new enrollment after unregistration is complete.
    Never hard-deletes the Device row or related Secure Notes.
    """
    device = db.scalar(
        select(Device).where(Device.device_id == device_id).with_for_update()
    )
    if not device:
        raise AppError(
            status_code=404,
            code="device_not_found",
            message=f"Device '{device_id}' not found.",
        )

    now = datetime.now(timezone.utc)
    device.status = "UNREGISTERED"
    device.unregistered_at = now

    # Invalidate all active approved sessions for this device
    active_sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.device_id == device.id,
            AuthSession.status == "APPROVED",
        ).with_for_update()
    ).all()
    for s in active_sessions:
        s.status = "REVOKED"
        s.expires_at = now

    db.commit()
    db.refresh(device)

    return DeviceResponse.model_validate(device)


def get_device_status(db: Session, device_id: str) -> DeviceStatusCheckResponse:
    """
    Query registration and access status for mobile authenticator synchronization.
    """
    device = db.scalar(
        select(Device).where(Device.device_id == device_id)
    )
    if not device:
        return DeviceStatusCheckResponse(
            device_id=device_id,
            status="NOT_ENROLLED",
            registration_status="UNREGISTERED",
            access_status="REVOKED",
            public_key_fingerprint=None,
            enrolled_at=None,
        )

    return DeviceStatusCheckResponse(
        device_id=device.device_id,
        status=device.status,
        registration_status="UNREGISTERED" if device.status == "UNREGISTERED" else "REGISTERED",
        access_status="ACTIVE" if device.status == "ACTIVE" else "REVOKED",
        public_key_fingerprint=device.public_key_fingerprint,
        enrolled_at=device.enrolled_at,
    )


def list_devices(db: Session) -> list[DeviceResponse]:
    """
    List all registered devices.
    """
    devices = db.scalars(select(Device).order_by(Device.enrolled_at.desc())).all()
    return [DeviceResponse.model_validate(d) for d in devices]
