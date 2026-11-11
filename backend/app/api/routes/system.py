import secrets

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.asset import Asset
from app.models.audit import AuditEvent
from app.models.auth import DEFAULT_ACCOUNT_ID, Device
from app.models.note import Note
from app.schemas.common import AuditEventSummary, SystemInfoResponse, SystemOverviewResponse
from app.services.health import check_database_connection

router = APIRouter()


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="Get non-sensitive application information",
)
def get_system_info() -> SystemInfoResponse:
    settings = get_settings()
    return SystemInfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        api_version="v1",
        database_engine="postgresql",
    )


@router.get(
    "/overview",
    response_model=SystemOverviewResponse,
    summary="Get real-time security posture overview backed by PostgreSQL state",
)
def get_system_overview(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_dev_admin_key: str | None = Header(default=None, alias="X-Dev-Admin-Key"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SystemOverviewResponse:
    database_status = "ok"
    latency_ms: float | None = None
    warnings: list[str] = []

    try:
        db_health = check_database_connection(db)
        database_status = db_health.status
        latency_ms = db_health.latency_ms
    except AppError:
        database_status = "unavailable"
        warnings.append("PostgreSQL connectivity is currently unavailable.")

    authenticated = False
    account_id = DEFAULT_ACCOUNT_ID
    caller_device: Device | None = None

    if authorization and authorization.startswith("Bearer "):
        try:
            caller_device = get_current_authenticated_device(authorization=authorization, db=db)
            authenticated = True
            account_id = caller_device.account_id
        except AppError:
            authenticated = False

    has_dev_admin = (
        settings.app_env != "production"
        and bool(x_dev_admin_key)
        and secrets.compare_digest(x_dev_admin_key or "", settings.dev_admin_key)
    )

    current_device: Device | None = None
    if database_status == "ok" and (authenticated or has_dev_admin or settings.app_env != "production"):
        current_device = db.scalar(
            select(Device)
            .where(
                Device.account_id == account_id,
                Device.status.in_(("ACTIVE", "REVOKED")),
            )
            .order_by(Device.enrolled_at.desc())
        )

    notes_count: int | None = None
    assets_count: int | None = None
    verified_assets_count: int | None = None
    recent_events: list[AuditEventSummary] = []

    if database_status == "ok" and authenticated and caller_device is not None:
        notes_count = int(
            db.scalar(
                select(func.count()).select_from(Note).where(Note.owner_id == caller_device.device_id)
            )
            or 0
        )
        assets_count = int(
            db.scalar(
                select(func.count()).select_from(Asset).where(Asset.device_id == caller_device.device_id)
            )
            or 0
        )
        verified_assets_count = int(
            db.scalar(
                select(func.count())
                .select_from(Asset)
                .where(
                    Asset.device_id == caller_device.device_id,
                    Asset.integrity_status == "VERIFIED",
                )
            )
            or 0
        )
        compromised_assets = int(
            db.scalar(
                select(func.count())
                .select_from(Asset)
                .where(
                    Asset.device_id == caller_device.device_id,
                    Asset.integrity_status == "COMPROMISED",
                )
            )
            or 0
        )
        if compromised_assets > 0:
            warnings.append(f"{compromised_assets} asset(s) reported COMPROMISED integrity status.")

        events = db.scalars(
            select(AuditEvent)
            .where(AuditEvent.chain_id == caller_device.device_id)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(8)
        ).all()
        recent_events = [
            AuditEventSummary(
                event_id=str(e.event_id),
                chain_id=e.chain_id,
                sequence=e.sequence,
                occurred_at=e.occurred_at,
                actor_type=e.actor_type,
                event_type=e.event_type,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                result=e.result,
                event_hash=e.event_hash,
            )
            for e in events
        ]
    elif database_status == "ok" and current_device is not None and (has_dev_admin or settings.app_env != "production"):
        events = db.scalars(
            select(AuditEvent)
            .where(AuditEvent.chain_id == current_device.device_id)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(8)
        ).all()
        recent_events = [
            AuditEventSummary(
                event_id=str(e.event_id),
                chain_id=e.chain_id,
                sequence=e.sequence,
                occurred_at=e.occurred_at,
                actor_type=e.actor_type,
                event_type=e.event_type,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                result=e.result,
                event_hash=e.event_hash,
            )
            for e in events
        ]

    if current_device is None:
        current_status = "UNREGISTERED"
        warnings.append("No hardware authenticator is currently bound to this account.")
    else:
        current_status = current_device.status
        if current_device.status == "REVOKED":
            warnings.append(
                f"Registered device '{current_device.device_name}' access is REVOKED. Sign-ins are blocked until restored or unregistered."
            )

    return SystemOverviewResponse(
        account_id=account_id,
        authenticated=authenticated,
        environment=settings.app_env,
        api_status="ok",
        database_status=database_status,
        database_latency_ms=latency_ms,
        registered_slots=1 if current_device is not None else 0,
        max_slots=1,
        current_device_id=current_device.device_id if current_device else None,
        current_device_name=current_device.device_name if current_device else None,
        current_device_status=current_status,
        notes_count=notes_count,
        assets_count=assets_count,
        verified_assets_count=verified_assets_count,
        warnings=warnings,
        recent_events=recent_events,
    )
