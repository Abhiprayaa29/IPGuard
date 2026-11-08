"""secure notes

Revision ID: 0004_secure_notes
Revises: 0003_auth_browser_channel
Create Date: 2026-11-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_secure_notes"
down_revision = "0003_auth_browser_channel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("title_enc", sa.Text(), nullable=False),
        sa.Column("content_enc", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notes")),
    )
    op.create_index(op.f("ix_notes_owner_id"), "notes", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notes_owner_id"), table_name="notes")
    op.drop_table("notes")
