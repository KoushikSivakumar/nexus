"""initial repository table

Revision ID: 202609050001
Revises:
Create Date: 2026-09-05 00:01:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202609050001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
    )
    op.create_index(op.f("ix_repositories_external_id"), "repositories", ["external_id"])
    op.create_index(op.f("ix_repositories_id"), "repositories", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_external_id"), table_name="repositories")
    op.drop_table("repositories")
