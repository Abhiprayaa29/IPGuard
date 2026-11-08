from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.auth import (
    DeviceRegisterRequest,
    DeviceResponse,
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
    get_device_status,
    list_devices,
    mark_session_scanned,
    register_device,
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
    Restrict device listing to explicitly isolated development environments
    with mandatory administrative key authentication.
    - In production environments, access is strictly forbidden (HTTP 403).
    - In development and test environments, missing or invalid key returns HTTP 401.
    """
    if settings.app_env == "production":
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="endpoint_disabled_in_production",
            message="Device registry inspection is strictly disabled in production environments.",
        )

    if not x_dev_admin_key or x_dev_admin_key != settings.dev_admin_key:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized_admin_access",
            message="Valid X-Dev-Admin-Key is required to access the device registry.",
        )


def require_device_action_access(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_dev_admin_key: str | None = Header(default=None, alias="X-Dev-Admin-Key"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Authorize device lifecycle modifications (revoke, unregister).
    1. If X-Dev-Admin-Key is provided, it must match settings.dev_admin_key.
    2. If Bearer token is provided, it must be an active authenticated session.
    3. In production, unauthenticated requests are strictly rejected with HTTP 401.
    """
    if x_dev_admin_key:
        if x_dev_admin_key != settings.dev_admin_key:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="unauthorized_admin_access",
                message="Invalid X-Dev-Admin-Key provided.",
            )
        return

    if authorization and authorization.startswith("Bearer "):
        get_current_authenticated_device(authorization=authorization, db=db)
        return

    if settings.app_env == "production":
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized_admin_access",
            message="Valid X-Dev-Admin-Key or active authenticated Bearer token is required.",
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
        409: {"model": ErrorResponse, "description": "Device or public key already registered."},
    },
)
def register_new_device(
    body: DeviceRegisterRequest,
    db: Session = Depends(get_db),
) -> DeviceResponse:
    return register_device(db=db, request=body)


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
    summary="Revoke an enrolled authenticator device",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized. Dev admin key or active session token required."},
        404: {"model": ErrorResponse, "description": "Device not found."},
    },
)
def revoke_enrolled_device(
    device_id: str,
    body: DeviceRevokeRequest | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_device_action_access),
) -> DeviceResponse:
    return revoke_device(db=db, device_id=device_id)


@router.post(
    "/devices/{device_id}/unregister",
    response_model=DeviceResponse,
    summary="Explicitly unregister a device, releasing its enrollment slot",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized. Dev admin key or active session token required."},
        404: {"model": ErrorResponse, "description": "Device not found."},
    },
)
def unregister_enrolled_device(
    device_id: str,
    body: DeviceUnregisterRequest | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_device_action_access),
) -> DeviceResponse:
    return unregister_device(db=db, device_id=device_id)


@router.get(
    "/devices",
    response_model=list[DeviceResponse],
    summary="List all enrolled devices",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized. Administrative key required."},
        403: {"model": ErrorResponse, "description": "Forbidden. Disabled in production."},
    },
)
def get_all_devices(
    db: Session = Depends(get_db),
    _: None = Depends(require_dev_admin_access),
) -> list[DeviceResponse]:
    return list_devices(db=db)
