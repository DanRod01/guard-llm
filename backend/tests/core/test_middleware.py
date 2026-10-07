import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_middleware_generates_correlation_id(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    assert "x-correlation-id" in response.headers
    cid = response.headers["x-correlation-id"]
    assert len(cid) >= 8


@pytest.mark.asyncio
async def test_middleware_preserves_valid_incoming_correlation_id(
    async_client: AsyncClient,
) -> None:
    custom_trace = "custom-trace-id-12345"
    response = await async_client.get(
        "/api/v1/health",
        headers={"X-Correlation-ID": custom_trace},
    )

    assert response.status_code == 200
    assert response.headers.get("x-correlation-id") == custom_trace


@pytest.mark.asyncio
async def test_middleware_sanitizes_invalid_incoming_header(
    async_client: AsyncClient,
) -> None:
    # Cabeçalho malicioso ou com caracteres ilegais para Header Injection
    malicious_header = "invalido;\r\nSet-Cookie: evil=1"
    response = await async_client.get(
        "/api/v1/health",
        headers={"X-Correlation-ID": malicious_header},
    )

    assert response.status_code == 200
    # O middleware deve descartar o header inválido e gerar um UUID seguro
    cid = response.headers.get("x-correlation-id")
    assert cid != malicious_header
    assert len(cid) == 32  # UUID hex length
