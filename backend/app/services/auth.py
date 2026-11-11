from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.auth import Account, AuthSession, DEFAULT_ACCOUNT_ID, Device
from app.schemas.auth import (
    DeviceLifecycleSummaryResponse,
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
from app.services.audit_chain import AuditChainError, append_audit_event
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


def _resolve_account_id(candidate: str | None) -> str:
    cleaned = (candidate or "").strip()
    return cleaned if cleaned else DEFAULT_ACCOUNT_ID


def _ensure_and_lock_account(db: Session, account_id: str) -> Account:
    """
    Create canonical Account row if absent and acquire an exclusive FOR UPDATE lock
    to serialize concurrent enrollment attempts on the same account.
    """
    dialect = db.get_bind().dialect.name
    insert_factory = {"postgresql": postgres_insert, "sqlite": sqlite_insert}.get(dialect)
    if insert_factory is not None:
        db.execute(
            insert_factory(Account)
            .values(account_id=account_id, display_name=f"IPGuard Account ({account_id})")
            .on_conflict_do_nothing(index_elements=[Account.account_id])
        )
    account = db.scalar(
        select(Account).where(Account.account_id == account_id).with_for_update()
    )
    if account is None:
        account = Account(account_id=account_id, display_name=f"IPGuard Account ({account_id})")
        db.add(account)
        db.flush()
    return account


def _record_device_audit_event(
    db: Session,
    *,
    device: Device,
    event_type: str,
    result: str,
    actor_type: str = "SYSTEM",
    reason: str | None = None,
) -> None:
    actor_device_id = device.device_id if actor_type == "DEVICE" else None
    payload: dict[str, object] = {
        "account_id": device.account_id,
        "device_id": device.device_id,
        "public_key_fingerprint": device.public_key_fingerprint,
        "registration_status": "UNREGISTERED" if device.status == "UNREGISTERED" else "REGISTERED",
        "status": device.status,
    }
    if reason:
        payload["reason"] = reason[:200]
    try:
        append_audit_event(
            db,
            chain_id=device.device_id,
            event_type=event_type,
            resource_type="device",
            resource_id=device.device_id,
            result=result,
            payload=payload,
            actor_type=actor_type,  # type: ignore[arg-type]
            actor_device_id=actor_device_id,
        )
    except AuditChainError as exc:
        raise AppError(
            status_code=500,
            code="audit_chain_error",
            message="Failed to record security audit event.",
        ) from exc


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
    account_id = _resolve_account_id(request.account_id)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=CHALLENGE_TIMEOUT_SECONDS)

    session_token = generate_secure_token(32)
    challenge_nonce = generate_secure_token(32)
    browser_channel_token = generate_secure_token(32)
    browser_channel_token_hash = hashlib.sha256(browser_channel_token.encode("utf-8")).hexdigest()

    session = AuthSession(
        account_id=account_id,
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
            code="session_already_consumed",
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
    Enforces One Account = Maximum 1 Registered Android Device (ACTIVE or REVOKED):
    - Locks the canonical Account row via SELECT FOR UPDATE to serialize concurrent enrollments.
    - Rejects duplicate registration of the same device or same account with HTTP 409 DEVICE_ALREADY_REGISTERED.
    - REVOKED device keeps the account slot locked until explicitly unregistered.
    - UNREGISTERED releases the account slot, allowing new device enrollment or re-enrollment.
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

    account_id = _resolve_account_id(session.account_id)

    # 2. Acquire account-level exclusive lock to serialize concurrent enrollment on the same account
    _ensure_and_lock_account(db, account_id)

    # 3. Enforce single-registered-device per account (ACTIVE or REVOKED locks the slot)
    account_registered_device = db.scalar(
        select(Device)
        .where(
            Device.account_id == account_id,
            Device.status.in_(("ACTIVE", "REVOKED")),
        )
        .with_for_update()
    )
    if account_registered_device:
        if account_registered_device.device_id == request.device_id:
            if account_registered_device.status == "REVOKED":
                raise AppError(
                    status_code=409,
                    code="DEVICE_ALREADY_REGISTERED",
                    message="Akses perangkat ini telah dicabut namun registrasi masih terkunci. Silakan lakukan Unregister Device melalui web console untuk mendaftarkan ulang.",
                )
            raise AppError(
                status_code=409,
                code="DEVICE_ALREADY_REGISTERED",
                message="Perangkat ini sudah terdaftar di IPGuard. Silakan gunakan Sign In untuk melanjutkan.",
            )
        raise AppError(
            status_code=409,
            code="DEVICE_ALREADY_REGISTERED",
            message="Akun ini sudah memiliki perangkat Android terdaftar (1/1). Lepas registrasi perangkat sebelumnya melalui Device Management sebelum mendaftarkan perangkat baru.",
        )

    # 4. Also ensure this device_id is not still ACTIVE/REVOKED under any legacy record
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
        if existing_device.status == "REVOKED":
            raise AppError(
                status_code=409,
                code="DEVICE_ALREADY_REGISTERED",
                message="Akses perangkat ini telah dicabut namun registrasi masih terkunci. Silakan lakukan Unregister Device melalui web console untuk mendaftarkan ulang.",
            )

    # 5. Cryptographically validate the public key (EC NIST P-256)
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
            if existing_key.status == "REVOKED":
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

    # 6. Verify canonical payload matches session parameters exactly
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

    # 7. Verify cryptographic signature using the provided public key
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

    # 8. Create new device or re-activate previously UNREGISTERED device
    if existing_device:
        device = existing_device
        device.account_id = account_id
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
            account_id=account_id,
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

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            status_code=409,
            code="DEVICE_ALREADY_REGISTERED",
            message="Akun ini sudah memiliki perangkat terdaftar atau perangkat bentrok dengan registrasi lain.",
        ) from exc

    # 9. Atomically consume the enrollment session and append audit record
    session.status = "APPROVED"
    session.device_id = device.id
    session.canonical_payload = request.canonical_payload
    session.signature = request.signature
    session.signed_at = now
    session.expires_at = now + timedelta(seconds=AUTHENTICATED_SESSION_LIFETIME_SECONDS)

    _record_device_audit_event(
        db,
        device=device,
        event_type="DEVICE_ENROLLED",
        result="ACTIVE",
        actor_type="DEVICE",
    )

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
    revoked/unregistered device, or invalid cryptographic signature.
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
            message=f"Device '{request.device_id}' is {device.status.lower()} and cannot authenticate.",
        )

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

    session.status = "APPROVED"
    session.device_id = device.id
    session.canonical_payload = request.canonical_payload
    session.signature = request.signature
    session.signed_at = now
    session.expires_at = now + timedelta(seconds=AUTHENTICATED_SESSION_LIFETIME_SECONDS)

    device.last_used_at = now

    _record_device_audit_event(
        db,
        device=device,
        event_type="DEVICE_AUTHENTICATED",
        result="APPROVED",
        actor_type="DEVICE",
    )

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


def _assert_caller_owns_target(caller_device: Device | None, target_device: Device) -> None:
    if caller_device is not None and caller_device.account_id != target_device.account_id:
        raise AppError(
            status_code=403,
            code="cross_owner_forbidden",
            message="Authenticated device is not authorized to manage another account's device.",
        )


def _invalidate_device_sessions(db: Session, device: Device, now: datetime) -> None:
    approved_sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.device_id == device.id,
            AuthSession.status == "APPROVED",
        ).with_for_update()
    ).all()
    for s in approved_sessions:
        s.status = "REVOKED"
        s.expires_at = now

    pending_sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.account_id == device.account_id,
            AuthSession.status.in_(("PENDING", "SCANNED")),
        ).with_for_update()
    ).all()
    for s in pending_sessions:
        s.status = "REVOKED"
        s.expires_at = now


def revoke_device(
    db: Session,
    device_id: str,
    *,
    caller_device: Device | None = None,
    reason: str | None = None,
) -> DeviceResponse:
    """
    Revoke an active device, preventing future authentications while keeping
    the account registration slot reserved (REVOKED still locks 1/1 slot).
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

    _assert_caller_owns_target(caller_device, device)

    if device.status == "UNREGISTERED":
        raise AppError(
            status_code=409,
            code="cannot_revoke_unregistered_device",
            message="Unregistered devices do not hold an active registration to revoke.",
        )

    now = datetime.now(timezone.utc)
    if device.status != "REVOKED":
        device.status = "REVOKED"
        device.revoked_at = now
        _invalidate_device_sessions(db, device, now)
        _record_device_audit_event(
            db,
            device=device,
            event_type="DEVICE_REVOKED",
            result="REVOKED",
            actor_type="SYSTEM",
            reason=reason,
        )

    db.commit()
    db.refresh(device)

    return DeviceResponse.model_validate(device)


def restore_device(
    db: Session,
    device_id: str,
    *,
    reason: str | None = None,
) -> DeviceResponse:
    """
    Restore access for a REVOKED device back to ACTIVE, keeping its original
    registration record and ECDSA P-256 public key intact without re-enrollment.
    Cannot be called on an UNREGISTERED device.
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

    if device.status == "UNREGISTERED":
        raise AppError(
            status_code=409,
            code="cannot_restore_unregistered_device",
            message="Unregistered devices cannot be restored. Complete new device enrollment instead.",
        )

    # Validate public key binding remains cryptographically intact before restoring
    parse_and_validate_public_key(device.public_key_x509)

    if device.status != "ACTIVE":
        device.status = "ACTIVE"
        device.revoked_at = None
        _record_device_audit_event(
            db,
            device=device,
            event_type="DEVICE_RESTORED",
            result="ACTIVE",
            actor_type="SYSTEM",
            reason=reason,
        )

    db.commit()
    db.refresh(device)

    return DeviceResponse.model_validate(device)


def unregister_device(
    db: Session,
    device_id: str,
    *,
    caller_device: Device | None = None,
    reason: str | None = None,
) -> DeviceResponse:
    """
    Explicitly unregister a device, ending its current registration binding and
    releasing the account's device slot (0/1). Preserves historical device record,
    audit trail, Secure Notes, and Asset Vault.
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

    _assert_caller_owns_target(caller_device, device)

    now = datetime.now(timezone.utc)
    if device.status != "UNREGISTERED":
        device.status = "UNREGISTERED"
        device.unregistered_at = now
        _invalidate_device_sessions(db, device, now)
        _record_device_audit_event(
            db,
            device=device,
            event_type="DEVICE_UNREGISTERED",
            result="UNREGISTERED",
            actor_type="SYSTEM",
            reason=reason,
        )

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
            account_id=None,
            status="NOT_ENROLLED",
            registration_status="UNREGISTERED",
            access_status="REVOKED",
            public_key_fingerprint=None,
            enrolled_at=None,
        )

    return DeviceStatusCheckResponse(
        device_id=device.device_id,
        account_id=device.account_id,
        status=device.status,
        registration_status="UNREGISTERED" if device.status == "UNREGISTERED" else "REGISTERED",
        access_status="ACTIVE" if device.status == "ACTIVE" else "REVOKED",
        public_key_fingerprint=device.public_key_fingerprint,
        enrolled_at=device.enrolled_at,
    )


def get_device_lifecycle_summary(
    db: Session,
    account_id: str,
) -> DeviceLifecycleSummaryResponse:
    """
    Return the single-device slot posture (0/1 or 1/1), current registered device
    (ACTIVE or REVOKED), and separated UNREGISTERED historical records for an account.
    """
    resolved_account = _resolve_account_id(account_id)
    devices = db.scalars(
        select(Device)
        .where(Device.account_id == resolved_account)
        .order_by(Device.enrolled_at.desc())
    ).all()

    current_device = next((d for d in devices if d.status in ("ACTIVE", "REVOKED")), None)
    history = [d for d in devices if d.status == "UNREGISTERED"]

    return DeviceLifecycleSummaryResponse(
        account_id=resolved_account,
        registered_slots=1 if current_device is not None else 0,
        max_slots=1,
        current_device=DeviceResponse.model_validate(current_device) if current_device else None,
        history=[DeviceResponse.model_validate(d) for d in history],
    )


def list_devices(db: Session) -> list[DeviceResponse]:
    """
    List all registered devices (administrative development inspection).
    """
    devices = db.scalars(select(Device).order_by(Device.enrolled_at.desc())).all()
    return [DeviceResponse.model_validate(d) for d in devices]
