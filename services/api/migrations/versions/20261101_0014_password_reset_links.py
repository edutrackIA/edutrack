"""password reset links

Invitation links gain a purpose so the same one-time token mechanism also serves
"forgot my password" links, which expire much sooner.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-01 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "invitations",
        sa.Column(
            "purpose",
            sa.Enum("INVITATION", "PASSWORD_RESET", name="token_purpose"),
            nullable=False,
            server_default="INVITATION",
        ),
    )


def downgrade() -> None:
    op.execute("DELETE FROM invitations WHERE purpose = 'PASSWORD_RESET'")
    op.drop_column("invitations", "purpose")
