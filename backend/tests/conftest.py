from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from guardllm.main import app


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Provides an isolated async HTTP client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
