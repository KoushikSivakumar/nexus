"""Model metadata tests for the shared SQLAlchemy model foundation.

These are metadata/introspection tests only and do not require a database
connection or any new tables.
"""

import uuid

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.types import DateTime

from app.models import Repository, TimestampMixin, UUIDPrimaryKeyMixin


def test_repository_subclasses_shared_mixins() -> None:
    assert issubclass(Repository, UUIDPrimaryKeyMixin)
    assert issubclass(Repository, TimestampMixin)


def test_repository_id_is_uuid() -> None:
    id_column = Repository.__table__.c.id

    assert isinstance(id_column.type, PostgreSQLUUID)
    assert id_column.type.as_uuid is True
    assert id_column.type.python_type is uuid.UUID


def test_repository_id_is_primary_key() -> None:
    id_column = Repository.__table__.c.id

    assert id_column.primary_key is True
    assert list(Repository.__table__.primary_key.columns) == [id_column]


def test_repository_uses_timestamp_fields() -> None:
    assert "created_at" in Repository.__table__.c
    assert "updated_at" in Repository.__table__.c


def test_repository_timestamp_fields_are_timezone_aware() -> None:
    for field in ("created_at", "updated_at"):
        column = Repository.__table__.c[field]

        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True


def test_repository_owner_name_uniqueness_remains_defined() -> None:
    unique_constraints = [
        constraint
        for constraint in Repository.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert len(unique_constraints) == 1
    constraint = unique_constraints[0]
    assert constraint.name == "uq_repositories_owner_name"
    assert [column.name for column in constraint.columns] == ["owner", "name"]


def test_repository_external_id_remains_indexed() -> None:
    assert Repository.__table__.c.external_id.index is True