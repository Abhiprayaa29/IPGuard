"""Add audit_blockchain_anchors table for M5 batch audit anchoring.

Revision ID: 0011_audit_blockchain_anchors
Revises: 0010_account_device_lifecycle
Create Date: 2026-11-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011_audit_blockchain_anchors"
down_revision: str | Sequence[str] | None = "0010_account_device_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_blockchain_anchors",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("audit_chain_id", sa.String(length=64), nullable=False),
        sa.Column("from_sequence", sa.BigInteger(), nullable=False),
        sa.Column("to_sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("merkle_root", sa.String(length=66), nullable=False),
        sa.Column("head_hash", sa.String(length=66), nullable=False),
        sa.Column("batch_reference", sa.String(length=160), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=False),
        sa.Column("chain_id", sa.BigInteger(), nullable=False),
        sa.Column("contract_address", sa.String(length=42), nullable=False),
        sa.Column("signer_address", sa.String(length=42), nullable=True),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("block_number", sa.BigInteger(), nullable=True),
        sa.Column("block_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "audit_chain_id",
            "from_sequence",
            "to_sequence",
            "network",
            "contract_address",
            name="uq_audit_blockchain_anchor_batch",
        ),
    )
    op.create_index(
        "ix_audit_blockchain_anchors_chain_status",
        "audit_blockchain_anchors",
        ["audit_chain_id", "status"],
    )
    op.create_index(
        "ix_audit_blockchain_anchors_tx_hash",
        "audit_blockchain_anchors",
        ["tx_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_blockchain_anchors_tx_hash", table_name="audit_blockchain_anchors")
    op.drop_index("ix_audit_blockchain_anchors_chain_status", table_name="audit_blockchain_anchors")
    op.drop_table("audit_blockchain_anchors")
