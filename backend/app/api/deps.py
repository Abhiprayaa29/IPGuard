"""
IPGuard API Dependencies — Authentication and Authorization Guards.
Integrates directly with Milestone 2 Hardware-Backed QR Authenticator sessions.
"""

from datetime import datetime, timezone
import re
from fastapi import Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.db.session import get_db
from app.models.auth import AuthSession, Device

HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")
IPGUARD_SESS_PREFIX = "ipguard_sess_"


def get_current_authenticated_device(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Device:
    """
    Authenticate request using Milestone 2 Hardware-Backed Session Access Token.
    1. Validates Authorization header with Bearer token format.
    2. Matches against auth_sessions table (supporting 64-hex session_token and ipguard_sess_ prefix).
    3. Enforces session status APPROVED (biometric/Keystore verified by mobile device).
    4. Enforces session expiration bounds (expires_at > current UTC time).
    5. Enforces enrolled device status ACTIVE (fails closed if revoked).
    Returns the verified Device model.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            message="Valid Authorization header with Bearer token is required.",
        )

    raw_token = authorization.removeprefix("Bearer ").strip()
    if not raw_token:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            message="Session access token is missing.",
        )

    # Normalize token candidate (strip ipguard_sess_ if present)
    if raw_token.startswith(IPGUARD_SESS_PREFIX):
        token_candidate = raw_token.removeprefix(IPGUARD_SESS_PREFIX).strip()
    else:
        token_candidate = raw_token

    if not token_candidate or not HEX_PATTERN.match(token_candidate):
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token_format",
            message="Session token must be a valid hexadecimal string.",
        )

    # 1. Exact match lookup on full 64-character session_token
    stmt = (
        select(AuthSession)
        .options(selectinload(AuthSession.device))
        .where(AuthSession.session_token == token_candidate)
    )
    auth_sess = db.scalar(stmt)

    # 2. Safe prefix lookup if token is a 24-character prefix (from M2 access_token generation)
    if not auth_sess and len(token_candidate) == 24:
        prefix_stmt = (
            select(AuthSession)
            .options(selectinload(AuthSession.device))
            .where(AuthSession.session_token.startswith(token_candidate))
        )
        matching_sessions = db.scalars(prefix_stmt).all()
        if len(matching_sessions) == 1:
            auth_sess = matching_sessions[0]
        elif len(matching_sessions) > 1:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="ambiguous_session_token",
                message="Session token prefix is ambiguous. Re-authentication required.",
            )

    if not auth_sess:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_session",
            message="Authentication session not found.",
        )

    # 3. Enforce APPROVED status
    if auth_sess.status != "APPROVED":
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="session_not_approved",
            message=f"Session status is '{auth_sess.status}'. Authentication must be APPROVED by mobile device.",
        )

    # 4. Enforce expiration bounds
    now = datetime.now(timezone.utc)
    if auth_sess.expires_at and now > auth_sess.expires_at:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="session_expired",
            message="Authentication session has expired. Please sign in again.",
        )

    # 5. Enforce bound device existence
    if not auth_sess.device:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unbound_device",
            message="Session is not bound to a registered hardware authenticator device.",
        )

    # 6. Enforce device ACTIVE status (fail closed on revoked devices)
    if auth_sess.device.status != "ACTIVE":
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="device_revoked",
            message=f"Authenticator device '{auth_sess.device.device_name}' is revoked.",
        )

    return auth_sess.device


def get_current_owner_id(
    device: Device = Depends(get_current_authenticated_device),
) -> str:
    """Extract persistent owner_id (device_id) from verified hardware authenticator."""
    return str(device.device_id)
