from dataclasses import dataclass

from guardllm.schemas.sanitization import PIIType, RedactedEntity, SanitizationResult
from guardllm.security.sanitization.rules import (
    API_KEY_PATTERNS,
    CPF_PATTERN,
    CREDIT_CARD_PATTERN,
    EMAIL_PATTERN,
    validate_cpf_checksum,
    validate_luhn_checksum,
)


@dataclass(frozen=True)
class _CandidateSpan:
    start: int
    end: int
    entity_type: PIIType
    masked_value: str


class SanitizerEngine:
    """Motor defensivo de sanitização e mascaramento de PII e segredos."""

    def sanitize(self, text: str) -> SanitizationResult:
        """Inspeciona o texto, detecta PII e substitui por marcadores seguros."""
        if not text:
            return SanitizationResult(sanitized_text="")

        candidates: list[_CandidateSpan] = []

        # 1. Detecção de Chaves de API e Segredos
        for pattern in API_KEY_PATTERNS:
            for match in pattern.finditer(text):
                candidates.append(
                    _CandidateSpan(
                        start=match.start(),
                        end=match.end(),
                        entity_type=PIIType.API_KEY,
                        masked_value="[REDACTED_API_KEY]",
                    )
                )

        # 2. Detecção de E-mails
        for match in EMAIL_PATTERN.finditer(text):
            candidates.append(
                _CandidateSpan(
                    start=match.start(),
                    end=match.end(),
                    entity_type=PIIType.EMAIL,
                    masked_value="[REDACTED_EMAIL]",
                )
            )

        # 3. Detecção e Validação Algorítmica de CPFs (Módulo 11)
        for match in CPF_PATTERN.finditer(text):
            raw_match = match.group()
            if validate_cpf_checksum(raw_match):
                candidates.append(
                    _CandidateSpan(
                        start=match.start(),
                        end=match.end(),
                        entity_type=PIIType.CPF,
                        masked_value="[REDACTED_CPF]",
                    )
                )

        # 4. Detecção e Validação Algorítmica de Cartões de Crédito (Luhn)
        for match in CREDIT_CARD_PATTERN.finditer(text):
            raw_match = match.group()
            if validate_luhn_checksum(raw_match):
                candidates.append(
                    _CandidateSpan(
                        start=match.start(),
                        end=match.end(),
                        entity_type=PIIType.CREDIT_CARD,
                        masked_value="[REDACTED_CREDIT_CARD]",
                    )
                )

        # Resolução de conflitos de sobreposição (Overlapping Spans)
        # Prioriza candidatos por ordem de início e maior comprimento
        candidates.sort(key=lambda s: (s.start, -(s.end - s.start)))

        non_overlapping: list[_CandidateSpan] = []
        last_end = 0

        for candidate in candidates:
            if candidate.start >= last_end:
                non_overlapping.append(candidate)
                last_end = candidate.end

        # Reconstrução do texto sanitizado
        reconstructed_parts: list[str] = []
        detected_entities: list[RedactedEntity] = []
        current_idx = 0

        for span in non_overlapping:
            reconstructed_parts.append(text[current_idx : span.start])
            reconstructed_parts.append(span.masked_value)

            detected_entities.append(
                RedactedEntity(
                    entity_type=span.entity_type,
                    masked_value=span.masked_value,
                    start_index=span.start,
                    end_index=span.end,
                )
            )
            current_idx = span.end

        reconstructed_parts.append(text[current_idx:])
        sanitized_text = "".join(reconstructed_parts)

        return SanitizationResult(
            sanitized_text=sanitized_text,
            entities_detected=detected_entities,
        )


sanitizer_engine = SanitizerEngine()
