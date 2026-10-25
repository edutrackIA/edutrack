"""create family messages and notification log

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-28 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "family_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "WEEKLY_ATTENDANCE",
                "PERFECT_ATTENDANCE",
                "PERIOD_GRADES",
                name="family_message_kind",
            ),
            nullable=False,
        ),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("SENT", "HELD", "FAILED", "DISCARDED", name="family_message_status"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("hold_reason", sa.String(length=200), nullable=True),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "kind", "reference_date"),
    )
    op.create_index("ix_family_messages_student_id", "family_messages", ["student_id"])
    op.create_table(
        "notification_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "recipient_id", "reference"),
    )


def downgrade() -> None:
    op.drop_table("notification_log")
    op.drop_index("ix_family_messages_student_id", table_name="family_messages")
    op.drop_table("family_messages")
