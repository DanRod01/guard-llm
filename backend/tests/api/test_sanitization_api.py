import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sanitize_endpoint_masks_pii(async_client: AsyncClient) -> None:
    payload = {
        "text": (
            "Cliente João, CPF 529.982.247-25, email joao@email.com, "
            "usando chave AKIAIOSFODNN7EXAMPLE."
        )
    }

    response = await async_client.post("/api/v1/security/sanitize", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "529.982.247-25" not in data["sanitized_text"]
    assert "joao@email.com" not in data["sanitized_text"]
    assert "AKIAIOSFODNN7EXAMPLE" not in data["sanitized_text"]

    assert "[REDACTED_CPF]" in data["sanitized_text"]
    assert "[REDACTED_EMAIL]" in data["sanitized_text"]
    assert "[REDACTED_API_KEY]" in data["sanitized_text"]
    assert len(data["entities_detected"]) == 3
