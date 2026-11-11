import secrets

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.auth import DEFAULT_ACCOUNT_ID, Device
from app.schemas.auth import (
    DeviceLifecycleSummaryResponse,
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceRestoreRequest,
    DeviceRevokeRequest,
    DeviceStatusCheckResponse,
    DeviceUnregisterRequest,
    SessionCreateRequest,
    SessionResponse,
    SessionScanRequest,
    SessionStatusResponse,
    SessionVerifyRequest,
)
from app.schemas.common import ErrorResponse
from app.services.auth import (
    create_auth_session,
    get_auth_session_status,
    get_device_lifecycle_summary,
    get_device_status,
    list_devices,
    mark_session_scanned,
    register_device,
    restore_device,
    revoke_device,
    unregister_device,
    verify_session_signature,
)

router = APIRouter()


def require_dev_admin_access(
    x_dev_admin_key: str | None = Header(default=None, alias="X-Dev-Admin-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Restrict global multi-row device listing to isolated development environments
    with mandatory administrative key authentication.
    """
    if settings.app_env == "production":
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="endpoint_disabled_in_production",
            message="Device registry inspection is strictly disabled in production environments.",
        )

    if not x_dev_admin_key or not secrets.compare_digest(x_dev_admin_key, settings.dev_admin_key):
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized_admin_access",
            message="Valid X-Dev-Admin-Key is required to access the device registry.",
        )


def _has_valid_recovery_or_dev_admin(
    *,
    x_dev_admin_key: str | None,
    x_account_recovery_key: str | None,
    settings: Settings,
) -> bool:
    if x_account_recovery_key:
        expected_recovery = (settings.account_recovery_key or "").strip()
        if not expected_recovery or not secrets.compare_digest(x_account_recovery_key, expected_recovery):
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_recovery_authorization",
                message="Invalid account recovery authorization key.",
            )
        return True

    if x_dev_admin_key:
        if settings.app_env == "production":
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="dev_admin_key_disabled_in_production",
                message="Development administrative key is disabled in production.",
            )
        if not secrets.compare_digest(x_dev_admin_key, settings.dev_admin_key):
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="unauthorized_admin_access",
                message="Invalid X-Dev-Admin-Key provided.",
            )
        return True

    return False


def require_device_action_access(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_dev_admin_key: str | None = Header(default=None, alias="X-Dev-Admin-Key"),
    x_account_recovery_key: str | None = Header(default=None, alias="X-Account-Recovery-Key"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Device | None:
    """
    Authorize device lifecycle queries and mutations (summary, revoke, unregister).
    Returns the authenticated caller Device when authorized via Bearer token so services
    enforce account-level ownership isolation, or None when authorized via recovery/dev admin key.
    """
    if _has_valid_recovery_or_dev_admin(
        x_dev_admin_key=x_dev_admin_key,
        x_account_recovery_key=x_account_recovery_key,
        settings=settings,
    ):
        return None

    if authorization and authorization.startswith("Bearer "):
        return get_current_authenticated_device(authorization=authorization, db=db)

    if settings.app_env == "production":
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized_admin_access",
            message="Valid authenticated Bearer token or account recovery authorization is required.",
        )
    return None


def require_restore_access_authorization(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_dev_admin_key: str | None = Header(default=None, alias="X-Dev-Admin-Key"),
    x_account_recovery_key: str | None = Header(default=None, alias="X-Account-Recovery-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Fail-closed authorization guard for restoring a REVOKED device.
    A REVOKED device MUST NEVER authorize its own restoration using its blocked key or Bearer token.
    Requires explicit X-Account-Recovery-Key (all environments) or X-Dev-Admin-Key (non-production only).
    """
    if _has_valid_recovery_or_dev_admin(
        x_dev_admin_key=x_dev_admin_key,
        x_account_recovery_key=x_account_recovery_key,
        settings=settings,
    ):
        return

    if authorization and authorization.startswith("Bearer "):
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="recovery_authorization_required",
            message="Device self-restoration via Bearer session token is forbidden. Valid recovery authorization is required.",
        )

    raise AppError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="recovery_authorization_required",
        message="Valid X-Account-Recovery-Key or administrative recovery authorization is required to restore access.",
    )


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create authentication or enrollment session challenge",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid session parameters or untrusted origin."},
    },
)
def create_session(
    body: SessionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    origin: str | None = Header(default=None),
) -> SessionResponse:
    candidate_origin = body.origin or origin
    client_ip = request.client.host if request.client else None
    client_ua = request.headers.get("user-agent")

    return create_auth_session(
        db=db,
        request=body,
        candidate_origin=candidate_origin,
        client_user_agent=client_ua,
        client_ip=client_ip,
    )


@router.get(
    "/sessions/{session_token}",
    response_model=SessionStatusResponse,
    summary="Get status of an authentication or enrollment session",
    responses={
        403: {"model": ErrorResponse, "description": "Invalid or missing browser channel token."},
        404: {"model": ErrorResponse, "description": "Session not found."},
    },
)
def get_session(
    session_token: str,
    x_browser_channel_token: str | None = Header(default=None, alias="X-Browser-Channel-Token"),
    db: Session = Depends(get_db),
) -> SessionStatusResponse:
    return get_auth_session_status(
        db=db,
        session_token=session_token,
        browser_channel_token=x_browser_channel_token,
    )


@router.post(
    "/sessions/{session_token}/scan",
    response_model=SessionStatusResponse,
    summary="Mark session as scanned by mobile authenticator",
    responses={
        400: {"model": ErrorResponse, "description": "Session expired or invalid state."},
        404: {"model": ErrorResponse, "description": "Session not found."},
    },
)
def scan_session(
    session_token: str,
    body: SessionScanRequest | None = None,
    db: Session = Depends(get_db),
) -> SessionStatusResponse:
    device_id = body.device_id if body else None
    return mark_session_scanned(
        db=db,
        session_token=session_token,
        device_id=device_id,
    )


@router.post(
    "/sessions/{session_token}/verify",
    response_model=SessionStatusResponse,
    summary="Verify signature for an authentication session",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid session, payload, or expired."},
        401: {"model": ErrorResponse, "description": "Cryptographic signature verification failed."},
        403: {"model": ErrorResponse, "description": "Device revoked or unauthorized."},
        404: {"model": ErrorResponse, "description": "Session or device not found."},
    },
)
def verify_session(
    session_token: str,
    body: SessionVerifyRequest,
    db: Session = Depends(get_db),
) -> SessionStatusResponse:
    return verify_session_signature(
        db=db,
        session_token=session_token,
        request=body,
    )


@router.post(
    "/devices/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new authenticator device with cryptographic proof",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid enrollment challenge or key."},
        401: {"model": ErrorResponse, "description": "Cryptographic signature verification failed."},
        404: {"model": ErrorResponse, "description": "Enrollment session not found."},
        409: {"model": ErrorResponse, "description": "Account or device already has a registered authenticator."},
    },
)
def register_new_device(
    body: DeviceRegisterRequest,
    db: Session = Depends(get_db),
) -> DeviceResponse:
    return register_device(db=db, request=body)


@router.get(
    "/devices/summary",
    response_model=DeviceLifecycleSummaryResponse,
    summary="Get single-device account registration summary and unregistered history",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized."},
        403: {"model": ErrorResponse, "description": "Cross-account inspection forbidden."},
    },
)
def get_account_device_summary(
    account_id: str | None = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
    caller_device: Device | None = Depends(require_device_action_access),
) -> DeviceLifecycleSummaryResponse:
    if caller_device is not None:
        if account_id and account_id != caller_device.account_id:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="cross_owner_forbidden",
                message="Cannot inspect device lifecycle summary for another account.",
            )
        target_account = caller_device.account_id
    else:
        target_account = account_id or DEFAULT_ACCOUNT_ID

    return get_device_lifecycle_summary(db=db, account_id=target_account)


@router.get(
    "/devices/{device_id}/status",
    response_model=DeviceStatusCheckResponse,
    summary="Check device registration and access status",
)
def check_device_enrollment_status(
    device_id: str,
    db: Session = Depends(get_db),
) -> DeviceStatusCheckResponse:
    return get_device_status(db=db, device_id=device_id)


@router.post(
    "/devices/{device_id}/revoke",
    response_model=DeviceResponse,
    summary="Temporarily revoke an enrolled authenticator device",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized."},
        403: {"model": ErrorResponse, "description": "Cross-owner modification forbidden."},
        404: {"model": ErrorResponse, "description": "Device not found."},
        409: {"model": ErrorResponse, "description": "Unregistered device cannot be revoked."},
    },
)
def revoke_enrolled_device(
    device_id: str,
    body: DeviceRevokeRequest | None = None,
    db: Session = Depends(get_db),
    caller_device: Device | None = Depends(require_device_action_access),
) -> DeviceResponse:
    return revoke_device(
        db=db,
        device_id=device_id,
        caller_device=caller_device,
        reason=body.reason if body else None,
    )


@router.post(
    "/devices/{device_id}/restore",
    response_model=DeviceResponse,
    summary="Restore access for a REVOKED authenticator device without creating a new key",
    responses={
        401: {"model": ErrorResponse, "description": "Recovery authorization required."},
        403: {"model": ErrorResponse, "description": "Self-restoration forbidden."},
        404: {"model": ErrorResponse, "description": "Device not found."},
        409: {"model": ErrorResponse, "description": "Unregistered device cannot be restored."},
    },
)
def restore_revoked_device(
    device_id: str,
    body: DeviceRestoreRequest | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_restore_access_authorization),
) -> DeviceResponse:
    return restore_device(
        db=db,
        device_id=device_id,
        reason=body.reason if body else None,
    )


@router.post(
    "/devices/{device_id}/unregister",
    response_model=DeviceResponse,
    summary="Explicitly unregister a device, releasing the account's device slot",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized."},
        403: {"model": ErrorResponse, "description": "Cross-owner modification forbidden."},
        404: {"model": ErrorResponse, "description": "Device not found."},
    },
)
def unregister_enrolled_device(
    device_id: str,
    body: DeviceUnregisterRequest | None = None,
    db: Session = Depends(get_db),
    caller_device: Device | None = Depends(require_device_action_access),
) -> DeviceResponse:
    return unregister_device(
        db=db,
        device_id=device_id,
        caller_device=caller_device,
        reason=body.reason if body else None,
    )


@router.get(
    "/devices",
    response_model=list[DeviceResponse],
    summary="List all registered devices (non-production admin)",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized. Administrative key required."},
        403: {"model": ErrorResponse, "description": "Forbidden. Endpoint disabled in production."},
    },
)
def get_registered_devices(
    db: Session = Depends(get_db),
    _: None = Depends(require_dev_admin_access),
) -> list[DeviceResponse]:
    return list_devices(db=db)
