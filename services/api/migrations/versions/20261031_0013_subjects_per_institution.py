"""subjects belong to an institution

Until now course names were shared by every school. Each school now manages its own
list, so two schools can both have "Matemática" without clashing.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-31 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("subjects", sa.Column("institution_id", sa.BigInteger(), nullable=True))
    # Existing courses go to the first school (the only one before this change).
    op.execute("UPDATE subjects SET institution_id = (SELECT MIN(id) FROM institutions)")
    op.alter_column("subjects", "institution_id", existing_type=sa.BigInteger(), nullable=False)
    op.create_foreign_key(
        "fk_subjects_institution", "subjects", "institutions", ["institution_id"], ["id"]
    )
    op.drop_constraint("name", "subjects", type_="unique")
    op.create_unique_constraint(
        "uq_subjects_institution_name", "subjects", ["institution_id", "name"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_subjects_institution_name", "subjects", type_="unique")
    op.create_unique_constraint("name", "subjects", ["name"])
    op.drop_constraint("fk_subjects_institution", "subjects", type_="foreignkey")
    op.drop_column("subjects", "institution_id")
