"""Add accounts table, account_id ownership, and single-registered-device partial index.

Revision ID: 0010_account_device_lifecycle
Revises: 0009_png_lsb_derivatives
Create Date: 2026-11-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_account_device_lifecycle"
down_revision: str | Sequence[str] | None = "0009_png_lsb_derivatives"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "display_name",
            sa.String(length=120),
            nullable=False,
            server_default="IPGuard Primary Account",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.add_column("devices", sa.Column("account_id", sa.String(length=64), nullable=True))
    op.add_column("auth_sessions", sa.Column("account_id", sa.String(length=64), nullable=True))

    conn = op.get_bind()

    # Ensure canonical primary account row exists
    conn.execute(
        sa.text(
            "INSERT INTO accounts (account_id, display_name) "
            "VALUES ('ipguard-primary', 'IPGuard Primary Account') "
            "ON CONFLICT (account_id) DO NOTHING"
        )
    )

    # Identify legacy devices deterministically:
    # Preserve every historical device row without data loss. Assign the newest real
    # Android client row (ipguard-dev-%) as the canonical primary account owner when active/revoked,
    # and assign isolated preserved legacy account IDs to test/other legacy rows so the
    # partial unique index never breaks pre-existing fixtures or historical data.
    primary_row = conn.execute(
        sa.text(
            "SELECT id FROM devices "
            "WHERE status IN ('ACTIVE', 'REVOKED') AND device_id LIKE 'ipguard-dev-%' "
            "ORDER BY enrolled_at DESC LIMIT 1"
        )
    ).fetchone()

    if primary_row:
        conn.execute(
            sa.text("UPDATE devices SET account_id = 'ipguard-primary' WHERE id = :id"),
            {"id": primary_row[0]},
        )

    remaining = conn.execute(
        sa.text("SELECT id, device_id FROM devices WHERE account_id IS NULL")
    ).fetchall()
    for row_id, dev_id in remaining:
        legacy_acct = f"legacy-{str(row_id)[:12]}"
        conn.execute(
            sa.text(
                "INSERT INTO accounts (account_id, display_name) "
                "VALUES (:acct, :name) ON CONFLICT (account_id) DO NOTHING"
            ),
            {"acct": legacy_acct, "name": f"Legacy Account ({dev_id[:24]})"},
        )
        conn.execute(
            sa.text("UPDATE devices SET account_id = :acct WHERE id = :id"),
            {"acct": legacy_acct, "id": row_id},
        )

    conn.execute(
        sa.text(
            "UPDATE auth_sessions SET account_id = 'ipguard-primary' WHERE account_id IS NULL"
        )
    )

    op.alter_column("devices", "account_id", existing_type=sa.String(length=64), nullable=False)
    op.alter_column(
        "auth_sessions", "account_id", existing_type=sa.String(length=64), nullable=False
    )

    op.create_index("ix_devices_account_id", "devices", ["account_id"], unique=False)
    op.create_index("ix_auth_sessions_account_id", "auth_sessions", ["account_id"], unique=False)
    op.create_index(
        "uq_devices_one_registered_per_account",
        "devices",
        ["account_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('ACTIVE', 'REVOKED')"),
    )


def downgrade() -> None:
    op.drop_index("uq_devices_one_registered_per_account", table_name="devices")
    op.drop_index("ix_auth_sessions_account_id", table_name="auth_sessions")
    op.drop_index("ix_devices_account_id", table_name="devices")
    op.drop_column("auth_sessions", "account_id")
    op.drop_column("devices", "account_id")
    op.drop_table("accounts")
