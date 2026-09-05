"""Migration-bootstrap integration test.

Proves that the current Alembic migration set can initialize a clean, empty
PostgreSQL database from scratch:

    empty test database -> alembic upgrade head -> schema exists -> ORM works

This uses a dedicated ``*_migration`` database (e.g. ``nexus_test_migration``)
that is dropped and recreated purely for this purpose -- it is never the
development ``nexus`` database and never the regular ``nexus_test`` database.
The drop helper refuses to run against any database whose name does not end in
``_migration``.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.session import create_database_engine
from app.models import Repository
from db_helpers import (
    APP_TABLES,
    EXPECTED_ALEMBIC_HEAD,
    build_migration_database_url,
    create_database_if_missing,
    drop_database_if_exists,
    run_alembic_upgrade,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def clean_migration_database(test_database_url: str):
    """Create a throwaway ``*_migration`` database, migrate it, drop it at the end."""
    migration_url = build_migration_database_url(test_database_url)
    drop_database_if_exists(migration_url)
    create_database_if_missing(migration_url)
    run_alembic_upgrade(migration_url)
    try:
        yield migration_url
    finally:
        drop_database_if_exists(migration_url)


def test_empty_database_reaches_head_and_creates_schema(clean_migration_database: str) -> None:
    engine = create_database_engine(clean_migration_database)
    try:
        inspector = inspect(engine)
        present = set(inspector.get_table_names())
        assert {"alembic_version", *APP_TABLES}.issubset(present)

        with engine.connect() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == EXPECTED_ALEMBIC_HEAD
    finally:
        engine.dispose()


def test_fresh_schema_supports_orm_writes(clean_migration_database: str) -> None:
    engine = create_database_engine(clean_migration_database)
    try:
        with Session(engine) as session:
            repository = Repository(
                owner="migration-owner", name="clean-database", external_id="migr-1"
            )
            session.add(repository)
            session.commit()

            assert isinstance(repository.id, uuid.UUID)
            assert repository.owner == "migration-owner"
            assert repository.created_at is not None
            assert repository.updated_at is not None
    finally:
        engine.dispose()