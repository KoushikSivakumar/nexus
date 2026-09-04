from redis import Redis
from fastapi import Depends
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.db.session import get_session_factory


class HealthService:
    def __init__(self, settings: Settings, session_factory=None) -> None:
        self.settings = settings
        self.session_factory = session_factory

    def database_ready(self) -> bool:
        try:
            session_factory = self.session_factory or get_session_factory()
            with session_factory() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def redis_ready(self) -> bool:
        try:
            client = Redis.from_url(str(self.settings.redis_url), socket_connect_timeout=1)
            return bool(client.ping())
        except Exception:
            return False

    def readiness_checks(self) -> dict[str, bool]:
        return {"database": self.database_ready(), "redis": self.redis_ready()}


def get_health_service(settings: Settings = Depends(get_settings)) -> HealthService:
    return HealthService(settings)
