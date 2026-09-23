from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PIIType(StrEnum):
    """Categorias de PII detectáveis pelo GuardLLM."""

    CPF = "CPF"
    EMAIL = "EMAIL"
    CREDIT_CARD = "CREDIT_CARD"
    API_KEY = "API_KEY"


class RedactedEntity(BaseModel):
    """Metadados de uma entidade sensível detectada e mascarada."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_type: PIIType = Field(description="Tipo de dado sensível detectado")
    masked_value: str = Field(description="Token de substituição seguro")
    start_index: int = Field(description="Índice de início no texto original")
    end_index: int = Field(description="Índice de fim no texto original")


class SanitizeRequest(BaseModel):
    """Payload de entrada para sanitização de texto."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(
        ...,
        min_length=1,
        description="Texto ou prompt a ser inspecionado contra vazamento de PII",
    )


class SanitizationResult(BaseModel):
    """Resultado imutável retornado pelo motor de sanitização."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sanitized_text: str = Field(
        description="Texto com dados sensíveis mascarados",
    )
    entities_detected: list[RedactedEntity] = Field(
        default_factory=list,
        description="Lista de entidades identificadas durante a inspeção",
    )

    @property
    def contains_pii(self) -> bool:
        """Indica se ao menos uma entidade sensível foi encontrada."""
        return len(self.entities_detected) > 0
