from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class InjectionCategory(StrEnum):
    """Categorias de ataques de Prompt Injection e Jailbreak (OWASP LLM01)."""

    SYSTEM_OVERRIDE = "SYSTEM_OVERRIDE"
    ROLEPLAY_JAILBREAK = "ROLEPLAY_JAILBREAK"
    SYSTEM_LEAK = "SYSTEM_LEAK"
    DELIMITER_HIJACK = "DELIMITER_HIJACK"


class InjectionDetectRequest(BaseModel):
    """Payload de entrada para inspeção de Prompt Injection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(
        ...,
        min_length=1,
        description="Texto do prompt a ser inspecionado contra injeção",
    )
    threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Limiar de pontuação para determinar bloqueio (default: 0.6)",
    )


class InjectionVerdict(BaseModel):
    """Resultado imutável da análise de segurança contra Prompt Injection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_injection: bool = Field(
        description="Veredito indicando se o prompt representa uma tentativa de ataque",
    )
    risk_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Pontuação ponderada de risco calculada entre 0.0 e 1.0",
    )
    categories: list[InjectionCategory] = Field(
        default_factory=list,
        description="Categorias de injeção detectadas na análise",
    )
    matched_patterns: list[str] = Field(
        default_factory=list,
        description="Identificadores dos padrões maliciosos acionados",
    )
