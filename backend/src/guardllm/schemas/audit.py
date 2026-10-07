from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AuditEventType(StrEnum):
    """Categorias taxonômicas de eventos de auditoria para ingestão em SIEM."""

    TRANSACTION_SUCCESS = "TRANSACTION_SUCCESS"
    PROMPT_INJECTION_BLOCKED = "PROMPT_INJECTION_BLOCKED"
    PII_REDACTED = "PII_REDACTED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"


class AuditSeverity(StrEnum):
    """Níveis de severidade alinhados ao syslog e padrões SecOps."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class TokenUsage(BaseModel):
    """Métricas de consumo de tokens para controle FinOps e contabilidade."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: int | None = Field(
        default=None,
        description="Tokens consumidos pelo prompt de entrada",
    )
    candidate_tokens: int | None = Field(
        default=None,
        description="Tokens gerados pelo modelo",
    )
    total_tokens: int | None = Field(
        default=None,
        description="Total consolidado de tokens da transação",
    )


class SecurityAuditDetails(BaseModel):
    """Metadados de segurança higienizados (CWE-532: Zero Plaintext PII)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    inbound_entities_count: int = Field(
        default=0,
        description="Total de PIIs ou segredos mascarados no prompt",
    )
    inbound_entity_types: list[str] = Field(
        default_factory=list,
        description="Tipos de entidades identificadas na entrada (ex: CPF, EMAIL)",
    )
    outbound_entities_count: int = Field(
        default=0,
        description="Total de PIIs mascaradas na resposta do modelo",
    )
    outbound_entity_types: list[str] = Field(
        default_factory=list,
        description="Tipos de entidades identificadas na saída",
    )
    injection_detected: bool = Field(
        default=False,
        description="Indica se houve detecção de Prompt Injection (OWASP LLM01)",
    )
    injection_risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Pontuação de risco de injeção",
    )
    injection_categories: list[str] = Field(
        default_factory=list,
        description="Categorias de injeção detectadas",
    )


class AuditEvent(BaseModel):
    """Evento imutável de auditoria estruturado para SIEM e OpenTelemetry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp ISO 8601 em UTC da ocorrência",
    )
    correlation_id: str = Field(
        description="Identificador único para rastreamento distribuído",
    )
    event_type: AuditEventType = Field(
        description="Tipo canônico do evento de auditoria",
    )
    severity: AuditSeverity = Field(
        description="Severidade do evento de segurança",
    )
    http_status: int = Field(
        description="Código de status HTTP retornado ao cliente",
    )
    client_ip: str | None = Field(
        default=None,
        description="Endereço IP do cliente requisitante",
    )
    model: str | None = Field(
        default=None,
        description="Identificador do modelo LLM envolvido",
    )
    latency_ms: float | None = Field(
        default=None,
        description="Latência total da transação em milissegundos",
    )
    security: SecurityAuditDetails = Field(
        description="Detalhes higienizados de segurança",
    )
    token_usage: TokenUsage | None = Field(
        default=None,
        description="Métricas de tokens, se aplicável",
    )
    message: str = Field(
        description="Mensagem resumida do evento para analistas de SOC",
    )
