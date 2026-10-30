"""student enrollment status

Records whether a student is still enrolled, withdrew, transferred or graduated, with
the date and reason. Withdrawals are the real outcome the risk model learns from.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-02 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUSES = ("ENROLLED", "WITHDRAWN", "TRANSFERRED", "GRADUATED")
REASONS = (
    "TRANSFER",
    "WORK",
    "ECONOMIC",
    "FAMILY",
    "HEALTH",
    "PREGNANCY",
    "DISTANCE",
    "DISENGAGEMENT",
    "UNKNOWN",
    "GRADUATION",
)


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column(
            "status",
            sa.Enum(*STATUSES, name="student_status"),
            nullable=False,
            server_default="ENROLLED",
        ),
    )
    op.add_column("students", sa.Column("exit_date", sa.Date(), nullable=True))
    op.add_column(
        "students", sa.Column("exit_reason", sa.Enum(*REASONS, name="exit_reason"), nullable=True)
    )
    op.add_column("students", sa.Column("exit_note", sa.String(length=500), nullable=True))
    op.create_index("ix_students_status", "students", ["status"])


def downgrade() -> None:
    op.drop_index("ix_students_status", table_name="students")
    op.drop_column("students", "exit_note")
    op.drop_column("students", "exit_reason")
    op.drop_column("students", "exit_date")
    op.drop_column("students", "status")
