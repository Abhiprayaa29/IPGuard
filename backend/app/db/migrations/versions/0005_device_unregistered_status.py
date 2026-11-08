"""add unregistered_at to devices for one-time enrollment lifecycle

Revision ID: 0005_device_unregistered_status
Revises: 0004_secure_notes
Create Date: 2026-11-08
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa


revision: str = '0005_device_unregistered_status'
down_revision: str | Sequence[str] | None = '0004_secure_notes'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'devices',
        sa.Column('unregistered_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('devices', 'unregistered_at')
