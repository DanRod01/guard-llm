from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(StrEnum):
    """Operational statuses for health checks."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResponse(BaseModel):
    """Strict contract for health check responses."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    status: HealthStatus = Field(
        default=HealthStatus.HEALTHY,
        description="Current health status of the security gateway",
    )
    version: str = Field(
        description="Semantic version of the running GuardLLM instance",
    )
    environment: str = Field(
        description="Active deployment environment (development, staging, production)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 UTC timestamp of the health check inspection",
    )
