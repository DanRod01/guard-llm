from unittest.mock import AsyncMock

import pytest

from guardllm.schemas.proxy import ChatMessage, ProxyChatRequest
from guardllm.schemas.sanitization import PIIType
from guardllm.security.sanitization.engine import SanitizerEngine
from guardllm.services.gemini import GeminiClient
from guardllm.services.proxy import ProxyService


@pytest.mark.asyncio
async def test_proxy_service_inbound_masks_pii_before_llm() -> None:
    mock_gemini = AsyncMock(spec=GeminiClient)
    mock_gemini._settings = AsyncMock()
    mock_gemini._settings.GEMINI_MODEL = "gemini-1.5-flash"

    # Simula resposta segura da LLM
    mock_gemini.generate_content.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Recebido com sucesso, cliente anônimo."}],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 20,
            "candidatesTokenCount": 8,
            "totalTokenCount": 28,
        },
    }

    sanitizer = SanitizerEngine()
    service = ProxyService(sanitizer=sanitizer, client=mock_gemini)

    valid_cpf = "529.982.247-25"
    email = "contato@empresa.com"
    request = ProxyChatRequest(
        prompt=f"O cliente {email} possui o CPF {valid_cpf}."
    )

    response = await service.process_chat(request)

    # 1. Verifica se a LLM recebeu apenas o texto higienizado
    called_contents = mock_gemini.generate_content.call_args.kwargs["contents"]
    sent_text = called_contents[0]["parts"][0]["text"]

    assert valid_cpf not in sent_text
    assert email not in sent_text
    assert "[REDACTED_CPF]" in sent_text
    assert "[REDACTED_EMAIL]" in sent_text

    # 2. Verifica a auditoria de segurança Inbound
    assert response.security.inbound_audit.sanitized is True
    assert len(response.security.inbound_audit.entities_redacted) == 2

    # 3. Metadados e resposta final
    assert response.output_text == "Recebido com sucesso, cliente anônimo."
    assert response.security.total_tokens == 28
    assert response.security.latency_ms > 0


@pytest.mark.asyncio
async def test_proxy_service_outbound_masks_pii_leaked_by_llm() -> None:
    mock_gemini = AsyncMock(spec=GeminiClient)
    mock_gemini._settings = AsyncMock()
    mock_gemini._settings.GEMINI_MODEL = "gemini-1.5-flash"

    # LLM alucina ou reflete um número de cartão de crédito válido
    leaked_card = "4532 0150 0000 0007"
    mock_gemini.generate_content.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": f"O cartão processado foi {leaked_card}."}],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 12,
            "totalTokenCount": 22,
        },
    }

    sanitizer = SanitizerEngine()
    service = ProxyService(sanitizer=sanitizer, client=mock_gemini)

    request = ProxyChatRequest(
        prompt="Qual cartão foi usado?",
        sanitize_outbound=True,
    )

    response = await service.process_chat(request)

    # O texto entregue ao usuário deve ter o cartão mascarado
    assert leaked_card not in response.output_text
    assert "[REDACTED_CREDIT_CARD]" in response.output_text

    # Auditoria de segurança Outbound
    assert response.security.outbound_audit is not None
    assert response.security.outbound_audit.sanitized is True
    redacted = response.security.outbound_audit.entities_redacted[0]
    assert redacted.entity_type == PIIType.CREDIT_CARD


@pytest.mark.asyncio
async def test_proxy_service_with_chat_messages_and_system_instruction() -> None:
    mock_gemini = AsyncMock(spec=GeminiClient)
    mock_gemini._settings = AsyncMock()
    mock_gemini._settings.GEMINI_MODEL = "gemini-1.5-flash"

    mock_gemini.generate_content.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Entendido, diretrizes seguidas."}],
                    "role": "model",
                }
            }
        ]
    }

    service = ProxyService(sanitizer=SanitizerEngine(), client=mock_gemini)

    messages = [
        ChatMessage(role="system", content="Você é um assistente do GuardLLM."),
        ChatMessage(role="user", content="Qual é o status do sistema?"),
    ]
    request = ProxyChatRequest(messages=messages)

    response = await service.process_chat(request)

    kwargs = mock_gemini.generate_content.call_args.kwargs
    assert kwargs["system_instruction"] == "Você é um assistente do GuardLLM."
    assert len(kwargs["contents"]) == 1
    assert kwargs["contents"][0]["role"] == "user"
    assert response.output_text == "Entendido, diretrizes seguidas."
