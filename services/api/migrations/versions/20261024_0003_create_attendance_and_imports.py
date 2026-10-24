"""create attendance and import jobs

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24 18:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PRESENT", "ABSENT", "LATE", "JUSTIFIED", name="attendance_status"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "date"),
    )
    op.create_index("ix_attendance_student_id", "attendance", ["student_id"])
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind", sa.Enum("STUDENTS", "GRADES", "ATTENDANCE", name="import_kind"), nullable=False
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.Enum("PENDING", "DONE", "FAILED", name="import_status"), nullable=False
        ),
        sa.Column("rows_ok", sa.Integer(), nullable=False),
        sa.Column("rows_failed", sa.Integer(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("import_jobs")
    op.drop_index("ix_attendance_student_id", table_name="attendance")
    op.drop_table("attendance")
