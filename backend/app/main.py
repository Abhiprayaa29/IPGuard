from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce production security constraints during startup (fail-closed)
    if settings.app_env == "production":
        _ = settings.notes_master_key_bytes
        _ = settings.asset_vault_master_key_bytes
        _ = settings.effective_account_recovery_key
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    description="Local API foundation for IPGuard system readiness checks.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
