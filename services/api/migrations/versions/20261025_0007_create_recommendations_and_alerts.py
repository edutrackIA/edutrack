"""create recommendations and alerts

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-25 20:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("assessment_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("period_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING_REVIEW", "APPROVED", "DISCARDED", name="recommendation_status"),
            nullable=False,
        ),
        sa.Column("parent_items", sa.JSON(), nullable=False),
        sa.Column("teacher_items", sa.JSON(), nullable=False),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["risk_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["academic_periods.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id"),
    )
    op.create_index("ix_recommendations_student_id", "recommendations", ["student_id"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("assessment_id", sa.BigInteger(), nullable=False),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["risk_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "recipient_id"),
    )
    op.create_index("ix_alerts_recipient_id", "alerts", ["recipient_id"])


def downgrade() -> None:
    op.drop_index("ix_alerts_recipient_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_recommendations_student_id", table_name="recommendations")
    op.drop_table("recommendations")
