"""create append-only audit hash chains

Revision ID: 0008_audit_hash_chain
Revises: 0007_asset_integrity_metadata
Create Date: 2026-11-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_audit_hash_chain"
down_revision: str | Sequence[str] | None = "0007_asset_integrity_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GENESIS_HASH = "0" * 64


def upgrade() -> None:
    op.create_table(
        "audit_chain_heads",
        sa.Column("chain_id", sa.String(length=64), nullable=False),
        sa.Column("last_sequence", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("last_hash", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("chain_id", name=op.f("pk_audit_chain_heads")),
    )
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("chain_id", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("actor_device_id", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("canonical_payload", sa.LargeBinary(), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["chain_id"],
            ["audit_chain_heads.chain_id"],
            name=op.f("fk_audit_events_chain_id_audit_chain_heads"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk_audit_events")),
        sa.UniqueConstraint(
            "chain_id", "sequence", name="uq_audit_events_chain_sequence"
        ),
    )

    # Seed existing device chains. New devices acquire a genesis head lazily on
    # their first append, inside that append's transaction.
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO audit_chain_heads (chain_id, last_sequence, last_hash) "
            "SELECT device_id, 0, :genesis_hash FROM devices"
        ),
        {"genesis_hash": GENESIS_HASH},
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("audit_chain_heads")
