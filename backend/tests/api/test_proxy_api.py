from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from guardllm.services.gemini import (
    GeminiAPIError,
    GeminiConfigError,
    GeminiTimeoutError,
)


@pytest.mark.asyncio
async def test_proxy_chat_endpoint_success(async_client: AsyncClient) -> None:
    fake_gemini_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Resposta segura para o cliente."}],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 5,
            "totalTokenCount": 15,
        },
    }

    with patch(
        "guardllm.services.proxy.gemini_client.generate_content",
        new_callable=AsyncMock,
        return_value=fake_gemini_resp,
    ):
        response = await async_client.post(
            "/api/v1/proxy/chat",
            json={"prompt": "Olá, me informe sobre segurança em LLMs."},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["output_text"] == "Resposta segura para o cliente."
        assert "security" in data
        assert data["security"]["inbound_audit"]["sanitized"] is False
        assert data["security"]["total_tokens"] == 15


@pytest.mark.asyncio
async def test_proxy_chat_endpoint_validation_error(async_client: AsyncClient) -> None:
    # Nem prompt nem messages fornecidos
    response = await async_client.post(
        "/api/v1/proxy/chat",
        json={"model": "gemini-1.5-flash"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_proxy_chat_endpoint_missing_api_key_returns_503(
    async_client: AsyncClient,
) -> None:
    with patch(
        "guardllm.services.proxy.gemini_client.generate_content",
        new_callable=AsyncMock,
        side_effect=GeminiConfigError("API Key missing"),
    ):
        response = await async_client.post(
            "/api/v1/proxy/chat",
            json={"prompt": "Teste"},
        )
        assert response.status_code == 503
        data = response.json()
        assert "indisponível" in data["detail"]


@pytest.mark.asyncio
async def test_proxy_chat_endpoint_timeout_returns_504(
    async_client: AsyncClient,
) -> None:
    with patch(
        "guardllm.services.proxy.gemini_client.generate_content",
        new_callable=AsyncMock,
        side_effect=GeminiTimeoutError("Timeout"),
    ):
        response = await async_client.post(
            "/api/v1/proxy/chat",
            json={"prompt": "Teste"},
        )
        assert response.status_code == 504
        data = response.json()
        assert "demorou muito" in data["detail"]


@pytest.mark.asyncio
async def test_proxy_chat_endpoint_upstream_error_returns_502(
    async_client: AsyncClient,
) -> None:
    with patch(
        "guardllm.services.proxy.gemini_client.generate_content",
        new_callable=AsyncMock,
        side_effect=GeminiAPIError(429, "Quota exceeded"),
    ):
        response = await async_client.post(
            "/api/v1/proxy/chat",
            json={"prompt": "Teste"},
        )
        assert response.status_code == 502
        data = response.json()
        assert "429" in data["detail"]
