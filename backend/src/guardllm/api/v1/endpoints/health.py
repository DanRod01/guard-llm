from fastapi import APIRouter, status

from guardllm.core.config import settings
from guardllm.schemas.health import HealthCheckResponse, HealthStatus

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Gateway Liveness & Readiness Probe",
    description="Returns the operational status, version, and environment of GuardLLM.",
)
async def check_health() -> HealthCheckResponse:
    return HealthCheckResponse(
        status=HealthStatus.HEALTHY,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
