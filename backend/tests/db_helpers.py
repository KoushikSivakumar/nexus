"""Shared helpers for the NEXUS real-PostgreSQL integration tests.

These helpers centralize the test-database bootstrap so the pytest fixtures and
the integration test modules use exactly the same logic:

* resolve the test database URL (environment override or project default)
* create the dedicated test database when it is missing
* drop a dedicated ``*_migration`` test database (never the development DB)
* apply Alembic migrations to a database (``alembic upgrade head``)
* truncate only the application tables for per-test isolation

The database URL is honored from ``NEXUS_TEST_DATABASE_URL`` so the Docker
hostname (``postgres``) and the local hostname (``localhost``) workflows keep
working unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI_PATH = BACKEND_DIR / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = BACKEND_DIR / "alembic"

DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://nexus:nexus@localhost:5432/nexus_test"
EXPECTED_ALEMBIC_HEAD = "202609050002"

# The eight application tables created by the Alembic migrations. Note that
# ``alembic_version`` is deliberately NOT part of this list: migration state is
# never truncated or modified by the test cleanup.
APP_TABLES = (
    "repositories",
    "commits",
    "pull_requests",
    "pull_request_reviews",
    "issues",
    "releases",
    "workflow_runs",
    "deployments",
)


def resolve_test_database_url() -> str:
    """Return the integration-test database URL.

    ``NEXUS_TEST_DATABASE_URL`` may override the project default. The default
    targets ``localhost`` (host-run tests against a host-mapped PostgreSQL
    container); inside Docker the environment variable points at ``postgres``.
    """
    return os.getenv("NEXUS_TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


def _admin_url(database_url: str):
    """Rewrite a database URL to target the server-level ``postgres`` database.

    Keeps the same host/port/credentials as the original URL so both the Docker
    (``postgres`` hostname) and local (``localhost``) workflows keep working.
    """
    url = make_url(database_url)
    return url.set(database="postgres")


def create_database_if_missing(database_url: str) -> None:
    """Create the target database on the PostgreSQL server if it does not exist.

    This only provisions the database itself -- the schema is always established
    through ``alembic upgrade head`` (the migration system is the source of
    truth, never hand-written SQL in the tests).
    """
    url = make_url(database_url)
    engine = create_engine(_admin_url(database_url), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": url.database},
            ).scalar()
            if not exists:
                quoted_name = url.database.replace('"', '""')
                connection.execute(text(f'CREATE DATABASE "{quoted_name}"'))
    finally:
        engine.dispose()


def drop_database_if_exists(database_url: str) -> None:
    """Drop a dedicated ``*_migration`` test database (safety-guarded).

    Used only by the migration-bootstrap integration test on its throwaway
    ``*_migration`` database. The development database and the regular test
    database are never droppable through this helper, so a misconfiguration can
    not wipe developer data.
    """
    url = make_url(database_url)
    if not url.database or not url.database.endswith("_migration"):
        raise AssertionError(
            f"Refusing to drop database {url.database!r}: only dedicated "
            "'*_migration' test databases may be dropped by the tests."
        )
    engine = create_engine(_admin_url(database_url), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            quoted_name = url.database.replace('"', '""')
            connection.execute(text(f'DROP DATABASE IF EXISTS "{quoted_name}" WITH (FORCE)'))
    finally:
        engine.dispose()


def build_migration_database_url(base_url: str) -> str:
    """Derive the dedicated migration-bootstrap database from the test URL.

    The same server/credentials are reused; only the database name changes,
    e.g. ``nexus_test`` -> ``nexus_test_migration``. ``render_as_string`` is
    used explicitly because ``str(URL)`` masks the password.
    """
    url = make_url(base_url)
    if not url.database:
        raise ValueError("The test database URL has no database name.")
    return url.set(database=f"{url.database}_migration").render_as_string(hide_password=False)


def run_alembic_upgrade(database_url: str) -> None:
    """Apply ``alembic upgrade head`` to ``database_url`` in-process.

    ``alembic/env.py`` reads the database URL from the application settings, so
    the ``NEXUS_DATABASE_URL`` environment variable is temporarily pointed at the
    target database and the cached settings object is cleared around the run.
    The prior environment value (if any) is restored afterwards.
    """
    from app.core.config import get_settings

    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    cfg.set_main_option("prepend_sys_path", str(BACKEND_DIR))
    cfg.set_main_option("path_separator", "os")
    cfg.set_main_option("sqlalchemy.url", database_url)

    previous_url = os.environ.get("NEXUS_DATABASE_URL")
    os.environ["NEXUS_DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        command.upgrade(cfg, "head")
    finally:
        if previous_url is None:
            os.environ.pop("NEXUS_DATABASE_URL", None)
        else:
            os.environ["NEXUS_DATABASE_URL"] = previous_url
        get_settings.cache_clear()


def truncate_all_tables(engine: Engine) -> None:
    """Delete all rows from the eight application tables.

    This is the controlled per-test cleanup used by the integration tests: it
    never touches ``alembic_version`` (migration state) and never drops the
    database.
    """
    table_names = ", ".join(APP_TABLES)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {table_names} CASCADE"))