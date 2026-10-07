import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from guardllm.schemas.proxy import (
    PromptInjectionBlockedResponse,
    ProxyChatRequest,
    ProxyChatResponse,
)
from guardllm.services.audit import audit_logger
from guardllm.services.gemini import (
    GeminiAPIError,
    GeminiConfigError,
    GeminiTimeoutError,
)
from guardllm.services.proxy import PromptInjectionError, proxy_service

logger = logging.getLogger("guardllm.api.proxy")

router = APIRouter()


def _get_client_ip(request: Request) -> str | None:
    """Extrai o IP do cliente considerando proxies reversos ou socket direto."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


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
    request: Request,
) -> ProxyChatResponse | JSONResponse:
    """Intermediário seguro de comunicação com a LLM."""
    client_ip = _get_client_ip(request)

    try:
        response = await proxy_service.process_chat(payload)
        audit_logger.log_transaction_success(
            response=response,
            http_status=status.HTTP_200_OK,
            client_ip=client_ip,
        )
        return response
    except PromptInjectionError as exc:
        audit_logger.log_injection_blocked(
            verdict=exc.verdict,
            client_ip=client_ip,
        )
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
        audit_logger.log_upstream_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_message="Chave de API ausente ou inválida",
            client_ip=client_ip,
        )
        logger.error("Falha de configuração do provedor de LLM: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Provedor de LLM indisponível devido a chave de API ausente/inválida."
            ),
        ) from exc
    except GeminiTimeoutError as exc:
        audit_logger.log_upstream_error(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_message="Timeout ao contatar provedor upstream",
            client_ip=client_ip,
        )
        logger.error("Timeout na comunicação com o provedor de LLM: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O provedor de LLM demorou muito para responder.",
        ) from exc
    except GeminiAPIError as exc:
        audit_logger.log_upstream_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_message=f"Erro retornado pelo upstream ({exc.status_code})",
            client_ip=client_ip,
        )
        logger.error(
            "Erro upstream do provedor de LLM (%d): %s",
            exc.status_code,
            exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro retornado pelo provedor upstream de LLM ({exc.status_code}).",
        ) from exc
