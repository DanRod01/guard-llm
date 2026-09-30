import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from guardllm.schemas.proxy import (
    PromptInjectionBlockedResponse,
    ProxyChatRequest,
    ProxyChatResponse,
)
from guardllm.services.gemini import (
    GeminiAPIError,
    GeminiConfigError,
    GeminiTimeoutError,
)
from guardllm.services.proxy import PromptInjectionError, proxy_service

logger = logging.getLogger("guardllm.api.proxy")

router = APIRouter()


@router.post(
    "/chat",
    response_model=ProxyChatResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": PromptInjectionBlockedResponse},
    },
    summary="Proxy Reversivo Defensivo para Chat LLM",
    description=(
        "Higieniza o prompt de entrada (Inbound Gate), bloqueia tentativas de "
        "injeção (OWASP LLM01), despacha para o modelo e higieniza a resposta "
        "gerada (Outbound Gate)."
    ),
)
async def proxy_chat(
    payload: ProxyChatRequest,
) -> ProxyChatResponse | JSONResponse:
    """Intermediário seguro de comunicação com a LLM."""
    try:
        return await proxy_service.process_chat(payload)
    except PromptInjectionError as exc:
        logger.warning(
            "Prompt Injection bloqueado preventivamente! Score: %.2f",
            exc.verdict.risk_score,
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=PromptInjectionBlockedResponse(
                detail=(
                    "Prompt Injection ou tentativa de Jailbreak "
                    "bloqueada preventivamente pelo GuardLLM."
                ),
                security=exc.verdict,
            ).model_dump(mode="json"),
        )
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
