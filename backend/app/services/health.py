from redis import Redis
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal


class HealthService:
    def __init__(self, settings: Settings, session_factory=SessionLocal) -> None:
        self.settings = settings
        self.session_factory = session_factory

    def database_ready(self) -> bool:
        try:
            with self.session_factory() as session:
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


def get_health_service() -> HealthService:
    return HealthService(get_settings())
