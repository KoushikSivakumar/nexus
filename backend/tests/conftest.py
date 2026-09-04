import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql+psycopg://nexus:nexus@localhost:5432/nexus_test",
        redis_url="redis://localhost:6379/1",
        cors_origins=["http://testserver"],
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    return TestClient(create_app(test_settings))
