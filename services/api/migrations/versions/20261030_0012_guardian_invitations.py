"""guardian invitations

Adds invitation links, lets invited users exist without a password until they accept,
and allows importing guardians.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-30 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_KINDS = sa.Enum("STUDENTS", "GRADES", "ATTENDANCE", name="import_kind")
NEW_KINDS = sa.Enum("STUDENTS", "GRADES", "ATTENDANCE", "GUARDIANS", name="import_kind")


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_invitations_user_id", "invitations", ["user_id"])
    op.alter_column(
        "users", "password_hash", existing_type=sa.String(length=255), nullable=True
    )
    op.alter_column(
        "import_jobs", "kind", existing_type=OLD_KINDS, type_=NEW_KINDS, existing_nullable=False
    )


def downgrade() -> None:
    op.execute("DELETE FROM import_jobs WHERE kind = 'GUARDIANS'")
    op.alter_column(
        "import_jobs", "kind", existing_type=NEW_KINDS, type_=OLD_KINDS, existing_nullable=False
    )
    op.execute("DELETE FROM users WHERE password_hash IS NULL")
    op.alter_column(
        "users", "password_hash", existing_type=sa.String(length=255), nullable=False
    )
    op.drop_index("ix_invitations_user_id", table_name="invitations")
    op.drop_table("invitations")
