"""add PNG LSB derivative lineage metadata

Revision ID: 0009_png_lsb_derivatives
Revises: 0008_audit_hash_chain
Create Date: 2026-11-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_png_lsb_derivatives"
down_revision: str | Sequence[str] | None = "0008_audit_hash_chain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(sa.Column("source_asset_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("derivative_type", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("watermark_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("stego_format_version", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_assets_source_asset_id_assets",
            "assets",
            ["source_asset_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    op.create_index("ix_assets_source_asset_id", "assets", ["source_asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assets_source_asset_id", table_name="assets")
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_constraint("fk_assets_source_asset_id_assets", type_="foreignkey")
        batch_op.drop_column("stego_format_version")
        batch_op.drop_column("watermark_id")
        batch_op.drop_column("derivative_type")
        batch_op.drop_column("source_asset_id")
