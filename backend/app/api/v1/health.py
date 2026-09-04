from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health import HealthService, get_health_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
def readiness(
    response: Response,
    health_service: HealthService = Depends(get_health_service),
) -> ReadinessResponse:
    checks = health_service.readiness_checks()
    ready = all(checks.values())

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(status="ready" if ready else "not_ready", checks=checks)
