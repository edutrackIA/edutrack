"""create risk tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-25 15:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "risk_thresholds",
        sa.Column("institution_id", sa.BigInteger(), nullable=False),
        sa.Column("medium_from", sa.Float(), nullable=False),
        sa.Column("high_from", sa.Float(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("institution_id"),
    )
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("period_id", sa.BigInteger(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("level", sa.Enum("LOW", "MEDIUM", "HIGH", name="risk_level"), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("top_factors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["academic_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "period_id", "model_version"),
    )
    op.create_index("ix_risk_assessments_student_id", "risk_assessments", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_risk_assessments_student_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
    op.drop_table("risk_thresholds")
