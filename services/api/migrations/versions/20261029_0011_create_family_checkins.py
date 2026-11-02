"""create family check-ins

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-29 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "family_checkins",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("guardian_id", sa.BigInteger(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("mood", sa.Enum("GOOD", "OK", "WORRIED", name="family_mood"), nullable=False),
        sa.Column("home_changes", sa.JSON(), nullable=False),
        sa.Column("peer_concern", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guardian_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "month"),
    )
    op.create_index("ix_family_checkins_student_id", "family_checkins", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_family_checkins_student_id", table_name="family_checkins")
    op.drop_table("family_checkins")
