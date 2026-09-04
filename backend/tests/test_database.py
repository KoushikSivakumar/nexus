import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db.session import create_database_engine


def test_database_connectivity() -> None:
    database_url = os.getenv(
        "NEXUS_TEST_DATABASE_URL",
        "postgresql+psycopg://nexus:nexus@localhost:5432/nexus_test",
    )
    engine = create_database_engine(database_url)

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")
    finally:
        engine.dispose()

    assert result == 1
