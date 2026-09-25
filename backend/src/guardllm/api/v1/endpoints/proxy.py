import logging

from fastapi import APIRouter, HTTPException, status

from guardllm.schemas.proxy import ProxyChatRequest, ProxyChatResponse
from guardllm.services.gemini import (
    GeminiAPIError,
    GeminiConfigError,
    GeminiTimeoutError,
)
from guardllm.services.proxy import proxy_service

logger = logging.getLogger("guardllm.api.proxy")

router = APIRouter()


@router.post(
    "/chat",
    response_model=ProxyChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Proxy Reversivo Defensivo para Chat LLM",
    description=(
        "Higieniza o prompt de entrada (Inbound Gate), despacha para o modelo "
        "e higieniza a resposta gerada (Outbound Gate), garantindo auditoria "
        "e conformidade."
    ),
)
async def proxy_chat(payload: ProxyChatRequest) -> ProxyChatResponse:
    """Intermediário seguro de comunicação com a LLM."""
    try:
        return await proxy_service.process_chat(payload)
    except GeminiConfigError as exc:
        logger.error("Falha de configuração do provedor de LLM: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Provedor de LLM indisponível devido a chave de API ausente/inválida."
            ),
        ) from exc
    except GeminiTimeoutError as exc:
        logger.error("Timeout na comunicação com o provedor de LLM: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O provedor de LLM demorou muito para responder.",
        ) from exc
    except GeminiAPIError as exc:
        logger.error(
            "Erro upstream do provedor de LLM (%d): %s",
            exc.status_code,
            exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro retornado pelo provedor upstream de LLM ({exc.status_code}).",
        ) from exc
