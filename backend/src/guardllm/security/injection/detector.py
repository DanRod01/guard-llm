import logging

from guardllm.schemas.injection import InjectionCategory, InjectionVerdict
from guardllm.security.injection.patterns import (
    INJECTION_RULES,
    normalize_text,
)

logger = logging.getLogger("guardllm.security.injection")


class InjectionDetector:
    """Motor heurístico de inspeção e scoring de risco (OWASP LLM01)."""

    def __init__(self, default_threshold: float = 0.6) -> None:
        self.default_threshold = default_threshold

    def detect(self, text: str, threshold: float | None = None) -> InjectionVerdict:
        """Inspeciona texto contra assinaturas de injeção e calcula risco ponderado.

        A computação é executada em tempo sub-milissegundo na CPU via expressões
        pré-compiladas e união probabilística saturada de pesos.
        """
        if not text or not text.strip():
            return InjectionVerdict(
                is_injection=False,
                risk_score=0.0,
                categories=[],
                matched_patterns=[],
            )

        active_threshold = (
            threshold if threshold is not None else self.default_threshold
        )
        normalized = normalize_text(text)

        matched_weights: list[float] = []
        matched_categories: set[InjectionCategory] = set()
        matched_patterns: list[str] = []

        for rule in INJECTION_RULES:
            if rule.regex.search(normalized):
                matched_weights.append(rule.weight)
                matched_categories.add(rule.category)
                matched_patterns.append(rule.pattern_id)

        if not matched_weights:
            return InjectionVerdict(
                is_injection=False,
                risk_score=0.0,
                categories=[],
                matched_patterns=[],
            )

        # União probabilística saturada de risco: 1 - Prod(1 - w_i)
        # Garante que múltiplos indícios aumentem o risco sem extrapolar 1.0
        complement_product = 1.0
        for w in matched_weights:
            complement_product *= 1.0 - w

        combined_risk = round(1.0 - complement_product, 2)
        is_injection = combined_risk >= active_threshold

        if is_injection:
            logger.warning(
                "Prompt Injection detectado! Score: %.2f | Cats: %s | Padrões: %s",
                combined_risk,
                [c.value for c in matched_categories],
                matched_patterns,
            )

        return InjectionVerdict(
            is_injection=is_injection,
            risk_score=combined_risk,
            categories=sorted(list(matched_categories)),
            matched_patterns=matched_patterns,
        )


injection_detector = InjectionDetector()
