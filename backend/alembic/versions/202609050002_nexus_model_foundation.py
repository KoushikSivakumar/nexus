"""NEXUS model foundation: UUID repositories and GitHub history tables

Revision ID: 202609050002
Revises: 202609050001
Create Date: 2026-09-05 00:02:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202609050002"
down_revision: str | Sequence[str] | None = "202609050001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace the old INTEGER-primary-key repositories schema with the current
    NEXUS model schema (UUID primary keys) and create the GitHub history tables.

    The preceding revision (202609050001) created ``repositories`` with an INTEGER
    primary key. PostgreSQL cannot transparently cast INTEGER values to UUIDs, and no
    data-migration strategy exists to map legacy rows into the UUID key space at this
    development stage. The old table has no dependent tables, so it is dropped and
    recreated with the UUID representation defined by the current models, and all
    GitHub history tables are created. Any rows previously stored under INTEGER primary
    keys would be dropped by this migration and must be re-ingested from GitHub later.
    """
    # ---------------------------------------------------------------------------
    # repositories: INTEGER primary key -> UUID primary key
    # ---------------------------------------------------------------------------
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_external_id"), table_name="repositories")
    op.drop_table("repositories")

    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
    )
    op.create_index(op.f("ix_repositories_external_id"), "repositories", ["external_id"])

    # ---------------------------------------------------------------------------
    # commits
    # ---------------------------------------------------------------------------
    op.create_table(
        "commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("sha", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("author_email", sa.String(length=255), nullable=False),
        sa.Column("committer_name", sa.String(length=255), nullable=False),
        sa.Column("committer_email", sa.String(length=255), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id", "external_id", name="uq_commits_repository_id_external_id"
        ),
    )
    op.create_index(
        "ix_commits_repository_id_committed_at",
        "commits",
        ["repository_id", "committed_at"],
    )
# ---------------------------------------------------------------------------
    # pull_requests
    # ---------------------------------------------------------------------------
    op.create_table(
        "pull_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("author_username", sa.String(length=255), nullable=False),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("github_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id",
            "external_id",
            name="uq_pull_requests_repository_id_external_id",
        ),
        sa.UniqueConstraint(
            "repository_id", "number", name="uq_pull_requests_repository_id_number"
        ),
    )
    op.create_index(
        "ix_pull_requests_repository_id_github_created_at",
        "pull_requests",
        ["repository_id", "github_created_at"],
    )
    op.create_index(
        "ix_pull_requests_repository_id_state",
        "pull_requests",
        ["repository_id", "state"],
    )

    # ---------------------------------------------------------------------------
    # pull_request_reviews
    # ---------------------------------------------------------------------------
    op.create_table(
        "pull_request_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "pull_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pull_requests.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("reviewer_username", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pull_request_id",
            "external_id",
            name="uq_pull_request_reviews_pull_request_id_external_id",
        ),
    )
    op.create_index(
        "ix_pull_request_reviews_pull_request_id_submitted_at",
        "pull_request_reviews",
        ["pull_request_id", "submitted_at"],
    )

    # ---------------------------------------------------------------------------
    # issues
    # ---------------------------------------------------------------------------
    op.create_table(
        "issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("author_username", sa.String(length=255), nullable=False),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("github_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id", "external_id", name="uq_issues_repository_id_external_id"
        ),
        sa.UniqueConstraint(
            "repository_id", "number", name="uq_issues_repository_id_number"
        ),
    )
    op.create_index(
        "ix_issues_repository_id_github_created_at",
        "issues",
        ["repository_id", "github_created_at"],
    )
    op.create_index(
        "ix_issues_repository_id_state",
        "issues",
        ["repository_id", "state"],
    )
# ---------------------------------------------------------------------------
    # releases
    # ---------------------------------------------------------------------------
    op.create_table(
        "releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("tag_name", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("author_username", sa.String(length=255), nullable=False),
        sa.Column("draft", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id", "external_id", name="uq_releases_repository_id_external_id"
        ),
        sa.UniqueConstraint(
            "repository_id", "tag_name", name="uq_releases_repository_id_tag_name"
        ),
    )
    op.create_index(
        "ix_releases_repository_id_published_at",
        "releases",
        ["repository_id", "published_at"],
    )

    # ---------------------------------------------------------------------------
    # workflow_runs
    # ---------------------------------------------------------------------------
    op.create_table(
        "workflow_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("workflow_name", sa.String(length=255), nullable=True),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("conclusion", sa.String(length=32), nullable=True),
        sa.Column("branch", sa.String(length=255), nullable=True),
        sa.Column("head_sha", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id",
            "external_id",
            name="uq_workflow_runs_repository_id_external_id",
        ),
        sa.UniqueConstraint(
            "repository_id",
            "run_number",
            name="uq_workflow_runs_repository_id_run_number",
        ),
    )
    op.create_index(
        "ix_workflow_runs_repository_id_started_at",
        "workflow_runs",
        ["repository_id", "started_at"],
    )
    op.create_index(
        "ix_workflow_runs_repository_id_status",
        "workflow_runs",
        ["repository_id", "status"],
    )

    # ---------------------------------------------------------------------------
    # deployments
    # ---------------------------------------------------------------------------
    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("environment", sa.String(length=255), nullable=True),
        sa.Column("ref", sa.String(length=255), nullable=False),
        sa.Column("creator_username", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id",
            "external_id",
            name="uq_deployments_repository_id_external_id",
        ),
    )
    op.create_index(
        "ix_deployments_repository_id_environment",
        "deployments",
        ["repository_id", "environment"],
    )
    op.create_index(
        "ix_deployments_repository_id_github_created_at",
        "deployments",
        ["repository_id", "github_created_at"],
    )


def downgrade() -> None:
    """Reverse the model-foundation migration: drop the GitHub history tables and the
    UUID-key ``repositories`` table, then restore the preceding revision's INTEGER-key
    ``repositories`` table exactly as defined by revision 202609050001.
    """
    # ---------------------------------------------------------------------------
    # Drop GitHub history tables in reverse foreign-key dependency order.
    # ---------------------------------------------------------------------------
    op.drop_table("pull_request_reviews")
    op.drop_table("deployments")
    op.drop_table("workflow_runs")
    op.drop_table("releases")
    op.drop_table("issues")
    op.drop_table("pull_requests")
    op.drop_table("commits")

    # ---------------------------------------------------------------------------
    # repositories: UUID primary key -> INTEGER primary key (previous revision).
    # ---------------------------------------------------------------------------
    op.drop_index(op.f("ix_repositories_external_id"), table_name="repositories")
    op.drop_table("repositories")

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