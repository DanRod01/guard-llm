from collections.abc import Iterator

import pytest
from httpx import AsyncClient

from guardllm.services.audit import audit_logger


@pytest.fixture(autouse=True)
def clean_audit_buffer() -> Iterator[None]:
    """Garante buffer limpo antes e depois de cada teste."""
    audit_logger.clear()
    yield
    audit_logger.clear()


@pytest.mark.asyncio
async def test_get_audit_events_empty(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/audit/events")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["events"] == []


@pytest.mark.asyncio
async def test_get_audit_stats_empty(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/audit/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_events"] == 0
    assert stats["transactions_success"] == 0
    assert stats["injections_blocked"] == 0
    assert stats["pii_redacted"] == 0
    assert stats["average_latency_ms"] == 0.0


@pytest.mark.asyncio
async def test_audit_records_event_from_proxy_chat(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simula resposta upstream do Gemini
    from guardllm.services.gemini import gemini_client

    async def mock_generate_content(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Resposta de teste segura."}],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 15,
                "candidatesTokenCount": 8,
                "totalTokenCount": 23,
            },
        }

    monkeypatch.setattr(gemini_client, "generate_content", mock_generate_content)

    # 1. Faz chamada com CPF para gerar evento PII_REDACTED
    payload = {"prompt": "Meu CPF é 529.982.247-25, tudo bem?"}
    post_res = await async_client.post("/api/v1/proxy/chat", json=payload)
    assert post_res.status_code == 200

    # 2. Consulta eventos no endpoint de auditoria
    events_res = await async_client.get("/api/v1/audit/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    assert events_data["total"] == 1
    event = events_data["events"][0]
    assert event["event_type"] == "PII_REDACTED"
    assert event["severity"] == "WARNING"
    assert event["security"]["inbound_entities_count"] == 1
    assert "CPF" in event["security"]["inbound_entity_types"]

    # 3. Consulta estatísticas
    stats_res = await async_client.get("/api/v1/audit/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_events"] == 1
    assert stats["pii_redacted"] == 1
    assert stats["total_tokens"] == 23
    assert stats["average_latency_ms"] > 0


@pytest.mark.asyncio
async def test_clear_audit_events(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from guardllm.services.gemini import gemini_client

    async def mock_generate_content(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "candidates": [{"content": {"parts": [{"text": "OK"}]}}],
            "usageMetadata": {"totalTokenCount": 5},
        }

    monkeypatch.setattr(gemini_client, "generate_content", mock_generate_content)

    await async_client.post("/api/v1/proxy/chat", json={"prompt": "Olá"})

    events_res = await async_client.get("/api/v1/audit/events")
    assert events_res.json()["total"] == 1

    delete_res = await async_client.delete("/api/v1/audit/events")
    assert delete_res.status_code == 204

    events_after = await async_client.get("/api/v1/audit/events")
    assert events_after.json()["total"] == 0
