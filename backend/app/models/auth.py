import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

DEFAULT_ACCOUNT_ID = "ipguard-primary"


def _fallback_isolated_account_id() -> str:
    return f"acct-{uuid.uuid4().hex[:16]}"


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="IPGuard Primary Account",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        Index(
            "uq_devices_one_registered_per_account",
            "account_id",
            unique=True,
            postgresql_where=text("status IN ('ACTIVE', 'REVOKED')"),
            sqlite_where=text("status IN ('ACTIVE', 'REVOKED')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=_fallback_isolated_account_id,
        index=True,
    )
    device_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    device_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    android_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    public_key_x509: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    public_key_fingerprint: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )
    security_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="TRUSTED_ENVIRONMENT",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    unregistered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    auth_sessions: Mapped[list["AuthSession"]] = relationship(
        "AuthSession",
        back_populates="device",
        cascade="all, delete-orphan",
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=DEFAULT_ACCOUNT_ID,
        index=True,
    )
    session_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    challenge_nonce: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    session_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="AUTHENTICATION",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )
    client_origin: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    client_user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    client_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    browser_channel_token_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    signature: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    canonical_payload: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    device: Mapped[Device | None] = relationship(
        "Device",
        back_populates="auth_sessions",
    )
