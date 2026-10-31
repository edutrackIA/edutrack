"""model events

Records who trained or activated each model version.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-03 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("action", sa.Enum("TRAINED", "ACTIVATED", name="model_action"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_events_version", "model_events", ["version"])


def downgrade() -> None:
    op.drop_index("ix_model_events_version", table_name="model_events")
    op.drop_table("model_events")
