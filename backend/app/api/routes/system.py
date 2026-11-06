from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import SystemInfoResponse

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
