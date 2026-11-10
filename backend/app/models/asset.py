import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Asset(Base):
    """
    Asset Vault entity.
    Stores encrypted digital asset metadata.
    Binary files are stored as XChaCha20-Poly1305 ciphertext in the storage directory.
    """

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    device_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    content_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    nonce: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    integrity_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_observed_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    derivative_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    watermark_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    stego_format_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    encryption_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="v1",
        server_default="v1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    device = relationship("Device", backref="assets", foreign_keys=[device_id])
    source_asset = relationship(
        "Asset",
        remote_side=[id],
        foreign_keys=[source_asset_id],
        back_populates="derivatives",
    )
    derivatives = relationship(
        "Asset",
        foreign_keys=[source_asset_id],
        back_populates="source_asset",
        passive_deletes="all",
    )
