"""create family surveys

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-24 21:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "family_surveys",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("period_id", sa.BigInteger(), nullable=False),
        sa.Column("responder_id", sa.BigInteger(), nullable=False),
        sa.Column("study_hours_week", sa.SmallInteger(), nullable=False),
        sa.Column(
            "parent_education",
            sa.Enum(
                "NONE", "PRIMARY", "SECONDARY", "TECHNICAL", "UNIVERSITY", name="parent_education"
            ),
            nullable=False,
        ),
        sa.Column("home_internet", sa.Boolean(), nullable=False),
        sa.Column("has_study_device", sa.Boolean(), nullable=False),
        sa.Column("family_communication", sa.SmallInteger(), nullable=False),
        sa.Column("student_works", sa.Boolean(), nullable=False),
        sa.Column("household_size", sa.SmallInteger(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["academic_periods.id"]),
        sa.ForeignKeyConstraint(["responder_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "period_id"),
    )
    op.create_index("ix_family_surveys_student_id", "family_surveys", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_family_surveys_student_id", table_name="family_surveys")
    op.drop_table("family_surveys")
