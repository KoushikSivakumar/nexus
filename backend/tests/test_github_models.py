"""Metadata/introspection tests for the TASK 2 GitHub history models.

These tests inspect SQLAlchemy metadata only and do not require a live
PostgreSQL server or a database connection.
"""

import uuid

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import configure_mappers
from sqlalchemy.types import DateTime

from app import models as app_models
from app.db.base import Base
from app.models import (
    Commit,
    Deployment,
    Issue,
    PullRequest,
    PullRequestReview,
    Release,
    Repository,
    WorkFlowRun,
)

GITHUB_HISTORY_MODELS = [
    Commit,
    PullRequest,
    PullRequestReview,
    Issue,
    Release,
    WorkFlowRun,
    Deployment,
]
REPOSITORY_OWNED_MODELS = [Commit, PullRequest, Issue, Release, WorkFlowRun, Deployment]


@pytest.fixture(autouse=True)
def _configure_mappers() -> None:
    """Resolve all mappers/relationships so relationship introspection works."""
    configure_mappers()


def _pk_column(model) -> object:
    primary_key = model.__table__.primary_key
    assert len(primary_key.columns) == 1
    return next(iter(primary_key.columns))


def _find_unique_constraint(model, name: str) -> UniqueConstraint | None:
    for constraint in model.__table__.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.name == name:
            return constraint
    return None


def _find_index(model, name: str) -> object | None:
    for index in model.__table__.indexes:
        if index.name == name:
            return index
    return None


# ---------------------------------------------------------------------------
# Exports / registration
# ---------------------------------------------------------------------------


def test_models_are_exported_from_app_models() -> None:
    expected = [
        "Repository",
        "Commit",
        "PullRequest",
        "PullRequestReview",
        "Issue",
        "Release",
        "WorkFlowRun",
        "Deployment",
        "TimestampMixin",
        "UUIDPrimaryKeyMixin",
    ]
    for name in expected:
        assert name in app_models.__all__
        assert hasattr(app_models, name)


def test_all_tables_registered_in_base_metadata() -> None:
    expected_tables = {
        "repositories",
        "commits",
        "pull_requests",
        "pull_request_reviews",
        "issues",
        "releases",
        "workflow_runs",
        "deployments",
    }
    assert expected_tables.issubset(Base.metadata.tables)


@pytest.mark.parametrize("model", GITHUB_HISTORY_MODELS)
def test_history_model_table_registered(model) -> None:
    assert model.__table__ is Base.metadata.tables[model.__tablename__]


# ---------------------------------------------------------------------------
# Shared foundation: UUID PK + timestamp mixin
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", GITHUB_HISTORY_MODELS)
def test_history_model_uses_uuid_primary_key(model) -> None:
    pk = _pk_column(model)
    assert pk.name == "id"
    assert isinstance(pk.type, PostgreSQLUUID)
    assert pk.type.as_uuid is True
    assert pk.type.python_type is uuid.UUID
    assert pk.primary_key is True


@pytest.mark.parametrize("model", GITHUB_HISTORY_MODELS)
def test_history_model_uses_timestamp_mixin(model) -> None:
    for field in ("created_at", "updated_at"):
        column = model.__table__.c[field]
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True


# ---------------------------------------------------------------------------
# Foreign keys
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", REPOSITORY_OWNED_MODELS)
def test_repository_owned_model_has_repository_id_uuid_fk(model) -> None:
    column = model.__table__.c.repository_id
    assert isinstance(column.type, PostgreSQLUUID)
    assert column.type.as_uuid is True
    assert len(column.foreign_keys) == 1
    foreign_key = next(iter(column.foreign_keys))
    assert foreign_key.target_fullname == "repositories.id"
    assert column.nullable is False


def test_pull_request_review_has_pull_request_id_uuid_fk() -> None:
    column = PullRequestReview.__table__.c.pull_request_id
    assert isinstance(column.type, PostgreSQLUUID)
    assert column.type.as_uuid is True
    assert len(column.foreign_keys) == 1
    assert next(iter(column.foreign_keys)).target_fullname == "pull_requests.id"
    assert column.nullable is False
    assert "repository_id" not in PullRequestReview.__table__.c


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "attr,target",
    [
        ("commits", Commit),
        ("pull_requests", PullRequest),
        ("issues", Issue),
        ("releases", Release),
        ("workflow_runs", WorkFlowRun),
        ("deployments", Deployment),
    ],
)
def test_repository_collection_relationship(attr, target) -> None:
    relationship = Repository.__mapper__.relationships[attr]
    assert relationship.mapper.class_ is target
    assert relationship.uselist is True


@pytest.mark.parametrize("model", REPOSITORY_OWNED_MODELS)
def test_history_model_has_repository_back_relationship(model) -> None:
    relationship = model.__mapper__.relationships["repository"]
    assert relationship.mapper.class_ is Repository
    assert relationship.uselist is False


def test_pull_request_reviews_relationship() -> None:
    reviews = PullRequest.__mapper__.relationships["reviews"]
    assert reviews.mapper.class_ is PullRequestReview
    assert reviews.uselist is True

    pull_request = PullRequestReview.__mapper__.relationships["pull_request"]
    assert pull_request.mapper.class_ is PullRequest
    assert pull_request.uselist is False


# ---------------------------------------------------------------------------
# Domain fields / external identifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", GITHUB_HISTORY_MODELS)
def test_external_id_present_on_every_history_model(model) -> None:
    assert "external_id" in model.__table__.c


def test_commit_has_sha_and_commit_message() -> None:
    assert "sha" in Commit.__table__.c
    assert "message" in Commit.__table__.c


def test_pull_request_and_issue_have_number() -> None:
    assert "number" in PullRequest.__table__.c
    assert "number" in Issue.__table__.c


def test_release_has_tag_name() -> None:
    assert "tag_name" in Release.__table__.c


def test_workflow_run_has_run_number() -> None:
    assert "run_number" in WorkFlowRun.__table__.c


def test_github_timestamps_are_explicit_and_timezone_aware() -> None:
    for column in (
        Commit.__table__.c.committed_at,
        PullRequest.__table__.c.github_created_at,
        PullRequest.__table__.c.github_updated_at,
        PullRequest.__table__.c.merged_at,
        PullRequest.__table__.c.closed_at,
        PullRequestReview.__table__.c.submitted_at,
        Issue.__table__.c.github_created_at,
        Issue.__table__.c.github_updated_at,
        Release.__table__.c.published_at,
        WorkFlowRun.__table__.c.started_at,
        WorkFlowRun.__table__.c.completed_at,
        Deployment.__table__.c.github_created_at,
    ):
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True
# ---------------------------------------------------------------------------
# Uniqueness constraints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model,constraint_name,columns",
    [
        (Commit, "uq_commits_repository_id_external_id", ["repository_id", "external_id"]),
        (PullRequest, "uq_pull_requests_repository_id_external_id", ["repository_id", "external_id"]),
        (PullRequest, "uq_pull_requests_repository_id_number", ["repository_id", "number"]),
        (
            PullRequestReview,
            "uq_pull_request_reviews_pull_request_id_external_id",
            ["pull_request_id", "external_id"],
        ),
        (Issue, "uq_issues_repository_id_external_id", ["repository_id", "external_id"]),
        (Issue, "uq_issues_repository_id_number", ["repository_id", "number"]),
        (Release, "uq_releases_repository_id_external_id", ["repository_id", "external_id"]),
        (Release, "uq_releases_repository_id_tag_name", ["repository_id", "tag_name"]),
        (WorkFlowRun, "uq_workflow_runs_repository_id_external_id", ["repository_id", "external_id"]),
        (WorkFlowRun, "uq_workflow_runs_repository_id_run_number", ["repository_id", "run_number"]),
        (Deployment, "uq_deployments_repository_id_external_id", ["repository_id", "external_id"]),
    ],
)
def test_expected_unique_constraint_exists(model, constraint_name, columns) -> None:
    constraint = _find_unique_constraint(model, constraint_name)
    assert constraint is not None, f"missing unique constraint {constraint_name}"
    assert [column.name for column in constraint.columns] == columns


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model,index_name,columns",
    [
        (Commit, "ix_commits_repository_id_committed_at", ["repository_id", "committed_at"]),
        (
            PullRequest,
            "ix_pull_requests_repository_id_github_created_at",
            ["repository_id", "github_created_at"],
        ),
        (PullRequest, "ix_pull_requests_repository_id_state", ["repository_id", "state"]),
        (
            PullRequestReview,
            "ix_pull_request_reviews_pull_request_id_submitted_at",
            ["pull_request_id", "submitted_at"],
        ),
        (
            Issue,
            "ix_issues_repository_id_github_created_at",
            ["repository_id", "github_created_at"],
        ),
        (Issue, "ix_issues_repository_id_state", ["repository_id", "state"]),
        (Release, "ix_releases_repository_id_published_at", ["repository_id", "published_at"]),
        (WorkFlowRun, "ix_workflow_runs_repository_id_started_at", ["repository_id", "started_at"]),
        (WorkFlowRun, "ix_workflow_runs_repository_id_status", ["repository_id", "status"]),
        (
            Deployment,
            "ix_deployments_repository_id_environment",
            ["repository_id", "environment"],
        ),
        (
            Deployment,
            "ix_deployments_repository_id_github_created_at",
            ["repository_id", "github_created_at"],
        ),
    ],
)
def test_expected_index_exists(model, index_name, columns) -> None:
    index = _find_index(model, index_name)
    assert index is not None, f"missing index {index_name}"
    assert [column.name for column in index.columns] == columns