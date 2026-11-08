"""add asset vault table for encrypted digital assets

Revision ID: 0006_asset_vault
Revises: 0005_device_unregistered_status
Create Date: 2026-11-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '0006_asset_vault'
down_revision: str | Sequence[str] | None = '0005_device_unregistered_status'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'assets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('device_id', sa.String(length=64), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=100), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('nonce', sa.String(length=64), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('encryption_version', sa.String(length=10), server_default='v1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.device_id'], name=op.f('fk_assets_device_id_devices'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_assets')),
        sa.UniqueConstraint('storage_key', name=op.f('uq_assets_storage_key')),
    )
    op.create_index(op.f('ix_assets_device_id'), 'assets', ['device_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_assets_device_id'), table_name='assets')
    op.drop_table('assets')
