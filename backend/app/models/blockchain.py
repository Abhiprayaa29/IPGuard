"""PostgreSQL registry of M5 blockchain audit batch anchors."""

from datetime import datetime
import uuid

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditBlockchainAnchor(Base):
    __tablename__ = "audit_blockchain_anchors"
    __table_args__ = (
        UniqueConstraint(
            "audit_chain_id",
            "from_sequence",
            "to_sequence",
            "network",
            "contract_address",
            name="uq_audit_blockchain_anchor_batch",
        ),
        Index("ix_audit_blockchain_anchors_chain_status", "audit_chain_id", "status"),
        Index("ix_audit_blockchain_anchors_tx_hash", "tx_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_chain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    from_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    to_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    merkle_root: Mapped[str] = mapped_column(String(66), nullable=False)
    head_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    batch_reference: Mapped[str] = mapped_column(String(160), nullable=False)
    network: Mapped[str] = mapped_column(String(32), nullable=False)
    chain_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    contract_address: Mapped[str] = mapped_column(String(42), nullable=False)
    signer_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    block_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    block_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
