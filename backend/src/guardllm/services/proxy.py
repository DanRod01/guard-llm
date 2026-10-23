import logging
import time
from typing import Any

from guardllm.schemas.injection import InjectionVerdict
from guardllm.schemas.proxy import (
    ProxyAuditMetadata,
    ProxyChatRequest,
    ProxyChatResponse,
    SecurityGateAudit,
)
from guardllm.schemas.sanitization import RedactedEntity
from guardllm.security.injection.detector import (
    InjectionDetector,
    injection_detector,
)
from guardllm.security.sanitization.engine import SanitizerEngine, sanitizer_engine
from guardllm.services.gemini import GeminiClient, gemini_client

logger = logging.getLogger("guardllm.services.proxy")


class PromptInjectionError(Exception):
    """Exceção levantada quando uma tentativa de Prompt Injection é bloqueada."""

    def __init__(self, verdict: InjectionVerdict) -> None:
        super().__init__(
            f"Tentativa de injeção detectada com risco {verdict.risk_score}"
        )
        self.verdict = verdict


class ProxyService:
    """Orquestrador defensivo do Proxy Reversivo GuardLLM.

    Executa inspeção contra Prompt Injection (OWASP LLM01), higienização de entrada
    (Inbound Gate), despacho para o LLM e higienização de saída (Outbound Gate).
    """

    def __init__(
        self,
        sanitizer: SanitizerEngine = sanitizer_engine,
        client: GeminiClient = gemini_client,
        detector: InjectionDetector = injection_detector,
    ) -> None:
        self._sanitizer = sanitizer
        self._client = client
        self._injection_detector = detector

    def _extract_user_text(self, request: ProxyChatRequest) -> str:
        """Extrai todo o conteúdo textual de entrada para análise anti-injeção.

        Inspeciona tanto `prompt` quanto `messages` conjuntamente para impedir
        tentativas de bypass por sombreamento de campos no payload.
        """
        segments: list[str] = []
        if request.prompt:
            segments.append(request.prompt)
        if request.messages:
            segments.extend(
                msg.content for msg in request.messages if msg.role != "model"
            )
        return " ".join(segments)

    def _prepare_gemini_payload(
        self, request: ProxyChatRequest
    ) -> tuple[list[dict[str, Any]], str | None, SecurityGateAudit]:
        """Sanitiza o conteúdo de entrada e o formata para a API do Gemini."""
        all_detected_entities: list[RedactedEntity] = []
        original_total_len = 0
        sanitized_total_len = 0

        sanitized_segments: list[str] = []
        system_instruction: str | None = None
        contents: list[dict[str, Any]] = []

        if request.prompt is not None:
            original_total_len += len(request.prompt)
            inbound_res = self._sanitizer.sanitize(request.prompt)
            sanitized_total_len += len(inbound_res.sanitized_text)
            all_detected_entities.extend(inbound_res.entities_detected)
            sanitized_segments.append(inbound_res.sanitized_text)

            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": inbound_res.sanitized_text}],
                }
            )

        if request.messages is not None:
            for msg in request.messages:
                original_total_len += len(msg.content)
                inbound_res = self._sanitizer.sanitize(msg.content)
                sanitized_total_len += len(inbound_res.sanitized_text)
                all_detected_entities.extend(inbound_res.entities_detected)
                sanitized_segments.append(inbound_res.sanitized_text)

                if msg.role == "system":
                    system_instruction = inbound_res.sanitized_text
                else:
                    gemini_role = (
                        "model" if msg.role in ("assistant", "model") else "user"
                    )
                    contents.append(
                        {
                            "role": gemini_role,
                            "parts": [{"text": inbound_res.sanitized_text}],
                        }
                    )

        inbound_audit = SecurityGateAudit(
            sanitized=len(all_detected_entities) > 0,
            entities_redacted=all_detected_entities,
            original_length=original_total_len,
            sanitized_length=sanitized_total_len,
            sanitized_preview=(
                "\n".join(sanitized_segments) if sanitized_segments else None
            ),
        )

        return contents, system_instruction, inbound_audit

    def _simulate_llm_response(self, sanitized_prompt: str) -> dict[str, Any]:
        """Motor de simulação determinística local (Sandbox Mode).

        Permite validar o pipeline Dual-Gate (incluindo Outbound Gate contra
        vazamento de credenciais pela própria LLM) sem chamadas externas.
        """
        lower_prompt = sanitized_prompt.lower()
        if any(
            kw in lower_prompt
            for kw in ("outbound", "alucina", "credencial interna", "debug dump")
        ):
            simulated_key = "AIzaSy" + "D9a8B7c6E5f4G3h2I1j0K9l8M7n6O5p4Q"
            simulated_text = (
                "Relatório de diagnóstico gerado pelo modelo:\n"
                f"- Chave de serviço: {simulated_key}\n"
                "- Responsável técnico (CPF): 529.982.247-25\n"
                "- Contato interno: secops@empresa.com.br"
            )
        else:
            simulated_text = (
                "Análise concluída pelo motor Sandbox GuardLLM.\n"
                f'Payload higienizado recebido pela LLM: "{sanitized_prompt}"\n\n'
                "Nenhum dado sensível original transitou para o provedor."
            )

        prompt_tok = max(8, len(sanitized_prompt.split()) * 2)
        cand_tok = max(12, len(simulated_text.split()) * 2)
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": simulated_text}],
                        "role": "model",
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": prompt_tok,
                "candidatesTokenCount": cand_tok,
                "totalTokenCount": prompt_tok + cand_tok,
            },
        }

    async def process_chat(self, request: ProxyChatRequest) -> ProxyChatResponse:
        """Executa o pipeline defensivo completo ponta a ponta."""
        start_time = time.perf_counter()

        # 1. Inspeção contra Prompt Injection e Jailbreak (OWASP LLM01)
        user_text = self._extract_user_text(request)
        injection_verdict = self._injection_detector.detect(user_text)

        if injection_verdict.is_injection and request.block_on_injection:
            logger.warning(
                "Ataque de Prompt Injection neutralizado na borda! Score: %.2f",
                injection_verdict.risk_score,
            )
            raise PromptInjectionError(injection_verdict)

        # 2. Inbound Sanitization Gate (Proteção de PII e Segredos)
        contents, system_instruction, inbound_audit = self._prepare_gemini_payload(
            request
        )

        if inbound_audit.sanitized:
            logger.info(
                "Inbound Gate neutralizou %d PII(s)/segredo(s) no prompt.",
                len(inbound_audit.entities_redacted),
            )

        # 3. Execução Segura no Provedor Upstream (Gemini) ou Sandbox Local
        if request.simulate_upstream:
            gemini_response = self._simulate_llm_response(
                inbound_audit.sanitized_preview or ""
            )
        else:
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

        # 4. Outbound Sanitization Gate (Proteção de Saída)
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
                sanitized_preview=final_text,
            )
            if outbound_audit.sanitized:
                logger.warning(
                    "Outbound Gate bloqueou vazamento de %d PII(s) na resposta da LLM!",
                    len(outbound_audit.entities_redacted),
                )

        # 5. Métricas e Auditoria LLMOps
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if request.simulate_upstream:
            target_model = "guardllm-sandbox-simulator"
        else:
            target_model = request.model or self._client._settings.GEMINI_MODEL

        security_metadata = ProxyAuditMetadata(
            inbound_audit=inbound_audit,
            outbound_audit=outbound_audit,
            injection_audit=injection_verdict,
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
