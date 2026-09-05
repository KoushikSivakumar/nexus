"""Database connectivity integration test.

Connects to the dedicated PostgreSQL test database (``nexus_test`` by default).
The session-scoped ``db_engine`` fixture creates the database when missing and
migrates it to the current Alembic head, so this test always runs against a
real, migrated PostgreSQL schema. If PostgreSQL is unavailable the fixture
raises and the test fails loudly instead of being silently skipped.
"""

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_database_connectivity(db_session) -> None:
    result = db_session.execute(text("SELECT 1")).scalar_one()

    assert result == 1
