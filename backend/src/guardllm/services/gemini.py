import logging
from typing import Any

import httpx

from guardllm.core.config import Settings, settings

logger = logging.getLogger("guardllm.services.gemini")


class GeminiError(Exception):
    """Exceção base para falhas de integração com o Google Gemini."""


class GeminiConfigError(GeminiError):
    """Exceção lançada quando a chave de API ou configuração está ausente."""


class GeminiAPIError(GeminiError):
    """Exceção lançada quando o upstream do Gemini retorna status de erro."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Gemini API upstream error ({status_code}): {message}")
        self.status_code = status_code
        self.message = message


class GeminiTimeoutError(GeminiError):
    """Exceção lançada quando o upstream do Gemini atinge o tempo limite."""


class GeminiClient:
    """Cliente HTTP assíncrono defensivo para comunicação com a API do Google Gemini."""

    def __init__(
        self,
        app_settings: Settings = settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = app_settings
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        """Retorna o cliente HTTP assíncrono com pooling ativo."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=self._settings.LLM_REQUEST_TIMEOUT_SECONDS,
                    connect=5.0,
                )
            )
        return self._client

    async def close(self) -> None:
        """Encerra graciosamente o pool de conexões HTTP."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _prepare_headers(self) -> dict[str, str]:
        """Prepara cabeçalhos de autenticação via header seguro (não query params)."""
        api_key = self._settings.GEMINI_API_KEY
        if not api_key:
            raise GeminiConfigError(
                "GEMINI_API_KEY não está configurada no ambiente do GuardLLM."
            )
        return {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        contents: list[dict[str, Any]],
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Constrói o payload JSON estrito em conformidade com a API REST do Gemini."""
        payload: dict[str, Any] = {"contents": contents}

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature

        if generation_config:
            payload["generationConfig"] = generation_config

        return payload

    async def generate_content(
        self,
        contents: list[dict[str, Any]],
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Dispara requisição de inferência ao Gemini com resiliência e fail-closed."""
        target_model = model or self._settings.GEMINI_MODEL
        url = (
            f"{self._settings.GEMINI_API_BASE_URL.rstrip('/')}/models/"
            f"{target_model}:generateContent"
        )
        headers = self._prepare_headers()
        payload = self._build_payload(contents, system_instruction, temperature)

        try:
            response = await self.client.post(
                url,
                headers=headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            logger.error("Timeout ao contatar Gemini upstream em %s", url)
            raise GeminiTimeoutError(
                "Tempo limite esgotado ao aguardar o modelo."
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Erro de transporte de rede ao contatar Gemini: %s", exc)
            raise GeminiAPIError(
                503, "Falha de rede ao conectar com o provedor de LLM."
            ) from exc

        if response.status_code != 200:
            logger.warning(
                "Gemini retornou código de erro HTTP %d: %s",
                response.status_code,
                response.text,
            )
            raise GeminiAPIError(response.status_code, response.text)

        data: dict[str, Any] = response.json()
        return data


# Instância singleton para ser injetada e reutilizada
gemini_client = GeminiClient()
