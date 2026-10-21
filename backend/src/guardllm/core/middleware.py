import re
import uuid
from contextvars import ContextVar

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# ContextVar assíncrono para acesso global e seguro ao ID de correlação
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

# Validador sanitizado de ID de correlação para evitar Header Injection
_VALID_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

# Cabeçalhos defensivos padrão OWASP contra sniffing, clickjacking e cache de PII
_SECURITY_HEADERS: tuple[tuple[str, str], ...] = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Cache-Control", "no-store"),
)


def get_correlation_id() -> str:
    """Retorna o Correlation ID da requisição corrente no contexto assíncrono."""
    return correlation_id_ctx.get()


class CorrelationIdMiddleware:
    """Pure ASGI Middleware de rastreabilidade distribuída e hardening HTTP.

    Implementado diretamente sobre o protocolo ASGI (sem BaseHTTPMiddleware)
    para evitar cópias de stream em memória e overhead de task groups.
    Injeta X-Correlation-ID e cabeçalhos defensivos OWASP na resposta.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req_headers = Headers(scope=scope)
        incoming_id = req_headers.get("X-Correlation-ID") or req_headers.get(
            "X-Request-ID"
        )

        if incoming_id and _VALID_ID_PATTERN.match(incoming_id):
            correlation_id = incoming_id
        else:
            correlation_id = uuid.uuid4().hex

        token = correlation_id_ctx.set(correlation_id)
        scope.setdefault("state", {})["correlation_id"] = correlation_id

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                resp_headers = MutableHeaders(scope=message)
                resp_headers["X-Correlation-ID"] = correlation_id
                for header_name, header_value in _SECURITY_HEADERS:
                    if header_name not in resp_headers:
                        resp_headers[header_name] = header_value
            await send(message)

        try:
            await self.app(scope, receive, send_with_security_headers)
        finally:
            correlation_id_ctx.reset(token)
