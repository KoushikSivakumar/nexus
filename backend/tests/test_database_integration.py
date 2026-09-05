"""Real PostgreSQL integration tests for the NEXUS database.

These tests exercise an actual PostgreSQL database (the dedicated ``nexus_test``
database, or whatever ``NEXUS_TEST_DATABASE_URL`` points at) and prove that the
SQLAlchemy models, the Alembic migration, the live PostgreSQL schema, and the
ORM behavior all agree with one another.

Bootstrap: the session-scoped ``db_engine`` fixture creates the database when
missing and runs ``alembic upgrade head`` before any test in this module.

Isolation: an autouse fixture truncates the eight application tables before and
after each test (controlled table cleanup -- ``alembic_version`` is never
touched, no database is ever dropped). Failed uniqueness / foreign-key
transactions are rolled back inside the tests and again by the ``db_session``
fixture teardown, so later tests are never poisoned.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

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
from db_helpers import APP_TABLES, EXPECTED_ALEMBIC_HEAD, truncate_all_tables

pytestmark = pytest.mark.integration

UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Row builders: minimal valid rows for each model.
# ---------------------------------------------------------------------------


def _repository(owner: str, name: str, external_id: str = "git-1") -> Repository:
    return Repository(owner=owner, name=name, external_id=external_id)


def _commit(repository_id: uuid.UUID, external_id: str, **kwargs) -> Commit:
    return Commit(
        repository_id=repository_id,
        external_id=external_id,
        sha=f"sha-{external_id}",
        message=f"Commit message for {external_id}",
        author_name="Alice",
        author_email="alice@example.com",
        committer_name="Bob",
        committer_email="bob@example.com",
        committed_at=_now(),
        **kwargs,
    )


def _pull_request(
    repository_id: uuid.UUID, external_id: str, number: int = 1, **kwargs
) -> PullRequest:
    return PullRequest(
        repository_id=repository_id,
        external_id=external_id,
        number=number,
        title=f"PR title {external_id}",
        body="PR body",
        state="open",
        author_username="alice",
        github_created_at=_now(),
        github_updated_at=_now(),
        **kwargs,
    )


def _pull_request_review(
    pull_request_id: uuid.UUID, external_id: str, **kwargs
) -> PullRequestReview:
    return PullRequestReview(
        pull_request_id=pull_request_id,
        external_id=external_id,
        reviewer_username="reviewer",
        state="approved",
        body="Looks good to me",
        submitted_at=_now(),
        **kwargs,
    )


def _issue(repository_id: uuid.UUID, external_id: str, number: int = 1, **kwargs) -> Issue:
    return Issue(
        repository_id=repository_id,
        external_id=external_id,
        number=number,
        title=f"Issue title {external_id}",
        body="Issue body",
        state="open",
        author_username="alice",
        github_created_at=_now(),
        github_updated_at=_now(),
        **kwargs,
    )


def _release(
    repository_id: uuid.UUID, external_id: str, tag_name: str = "v1.0.0", **kwargs
) -> Release:
    return Release(
        repository_id=repository_id,
        external_id=external_id,
        tag_name=tag_name,
        name=f"Release {external_id}",
        body="Release notes",
        author_username="alice",
        draft=False,
        published_at=_now(),
        **kwargs,
    )


def _workflow_run(
    repository_id: uuid.UUID, external_id: str, run_number: int = 7, **kwargs
) -> WorkFlowRun:
    return WorkFlowRun(
        repository_id=repository_id,
        external_id=external_id,
        workflow_id="12345",
        workflow_name="CI",
        run_number=run_number,
        status="completed",
        conclusion="success",
        branch="main",
        head_sha="abc123",
        started_at=_now(),
        completed_at=_now(),
        **kwargs,
    )


def _deployment(repository_id: uuid.UUID, external_id: str, **kwargs) -> Deployment:
    return Deployment(
        repository_id=repository_id,
        external_id=external_id,
        environment="production",
        ref="refs/heads/main",
        creator_username="alice",
        status="success",
        github_created_at=_now(),
        **kwargs,
    )


def _review_parent(repository: Repository) -> PullRequest:
    return _pull_request(repository.id, "pr-ext-1", number=101)
# ---------------------------------------------------------------------------
# Parametrization tables.
# ---------------------------------------------------------------------------

# (model, builder, fk_column, parent_factory, domain_attrs)
HISTORY_CRUD_CASES = [
    pytest.param(Commit, _commit, "repository_id", None, ("sha", "message"), id="Commit"),
    pytest.param(
        PullRequest, _pull_request, "repository_id", None, ("number", "state"), id="PullRequest"
    ),
    pytest.param(
        PullRequestReview,
        _pull_request_review,
        "pull_request_id",
        _review_parent,
        ("state", "reviewer_username"),
        id="PullRequestReview",
    ),
    pytest.param(Issue, _issue, "repository_id", None, ("number", "title"), id="Issue"),
    pytest.param(
        Release, _release, "repository_id", None, ("tag_name", "author_username"), id="Release"
    ),
    pytest.param(
        WorkFlowRun, _workflow_run, "repository_id", None, ("run_number", "status"),
        id="WorkFlowRun",
    ),
    pytest.param(
        Deployment, _deployment, "repository_id", None, ("ref", "environment"), id="Deployment"
    ),
]

REPOSITORY_OWNED_MODELS = [
    pytest.param(Commit, _commit, id="Commit"),
    pytest.param(PullRequest, _pull_request, id="PullRequest"),
    pytest.param(Issue, _issue, id="Issue"),
    pytest.param(Release, _release, id="Release"),
    pytest.param(WorkFlowRun, _workflow_run, id="WorkFlowRun"),
    pytest.param(Deployment, _deployment, id="Deployment"),
]

EXTERNAL_ID_UNIQUENESS_CASES = [
    pytest.param(Commit, _commit, id="Commit"),
    pytest.param(PullRequest, _pull_request, id="PullRequest"),
    pytest.param(Issue, _issue, id="Issue"),
    pytest.param(Release, _release, id="Release"),
    pytest.param(WorkFlowRun, _workflow_run, id="WorkFlowRun"),
    pytest.param(Deployment, _deployment, id="Deployment"),
]

SECONDARY_UNIQUENESS_CASES = [
    pytest.param(PullRequest, _pull_request, "number", id="PullRequest-number"),
    pytest.param(Issue, _issue, "number", id="Issue-number"),
    pytest.param(Release, _release, "tag_name", id="Release-tag_name"),
    pytest.param(WorkFlowRun, _workflow_run, "run_number", id="WorkFlowRun-run_number"),
]
EXPECTED_INDEXES = [
    pytest.param(
        "repositories", "ix_repositories_external_id", ["external_id"],
        id="repositories:ix_repositories_external_id",
    ),
    pytest.param(
        "commits", "ix_commits_repository_id_committed_at",
        ["repository_id", "committed_at"],
        id="commits:ix_commits_repository_id_committed_at",
    ),
    pytest.param(
        "pull_requests", "ix_pull_requests_repository_id_github_created_at",
        ["repository_id", "github_created_at"],
        id="pull_requests:ix_pull_requests_repository_id_github_created_at",
    ),
    pytest.param(
        "pull_requests", "ix_pull_requests_repository_id_state",
        ["repository_id", "state"],
        id="pull_requests:ix_pull_requests_repository_id_state",
    ),
    pytest.param(
        "pull_request_reviews", "ix_pull_request_reviews_pull_request_id_submitted_at",
        ["pull_request_id", "submitted_at"],
        id="pull_request_reviews:ix_pull_request_reviews_pull_request_id_submitted_at",
    ),
    pytest.param(
        "issues", "ix_issues_repository_id_github_created_at",
        ["repository_id", "github_created_at"],
        id="issues:ix_issues_repository_id_github_created_at",
    ),
    pytest.param(
        "issues", "ix_issues_repository_id_state", ["repository_id", "state"],
        id="issues:ix_issues_repository_id_state",
    ),
    pytest.param(
        "releases", "ix_releases_repository_id_published_at",
        ["repository_id", "published_at"],
        id="releases:ix_releases_repository_id_published_at",
    ),
    pytest.param(
        "workflow_runs", "ix_workflow_runs_repository_id_started_at",
        ["repository_id", "started_at"],
        id="workflow_runs:ix_workflow_runs_repository_id_started_at",
    ),
    pytest.param(
        "workflow_runs", "ix_workflow_runs_repository_id_status",
        ["repository_id", "status"],
        id="workflow_runs:ix_workflow_runs_repository_id_status",
    ),
    pytest.param(
        "deployments", "ix_deployments_repository_id_environment",
        ["repository_id", "environment"],
        id="deployments:ix_deployments_repository_id_environment",
    ),
    pytest.param(
        "deployments", "ix_deployments_repository_id_github_created_at",
        ["repository_id", "github_created_at"],
        id="deployments:ix_deployments_repository_id_github_created_at",
    ),
]
EXPECTED_UNIQUE_CONSTRAINTS = [
    pytest.param(
        "repositories", "uq_repositories_owner_name", ["owner", "name"],
        id="repositories:uq_repositories_owner_name",
    ),
    pytest.param(
        "commits", "uq_commits_repository_id_external_id",
        ["repository_id", "external_id"],
        id="commits:uq_commits_repository_id_external_id",
    ),
    pytest.param(
        "pull_requests", "uq_pull_requests_repository_id_external_id",
        ["repository_id", "external_id"],
        id="pull_requests:uq_pull_requests_repository_id_external_id",
    ),
    pytest.param(
        "pull_requests", "uq_pull_requests_repository_id_number",
        ["repository_id", "number"],
        id="pull_requests:uq_pull_requests_repository_id_number",
    ),
    pytest.param(
        "pull_request_reviews", "uq_pull_request_reviews_pull_request_id_external_id",
        ["pull_request_id", "external_id"],
        id="pull_request_reviews:uq_pull_request_reviews_pull_request_id_external_id",
    ),
    pytest.param(
        "issues", "uq_issues_repository_id_external_id",
        ["repository_id", "external_id"],
        id="issues:uq_issues_repository_id_external_id",
    ),
    pytest.param(
        "issues", "uq_issues_repository_id_number", ["repository_id", "number"],
        id="issues:uq_issues_repository_id_number",
    ),
    pytest.param(
        "releases", "uq_releases_repository_id_external_id",
        ["repository_id", "external_id"],
        id="releases:uq_releases_repository_id_external_id",
    ),
    pytest.param(
        "releases", "uq_releases_repository_id_tag_name",
        ["repository_id", "tag_name"],
        id="releases:uq_releases_repository_id_tag_name",
    ),
    pytest.param(
        "workflow_runs", "uq_workflow_runs_repository_id_external_id",
        ["repository_id", "external_id"],
        id="workflow_runs:uq_workflow_runs_repository_id_external_id",
    ),
    pytest.param(
        "workflow_runs", "uq_workflow_runs_repository_id_run_number",
        ["repository_id", "run_number"],
        id="workflow_runs:uq_workflow_runs_repository_id_run_number",
    ),
    pytest.param(
        "deployments", "uq_deployments_repository_id_external_id",
        ["repository_id", "external_id"],
        id="deployments:uq_deployments_repository_id_external_id",
    ),
]
EXPECTED_FOREIGN_KEYS = [
    pytest.param("commits", "repositories", id="commits->repositories"),
    pytest.param("pull_requests", "repositories", id="pull_requests->repositories"),
    pytest.param(
        "pull_request_reviews", "pull_requests", id="pull_request_reviews->pull_requests"
    ),
    pytest.param("issues", "repositories", id="issues->repositories"),
    pytest.param("releases", "repositories", id="releases->repositories"),
    pytest.param("workflow_runs", "repositories", id="workflow_runs->repositories"),
    pytest.param("deployments", "repositories", id="deployments->repositories"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_tables(db_engine) -> Generator[None, None, None]:
    """Controlled per-test cleanup: truncate the eight application tables only."""
    truncate_all_tables(db_engine)
    yield
    truncate_all_tables(db_engine)
# ---------------------------------------------------------------------------
# Basic schema tests against the migrated PostgreSQL database.
# ---------------------------------------------------------------------------


def test_schema_contains_all_application_tables(db_engine) -> None:
    inspector = inspect(db_engine)
    present = set(inspector.get_table_names())

    assert set(APP_TABLES).issubset(present)


def test_alembic_version_is_at_head(db_engine) -> None:
    with db_engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert version == EXPECTED_ALEMBIC_HEAD


# ---------------------------------------------------------------------------
# Repository CRUD + uniqueness.
# ---------------------------------------------------------------------------


def test_repository_crud_round_trip(db_session) -> None:
    repository = _repository(owner="crud-owner", name="crud-repo", external_id="gh-42")
    db_session.add(repository)
    db_session.commit()

    assert repository.id is not None
    assert isinstance(repository.id, uuid.UUID)
    assert repository.owner == "crud-owner"
    assert repository.name == "crud-repo"
    assert repository.external_id == "gh-42"
    assert repository.created_at is not None
    assert repository.updated_at is not None
    assert repository.created_at.tzinfo is not None
    assert repository.updated_at.tzinfo is not None

    db_session.expire_all()
    fetched = db_session.get(Repository, repository.id)
    assert fetched is not None
    assert fetched.id == repository.id
    assert fetched.owner == "crud-owner"
    assert fetched.name == "crud-repo"
    assert fetched.external_id == "gh-42"
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


def test_repository_owner_name_uniqueness_enforced(db_session) -> None:
    db_session.add(_repository(owner="duplicate-owner", name="duplicate-name", external_id="ext-a"))
    db_session.commit()

    duplicate = _repository(owner="duplicate-owner", name="duplicate-name", external_id="ext-b")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    rows = db_session.scalars(
        select(Repository).where(
            Repository.owner == "duplicate-owner",
            Repository.name == "duplicate-name",
        )
    ).all()
    assert len(rows) == 1
    assert rows[0].external_id == "ext-a"
# ---------------------------------------------------------------------------
# History model CRUD against the real schema.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model,builder,fk_field,parent_factory,domain_attrs", HISTORY_CRUD_CASES)
def test_history_model_insert_query_round_trip(
    db_session, model, builder, fk_field, parent_factory, domain_attrs
) -> None:
    repository = _repository(owner=f"hist-{model.__tablename__}", name="repo", external_id="rext-1")
    db_session.add(repository)
    db_session.commit()

    parent = parent_factory(repository) if parent_factory is not None else repository
    if parent is not repository:
        db_session.add(parent)
        db_session.commit()

    row = builder(parent.id, "ext-1")
    db_session.add(row)
    db_session.commit()

    assert row.id is not None
    assert isinstance(row.id, uuid.UUID)
    assert getattr(row, fk_field) == parent.id
    assert row.created_at is not None
    assert row.updated_at is not None

    db_session.expire_all()
    loaded = db_session.get(model, row.id)
    assert loaded is not None
    assert getattr(loaded, fk_field) == parent.id
    assert loaded.created_at is not None
    assert loaded.updated_at is not None
    for attribute in domain_attrs:
        assert getattr(loaded, attribute) is not None


# ---------------------------------------------------------------------------
# Foreign-key enforcement.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model,builder", REPOSITORY_OWNED_MODELS)
def test_repository_foreign_key_is_enforced(db_session, model, builder) -> None:
    row = builder(uuid.uuid4(), "ext-missing-repo")
    db_session.add(row)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_pull_request_review_foreign_key_is_enforced(db_session) -> None:
    review = _pull_request_review(uuid.uuid4(), "ext-missing-pr")
    db_session.add(review)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
# ---------------------------------------------------------------------------
# ORM relationship round-trip.
# ---------------------------------------------------------------------------


def test_repository_pull_request_review_relationship_round_trip(db_session) -> None:
    repository = _repository(owner="relation-owner", name="relation-repo", external_id="rel-1")
    db_session.add(repository)
    db_session.commit()

    pull_request = _pull_request(repository.id, "pr-ext-1", number=101)
    db_session.add(pull_request)
    db_session.commit()

    review = _pull_request_review(pull_request.id, "rev-ext-1")
    db_session.add(review)
    db_session.commit()

    commit = _commit(repository.id, "commit-ext-1")
    db_session.add(commit)
    db_session.commit()

    db_session.expire_all()

    reloaded_repository = db_session.get(Repository, repository.id)
    reloaded_pull_request = db_session.get(PullRequest, pull_request.id)
    reloaded_review = db_session.get(PullRequestReview, review.id)
    reloaded_commit = db_session.get(Commit, commit.id)

    assert reloaded_pull_request in reloaded_repository.pull_requests
    assert reloaded_pull_request.repository.id == repository.id
    assert reloaded_review in reloaded_pull_request.reviews
    assert reloaded_review.pull_request.id == pull_request.id
    assert reloaded_commit in reloaded_repository.commits
    assert reloaded_commit.repository.id == repository.id


# ---------------------------------------------------------------------------
# Timestamp behavior (server-side defaults, no triggers).
# ---------------------------------------------------------------------------


def test_server_defaults_populate_timestamps(db_session) -> None:
    repository = _repository(owner="timestamp-owner", name="timestamp-repo", external_id="ts-1")
    db_session.add(repository)
    db_session.commit()

    db_session.expire_all()
    loaded = db_session.get(Repository, repository.id)

    assert isinstance(loaded.created_at, datetime)
    assert isinstance(loaded.updated_at, datetime)
    assert loaded.created_at.tzinfo is not None
    assert loaded.updated_at.tzinfo is not None


def test_updated_at_refresh_follows_timestamp_mixin(db_session) -> None:
    repository = _repository(owner="timestamp-owner", name="before", external_id="ts-2")
    db_session.add(repository)
    db_session.commit()
    initial_created_at = repository.created_at
    initial_updated_at = repository.updated_at

    repository.name = "after"
    # PostgreSQL now() returns the transaction start time, so guarantee the
    # update transaction begins strictly later than the insert transaction.
    time.sleep(0.01)
    db_session.commit()

    db_session.expire_all()
    loaded = db_session.get(Repository, repository.id)

    assert loaded.name == "after"
    assert loaded.created_at == initial_created_at
    assert loaded.updated_at is not None
    assert loaded.updated_at.tzinfo is not None
    assert loaded.updated_at > initial_updated_at
# ---------------------------------------------------------------------------
# External identifier uniqueness constraints.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model,builder", EXTERNAL_ID_UNIQUENESS_CASES)
def test_external_id_uniqueness_enforced(db_session, model, builder) -> None:
    repository = _repository(
        owner=f"uniq-{model.__tablename__}", name="repo", external_id="rext-1"
    )
    db_session.add(repository)
    db_session.commit()

    db_session.add(builder(repository.id, "ext-dup"))
    db_session.commit()

    duplicate = builder(repository.id, "ext-dup")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_pull_request_review_external_id_uniqueness_enforced(db_session) -> None:
    repository = _repository(owner="uniq-review", name="repo", external_id="rext-1")
    db_session.add(repository)
    db_session.commit()
    pull_request = _pull_request(repository.id, "pr-ext-1", number=1)
    db_session.add(pull_request)
    db_session.commit()

    db_session.add(_pull_request_review(pull_request.id, "rev-ext-dup"))
    db_session.commit()

    db_session.add(_pull_request_review(pull_request.id, "rev-ext-dup"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("model,builder,secondary_field", SECONDARY_UNIQUENESS_CASES)
def test_secondary_field_uniqueness_enforced(db_session, model, builder, secondary_field) -> None:
    # The builders use constant defaults for the secondary unique fields
    # (number / tag_name / run_number), so two rows with different external_id
    # values collide on exactly the (repository_id, secondary_field) constraint.
    repository = _repository(
        owner=f"uniq2-{model.__tablename__}", name="repo", external_id="rext-2"
    )
    db_session.add(repository)
    db_session.commit()

    db_session.add(builder(repository.id, "ext-first"))
    db_session.commit()

    duplicate = builder(repository.id, "ext-second")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# Live-schema index / constraint / foreign-key validation.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("table_name,index_name,expected_columns", EXPECTED_INDEXES)
def test_indexes_exist_in_database(db_engine, table_name, index_name, expected_columns) -> None:
    indexes = inspect(db_engine).get_indexes(table_name)
    by_name = {index["name"]: index for index in indexes}

    assert index_name in by_name, f"Missing index {index_name!r} on {table_name!r}"
    assert by_name[index_name]["column_names"] == expected_columns


@pytest.mark.parametrize("table_name,constraint_name,expected_columns", EXPECTED_UNIQUE_CONSTRAINTS)
def test_unique_constraints_exist_in_database(
    db_engine, table_name, constraint_name, expected_columns
) -> None:
    constraints = inspect(db_engine).get_unique_constraints(table_name)
    by_name = {constraint["name"]: constraint for constraint in constraints}

    assert constraint_name in by_name, f"Missing unique constraint {constraint_name!r} on {table_name!r}"
    assert by_name[constraint_name]["column_names"] == expected_columns


@pytest.mark.parametrize("table_name,referenced_table", EXPECTED_FOREIGN_KEYS)
def test_foreign_keys_exist_in_database(db_engine, table_name, referenced_table) -> None:
    foreign_keys = inspect(db_engine).get_foreign_keys(table_name)

    assert any(fk["referred_table"] == referenced_table for fk in foreign_keys)