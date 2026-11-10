"""PostgreSQL row-lock integration test, opt-in to a disposable test database."""

from concurrent.futures import ThreadPoolExecutor
import os

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.models.audit import AuditEvent
from app.services.audit_chain import append_audit_event, verify_audit_chain


@pytest.fixture
def postgres_audit_factory():
    database_url = os.getenv("IPGUARD_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("Set IPGUARD_TEST_POSTGRES_URL to a disposable *_ipguard_test database.")
    parsed_url = make_url(database_url)
    if not parsed_url.drivername.startswith("postgresql") or not (
        parsed_url.database and parsed_url.database.lower().endswith("_ipguard_test")
    ):
        pytest.fail("Refusing PostgreSQL audit tests outside a database ending in _ipguard_test.")

    engine = create_engine(database_url, pool_pre_ping=True, pool_size=12, max_overflow=0)
    # Explicit opt-in plus the database-name guard confines DDL to a disposable test DB.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_parallel_appends_serialize_on_postgres_chain_head(postgres_audit_factory):
    factory = postgres_audit_factory
    chain_id = "postgres-audit-concurrency-device"

    def append_one(index: int) -> None:
        with factory.begin() as db:
            append_audit_event(
                db,
                chain_id=chain_id,
                actor_type="SYSTEM",
                event_type="INTEGRITY_CHECK_PASSED",
                resource_type="asset",
                resource_id=f"asset-{index}",
                result="VERIFIED",
                payload={"integrity_status": "VERIFIED", "ordinal": index},
            )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(append_one, range(24)))

    with factory() as db:
        events = list(
            db.scalars(
                select(AuditEvent)
                .where(AuditEvent.chain_id == chain_id)
                .order_by(AuditEvent.sequence)
            ).all()
        )
        result = verify_audit_chain(db, chain_id)

    assert [event.sequence for event in events] == list(range(1, 25))
    assert result.valid is True
    assert result.event_count == 24
