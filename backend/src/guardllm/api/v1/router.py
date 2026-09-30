from fastapi import APIRouter

from guardllm.api.v1.endpoints import health, injection, proxy, sanitization

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(
    sanitization.router,
    prefix="/security",
    tags=["Security Sanitization"],
)
api_router.include_router(
    injection.router,
    prefix="/security/injection",
    tags=["Prompt Injection Defense"],
)
api_router.include_router(
    proxy.router,
    prefix="/proxy",
    tags=["LLM Proxy"],
)
