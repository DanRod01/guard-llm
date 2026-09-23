import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200_and_valid_schema(
    async_client: AsyncClient,
) -> None:
    """Verifies that the /api/v1/health probe returns 200 OK with strict schema."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
    assert "timestamp" in data
