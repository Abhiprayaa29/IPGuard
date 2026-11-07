from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceRevokeRequest,
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
    list_devices,
    mark_session_scanned,
    register_device,
    revoke_device,
    verify_session_signature,
)

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create authentication or enrollment session challenge",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid session parameters."},
    },
)
def create_session(
    body: SessionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    origin: str | None = Header(default=None),
) -> SessionResponse:
    client_origin = body.origin or origin or request.headers.get("referer") or "http://localhost:5173"
    client_ip = request.client.host if request.client else None
    client_ua = request.headers.get("user-agent")

    return create_auth_session(
        db=db,
        request=body,
        client_origin=client_origin,
        client_user_agent=client_ua,
        client_ip=client_ip,
    )


@router.get(
    "/sessions/{session_token}",
    response_model=SessionStatusResponse,
    summary="Get status of an authentication or enrollment session",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found."},
    },
)
def get_session(
    session_token: str,
    db: Session = Depends(get_db),
) -> SessionStatusResponse:
    return get_auth_session_status(db=db, session_token=session_token)


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


@router.post(
    "/devices/{device_id}/revoke",
    response_model=DeviceResponse,
    summary="Revoke an enrolled authenticator device",
    responses={
        404: {"model": ErrorResponse, "description": "Device not found."},
    },
)
def revoke_enrolled_device(
    device_id: str,
    body: DeviceRevokeRequest | None = None,
    db: Session = Depends(get_db),
) -> DeviceResponse:
    return revoke_device(db=db, device_id=device_id)


@router.get(
    "/devices",
    response_model=list[DeviceResponse],
    summary="List all enrolled devices",
)
def get_all_devices(
    db: Session = Depends(get_db),
) -> list[DeviceResponse]:
    return list_devices(db=db)
