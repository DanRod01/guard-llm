from fastapi import APIRouter

from guardllm.api.v1.endpoints import health, sanitization

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(
    sanitization.router,
    prefix="/security",
    tags=["Security Sanitization"],
)
