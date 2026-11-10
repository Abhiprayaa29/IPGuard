"""add asset integrity check metadata

Revision ID: 0007_asset_integrity_metadata
Revises: 0006_asset_vault
Create Date: 2026-11-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_asset_integrity_metadata"
down_revision: str | Sequence[str] | None = "0006_asset_vault"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column(
            "integrity_status",
            sa.String(length=16),
            server_default="PENDING",
            nullable=False,
        ),
    )
    op.add_column(
        "assets",
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "assets",
        sa.Column("last_observed_sha256", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assets", "last_observed_sha256")
    op.drop_column("assets", "last_checked_at")
    op.drop_column("assets", "integrity_status")
