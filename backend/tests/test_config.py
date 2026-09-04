from app.core.config import Settings


def test_configuration_loads_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_APP_NAME", "NEXUS Test API")
    monkeypatch.setenv("NEXUS_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "NEXUS_DATABASE_URL",
        "postgresql+psycopg://nexus:nexus@postgres:5432/nexus",
    )
    monkeypatch.setenv("NEXUS_REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("NEXUS_CORS_ORIGINS", "http://localhost:5173,http://testserver")

    settings = Settings()

    assert settings.app_name == "NEXUS Test API"
    assert settings.environment == "test"
    assert str(settings.database_url).startswith("postgresql+psycopg://")
    assert settings.cors_origins == ["http://localhost:5173", "http://testserver"]
