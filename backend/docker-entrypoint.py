"""NEXUS backend Docker entrypoint.

Startup / readiness bootstrap for the API container:

    1. Wait for PostgreSQL to accept connections (healthcheck plus retry loop --
       never a blind sleep; the image reads the database URL from the same
       settings the application uses).
    2. Apply migrations with ``alembic upgrade head``.  This is the ONLY
       mechanism that creates the NEXUS schema and is idempotent: a second run
       simply reports the database is already at the head revision.
    3. Only then exec the container command (default: uvicorn app.main:app).

If PostgreSQL never becomes reachable, or ``alembic upgrade head`` fails, this
entrypoint exits with a non-zero status so the failure is visible and the API
does not start against an uninitialized database.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from sqlalchemy import create_engine, text

DEFAULT_MAX_ATTEMPTS = 60
DEFAULT_INTERVAL_SECONDS = 2


def _database_url() -> str:
    """Return the parsed application database URL."""
    from app.core.config import get_settings

    return str(get_settings().database_url)


def wait_for_database(url: str) -> None:
    """Block until PostgreSQL accepts connections or the retry budget is spent.

    Uses a short, fixed retry cadence (no long arbitrary sleep) so steady-state
    startup is fast while a cold PostgreSQL container still gets real time to
    become ready.
    """
    max_attempts = int(os.getenv("NEXUS_DB_WAIT_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS)))
    interval_seconds = float(
        os.getenv("NEXUS_DB_WAIT_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS))
    )

    engine = create_engine(url, pool_pre_ping=True)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("PostgreSQL is reachable.", flush=True)
            return
        except Exception as exc:  # noqa: BLE001 - any DB error means "not ready yet"
            last_error = exc
            print(
                f"Waiting for PostgreSQL to become ready "
                f"(attempt {attempt}/{max_attempts}): {exc}",
                flush=True,
            )
            time.sleep(interval_seconds)

    raise SystemExit(
        f"PostgreSQL was not reachable after {max_attempts} attempts "
        f"({interval_seconds}s apart). Last error: {last_error}. "
        "Check the postgres service and NEXUS_DATABASE_URL."
    )


def run_migrations() -> None:
    """Apply ``alembic upgrade head`` — the single source of schema truth."""
    print("Running: alembic upgrade head", flush=True)
    result = subprocess.run(["alembic", "upgrade", "head"])
    if result.returncode != 0:
        raise SystemExit(
            f"alembic upgrade head failed with exit code {result.returncode}. "
            "The API will not start because the database schema is not ready."
        )
    print("alembic upgrade head completed; database is at the current head.", flush=True)


def main() -> None:
    url = _database_url()
    wait_for_database(url)
    run_migrations()

    command = sys.argv[1:]
    if not command:
        command = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

    print(f"Starting API: {' '.join(command)}", flush=True)
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()