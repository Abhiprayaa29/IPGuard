from time import perf_counter

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.services.health import check_database_connection


def test_unreachable_database_fails_quickly_and_generically() -> None:
    engine = create_engine(
        "postgresql+psycopg://ipguard:local-test-only@127.0.0.1:1/ipguard",
        connect_args={"connect_timeout": 1},
    )

    started_at = perf_counter()
    with Session(engine) as session, pytest.raises(AppError) as error:
        check_database_connection(session)
    elapsed = perf_counter() - started_at

    assert error.value.status_code == 503
    assert error.value.code == "database_unavailable"
    assert error.value.message == "PostgreSQL is unavailable."
    assert elapsed < 5
