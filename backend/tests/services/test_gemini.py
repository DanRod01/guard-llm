from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from guardllm.core.config import Settings
from guardllm.services.gemini import (
    GeminiAPIError,
    GeminiClient,
    GeminiConfigError,
    GeminiTimeoutError,
)


def test_gemini_client_missing_api_key_raises_config_error() -> None:
    test_settings = Settings(GEMINI_API_KEY="")
    client = GeminiClient(app_settings=test_settings)

    with pytest.raises(GeminiConfigError, match="GEMINI_API_KEY não está configurada"):
        client._prepare_headers()


def test_gemini_client_prepare_headers_with_valid_key() -> None:
    test_settings = Settings(GEMINI_API_KEY="AIzaSyTestKey123")
    client = GeminiClient(app_settings=test_settings)

    headers = client._prepare_headers()
    assert headers["x-goog-api-key"] == "AIzaSyTestKey123"
    assert headers["Content-Type"] == "application/json"


def test_gemini_client_build_payload_with_system_instruction() -> None:
    test_settings = Settings(GEMINI_API_KEY="AIzaSyTestKey123")
    client = GeminiClient(app_settings=test_settings)

    contents = [{"role": "user", "parts": [{"text": "Olá"}]}]
    payload = client._build_payload(
        contents=contents,
        system_instruction="Você é um assistente seguro.",
        temperature=0.7,
    )

    assert payload["contents"] == contents
    sys_text = payload["systemInstruction"]["parts"][0]["text"]
    assert sys_text == "Você é um assistente seguro."
    assert payload["generationConfig"]["temperature"] == 0.7


@pytest.mark.asyncio
async def test_gemini_client_generate_content_success() -> None:
    test_settings = Settings(GEMINI_API_KEY="AIzaSyTestKey123")
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.is_closed = False

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Resposta segura do Gemini"}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 5,
            "candidatesTokenCount": 10,
            "totalTokenCount": 15,
        },
    }
    mock_http_client.post.return_value = mock_response

    client = GeminiClient(app_settings=test_settings, client=mock_http_client)
    result = await client.generate_content(
        contents=[{"role": "user", "parts": [{"text": "Teste"}]}]
    )

    assert "candidates" in result
    candidate_text = result["candidates"][0]["content"]["parts"][0]["text"]
    assert candidate_text == "Resposta segura do Gemini"
    assert result["usageMetadata"]["totalTokenCount"] == 15


@pytest.mark.asyncio
async def test_gemini_client_timeout_raises_gemini_timeout_error() -> None:
    test_settings = Settings(GEMINI_API_KEY="AIzaSyTestKey123")
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.is_closed = False
    mock_http_client.post.side_effect = httpx.TimeoutException("Read timed out")

    client = GeminiClient(app_settings=test_settings, client=mock_http_client)

    with pytest.raises(GeminiTimeoutError, match="Tempo limite esgotado"):
        await client.generate_content(
            contents=[{"role": "user", "parts": [{"text": "Teste"}]}]
        )


@pytest.mark.asyncio
async def test_gemini_client_upstream_error_raises_gemini_api_error() -> None:
    test_settings = Settings(GEMINI_API_KEY="AIzaSyTestKey123")
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.is_closed = False

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.text = '{"error": {"message": "Invalid argument"}}'
    mock_http_client.post.return_value = mock_response

    client = GeminiClient(app_settings=test_settings, client=mock_http_client)

    with pytest.raises(GeminiAPIError) as exc_info:
        await client.generate_content(
            contents=[{"role": "user", "parts": [{"text": "Teste"}]}]
        )

    assert exc_info.value.status_code == 400
    assert "Invalid argument" in exc_info.value.message
