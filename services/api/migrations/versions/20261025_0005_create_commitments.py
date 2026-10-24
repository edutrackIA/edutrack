"""create commitments

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-25 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commitments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("tutor_id", sa.BigInteger(), nullable=False),
        sa.Column("guardian_id", sa.BigInteger(), nullable=False),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("agreements", sa.Text(), nullable=False),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "FULFILLED", "BREACHED", name="commitment_status"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tutor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["guardian_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commitments_student_id", "commitments", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_commitments_student_id", table_name="commitments")
    op.drop_table("commitments")
