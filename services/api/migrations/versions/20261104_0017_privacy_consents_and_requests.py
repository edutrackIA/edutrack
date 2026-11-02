"""privacy consents and data subject requests

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-04 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "privacy_consents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("notice_version", sa.String(length=20), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "notice_version"),
    )
    op.create_index("ix_privacy_consents_user_id", "privacy_consents", ["user_id"])
    op.create_table(
        "data_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.BigInteger(), nullable=False),
        sa.Column("requester_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "ACCESS", "RECTIFICATION", "CANCELLATION", "OPPOSITION", name="data_request_kind"
            ),
            nullable=False,
        ),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RESOLVED", "REJECTED", name="data_request_status"),
            nullable=False,
        ),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_requests_student_id", "data_requests", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_data_requests_student_id", table_name="data_requests")
    op.drop_table("data_requests")
    op.drop_index("ix_privacy_consents_user_id", table_name="privacy_consents")
    op.drop_table("privacy_consents")
