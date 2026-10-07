import re
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ContextVar assíncrono para acesso global e seguro ao ID de correlação
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

# Validador sanitizado de ID de correlação para evitar Header Injection
_VALID_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def get_correlation_id() -> str:
    """Retorna o Correlation ID da requisição corrente no contexto assíncrono."""
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware de rastreabilidade distribuída para observabilidade e logs SIEM.

    Intercepta requisições HTTP, propaga ou gera um Correlation ID único,
    armazena no contexto assíncrono e injeta no cabeçalho de resposta.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming_id = request.headers.get("X-Correlation-ID") or request.headers.get(
            "X-Request-ID"
        )

        if incoming_id and _VALID_ID_PATTERN.match(incoming_id):
            correlation_id = incoming_id
        else:
            correlation_id = uuid.uuid4().hex

        # Configura o contexto assíncrono e o estado da requisição
        token = correlation_id_ctx.set(correlation_id)
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
        finally:
            correlation_id_ctx.reset(token)

        # Injeta o cabeçalho padronizado na resposta HTTP
        response.headers["X-Correlation-ID"] = correlation_id
        return response
