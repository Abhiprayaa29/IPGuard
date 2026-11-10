"""Append-only audit chain metadata and events."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    event,
    ForeignKey,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditChainHead(Base):
    __tablename__ = "audit_chain_heads"

    chain_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    last_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        UniqueConstraint("chain_id", "sequence", name="uq_audit_events_chain_sequence"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chain_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("audit_chain_heads.chain_id", ondelete="RESTRICT"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    # Keep the exact canonical UTF-8 payload bytes; verifier hashes these bytes
    # directly and never reconstructs them from a database JSON value.
    canonical_payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)


@event.listens_for(AuditEvent, "before_update")
def _reject_audit_event_update(_mapper, _connection, _target) -> None:
    raise RuntimeError("Audit events are append-only and cannot be updated.")


@event.listens_for(AuditEvent, "before_delete")
def _reject_audit_event_delete(_mapper, _connection, _target) -> None:
    raise RuntimeError("Audit events are append-only and cannot be deleted.")
