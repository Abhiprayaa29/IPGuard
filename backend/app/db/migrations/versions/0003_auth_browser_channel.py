"""add browser_channel_token_hash to auth_sessions

Revision ID: 0003_auth_browser_channel
Revises: 0002_devices_and_auth_sessions
Create Date: 2026-11-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '0003_auth_browser_channel'
down_revision: str | Sequence[str] | None = '0002_devices_and_auth_sessions'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'auth_sessions',
        sa.Column('browser_channel_token_hash', sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f('ix_auth_sessions_browser_channel_token_hash'),
        'auth_sessions',
        ['browser_channel_token_hash'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_auth_sessions_browser_channel_token_hash'),
        table_name='auth_sessions',
    )
    op.drop_column('auth_sessions', 'browser_channel_token_hash')
