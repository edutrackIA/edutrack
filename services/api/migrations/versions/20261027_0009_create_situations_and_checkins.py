"""create student situations and weekly check-ins

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-27 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SITUATION_KINDS = (
    "GRIEF",
    "HEALTH",
    "RELOCATION",
    "ECONOMIC_HARDSHIP",
    "PSYCHOLOGY_FOLLOW_UP",
    "PARENTS_SEPARATION",
    "PARENTS_AWAY",
    "HOME_RESPONSIBILITIES",
    "MIGRANT",
    "SPECIAL_NEEDS",
    "HIGH_ACHIEVER",
    "BULLYING",
    "PREGNANCY",
    "FAMILY_VIOLENCE",
    "SUBSTANCE_USE",
    "OTHER",
)


def upgrade() -> None:
    op.create_table(
        "student_situations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.Enum(*SITUATION_KINDS, name="situation_kind"), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column("resolved_on", sa.Date(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_situations_student_id", "student_situations", ["student_id"])
    op.create_table(
        "situation_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("situation_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "action",
            sa.Enum("CREATED", "UPDATED", "RESOLVED", "REOPENED", name="situation_action"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["situation_id"], ["student_situations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_situation_events_situation_id", "situation_events", ["situation_id"])
    op.create_table(
        "weekly_checkins",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("classroom_id", sa.BigInteger(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("completed_by", sa.BigInteger(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_id", "week_start"),
    )


def downgrade() -> None:
    op.drop_table("weekly_checkins")
    op.drop_index("ix_situation_events_situation_id", table_name="situation_events")
    op.drop_table("situation_events")
    op.drop_index("ix_student_situations_student_id", table_name="student_situations")
    op.drop_table("student_situations")
