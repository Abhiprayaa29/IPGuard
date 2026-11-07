from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

settings = get_settings()

app = FastAPI(
    title=f"{settings.app_name} API",
    description="Local API foundation for IPGuard system readiness checks.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type", "Origin", "User-Agent"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
