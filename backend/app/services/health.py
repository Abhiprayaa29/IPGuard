import logging
from time import perf_counter

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.schemas.common import DatabaseHealthResponse

logger = logging.getLogger(__name__)


def check_database_connection(db: Session) -> DatabaseHealthResponse:
    started_at = perf_counter()
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning(
            "Database health check failed (%s)",
            type(exc).__name__,
        )
        raise AppError(
            status_code=503,
            code="database_unavailable",
            message="PostgreSQL is unavailable.",
        ) from exc

    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    return DatabaseHealthResponse(
        status="ok",
        database="postgresql",
        latency_ms=latency_ms,
    )
