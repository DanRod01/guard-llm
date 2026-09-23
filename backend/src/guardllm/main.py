import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from guardllm.api.v1.router import api_router
from guardllm.core.config import settings

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("guardllm")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan event handler for startup and shutdown procedures."""
    logger.info(
        "GuardLLM Gateway starting up | Environment: %s | Version: %s",
        settings.ENVIRONMENT,
        settings.VERSION,
    )
    yield
    logger.info("GuardLLM Gateway shutting down gracefully...")


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Defensive Security Reverse Proxy for LLMs in Production.",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # Restrictive CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # API Version 1 Router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app: FastAPI = create_application()
