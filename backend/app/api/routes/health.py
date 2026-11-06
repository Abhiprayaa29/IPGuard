from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.common import (
    DatabaseHealthResponse,
    ErrorResponse,
    HealthResponse,
)
from app.services.health import check_database_connection

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API service health",
)
def get_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="ipguard-api",
        version=settings.app_version,
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    summary="Check PostgreSQL connectivity",
    responses={
        503: {
            "model": ErrorResponse,
            "description": "PostgreSQL is unavailable.",
        }
    },
)
def get_database_health(
    db: Session = Depends(get_db),
) -> DatabaseHealthResponse:
    return check_database_connection(db)
