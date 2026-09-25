import logging
import time
from typing import Any

from guardllm.schemas.proxy import (
    ProxyAuditMetadata,
    ProxyChatRequest,
    ProxyChatResponse,
    SecurityGateAudit,
)
from guardllm.schemas.sanitization import RedactedEntity
from guardllm.security.sanitization.engine import SanitizerEngine, sanitizer_engine
from guardllm.services.gemini import GeminiClient, gemini_client

logger = logging.getLogger("guardllm.services.proxy")


class ProxyService:
    """Orquestrador defensivo do Proxy Reversivo GuardLLM.

    Executa a higienização de entrada (Inbound Gate), despacha para o modelo de LLM
    e higieniza a resposta gerada (Outbound Gate).
    """

    def __init__(
        self,
        sanitizer: SanitizerEngine = sanitizer_engine,
        client: GeminiClient = gemini_client,
    ) -> None:
        self._sanitizer = sanitizer
        self._client = client

    def _prepare_gemini_payload(
        self, request: ProxyChatRequest
    ) -> tuple[list[dict[str, Any]], str | None, SecurityGateAudit]:
        """Sanitiza o conteúdo de entrada e o formata para a API do Gemini."""
        all_detected_entities: list[RedactedEntity] = []
        original_total_len = 0
        sanitized_total_len = 0

        system_instruction: str | None = None
        contents: list[dict[str, Any]] = []

        if request.prompt is not None:
            original_total_len = len(request.prompt)
            inbound_res = self._sanitizer.sanitize(request.prompt)
            sanitized_total_len = len(inbound_res.sanitized_text)
            all_detected_entities.extend(inbound_res.entities_detected)

            contents.append({
                "role": "user",
                "parts": [{"text": inbound_res.sanitized_text}],
            })

        elif request.messages is not None:
            for msg in request.messages:
                original_total_len += len(msg.content)
                inbound_res = self._sanitizer.sanitize(msg.content)
                sanitized_total_len += len(inbound_res.sanitized_text)
                all_detected_entities.extend(inbound_res.entities_detected)

                if msg.role == "system":
                    # Diretiva de sistema para o modelo
                    system_instruction = inbound_res.sanitized_text
                else:
                    gemini_role = (
                        "model"
                        if msg.role in ("assistant", "model")
                        else "user"
                    )
                    contents.append({
                        "role": gemini_role,
                        "parts": [{"text": inbound_res.sanitized_text}],
                    })

        inbound_audit = SecurityGateAudit(
            sanitized=len(all_detected_entities) > 0,
            entities_redacted=all_detected_entities,
            original_length=original_total_len,
            sanitized_length=sanitized_total_len,
        )

        return contents, system_instruction, inbound_audit

    async def process_chat(self, request: ProxyChatRequest) -> ProxyChatResponse:
        """Executa o pipeline defensivo completo ponta a ponta."""
        start_time = time.perf_counter()

        # 1. Inbound Sanitization Gate (Proteção de Entrada)
        contents, system_instruction, inbound_audit = self._prepare_gemini_payload(
            request
        )

        if inbound_audit.sanitized:
            logger.info(
                "Inbound Gate neutralizou %d PII(s)/segredo(s) no prompt.",
                len(inbound_audit.entities_redacted),
            )

        # 2. Execução Segura no Provedor Upstream (Gemini)
        gemini_response = await self._client.generate_content(
            contents=contents,
            model=request.model,
            system_instruction=system_instruction,
            temperature=request.temperature,
        )

        # Extração de texto e uso de tokens
        raw_text = ""
        candidates = gemini_response.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts and "text" in parts[0]:
                raw_text = parts[0]["text"]

        usage = gemini_response.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount")
        candidate_tokens = usage.get("candidatesTokenCount")
        total_tokens = usage.get("totalTokenCount")

        # 3. Outbound Sanitization Gate (Proteção de Saída)
        outbound_audit: SecurityGateAudit | None = None
        final_text = raw_text

        if request.sanitize_outbound and raw_text:
            outbound_res = self._sanitizer.sanitize(raw_text)
            final_text = outbound_res.sanitized_text
            outbound_audit = SecurityGateAudit(
                sanitized=len(outbound_res.entities_detected) > 0,
                entities_redacted=outbound_res.entities_detected,
                original_length=len(raw_text),
                sanitized_length=len(final_text),
            )
            if outbound_audit.sanitized:
                logger.warning(
                    "Outbound Gate bloqueou vazamento de %d PII(s) na resposta da LLM!",
                    len(outbound_audit.entities_redacted),
                )

        # 4. Métricas e Auditoria LLMOps
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        target_model = request.model or self._client._settings.GEMINI_MODEL

        security_metadata = ProxyAuditMetadata(
            inbound_audit=inbound_audit,
            outbound_audit=outbound_audit,
            model_used=target_model,
            latency_ms=round(elapsed_ms, 2),
            prompt_tokens=prompt_tokens,
            candidate_tokens=candidate_tokens,
            total_tokens=total_tokens,
        )

        return ProxyChatResponse(
            output_text=final_text,
            security=security_metadata,
        )


proxy_service = ProxyService()
