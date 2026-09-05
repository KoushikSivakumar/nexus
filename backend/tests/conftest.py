from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.session import create_database_engine
from app.main import create_app
from db_helpers import create_database_if_missing, resolve_test_database_url, run_alembic_upgrade


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="test",
        database_url=resolve_test_database_url(),
        redis_url="redis://localhost:6379/1",
        cors_origins=["http://testserver"],
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    return TestClient(create_app(test_settings))


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """The dedicated integration-test database URL (env override supported)."""
    return resolve_test_database_url()


@pytest.fixture(scope="session")
def db_engine(test_database_url: str) -> Generator[Engine, None, None]:
    """Bootstrap the dedicated test database and yield an engine bound to it.

    The database (``nexus_test`` by default) is created when missing and migrated
    to the current Alembic head. If PostgreSQL is unreachable this fixture raises
    so the integration tests fail loudly instead of being silently skipped.
    """
    create_database_if_missing(test_database_url)
    run_alembic_upgrade(test_database_url)
    engine = create_database_engine(test_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Provide a real SQLAlchemy session against the migrated test database.

    Tests commit their own transactions; the integration modules clean up with
    controlled table truncation between tests. The teardown additionally rolls
    back any in-flight transaction (e.g. one left behind by an expected
    IntegrityError) so later tests are never poisoned.
    """
    session_factory = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
