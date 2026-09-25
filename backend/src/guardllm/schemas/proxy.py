from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from guardllm.schemas.sanitization import RedactedEntity


class ChatMessage(BaseModel):
    """Representação de uma mensagem no diálogo."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["user", "model", "assistant", "system"] = Field(
        ...,
        description="Papel do remetente da mensagem",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Conteúdo textual da mensagem",
    )


class ProxyChatRequest(BaseModel):
    """Payload de entrada para o Proxy Reversivo GuardLLM."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt: str | None = Field(
        default=None,
        description="Prompt de texto simples a ser enviado à LLM",
    )
    messages: list[ChatMessage] | None = Field(
        default=None,
        description="Histórico de mensagens de chat estruturado",
    )
    model: str | None = Field(
        default=None,
        description="Identificador do modelo LLM (ex: gemini-1.5-flash)",
    )
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Temperatura de amostragem para a geração",
    )
    sanitize_outbound: bool = Field(
        default=True,
        description="Se verdadeiro, também inspeciona e mascara a resposta do modelo",
    )

    @model_validator(mode="after")
    def validate_content_presence(self) -> "ProxyChatRequest":
        """Garante que ao menos um prompt ou histórico de mensagens foi enviado."""
        if not self.prompt and not self.messages:
            raise ValueError(
                "Pelo menos um dos campos 'prompt' ou 'messages' deve ser fornecido."
            )
        return self


class SecurityGateAudit(BaseModel):
    """Auditoria detalhada de passagem por portão de segurança (Inbound/Outbound)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sanitized: bool = Field(
        description="Indica se alguma entidade sensível foi encontrada e mascarada",
    )
    entities_redacted: list[RedactedEntity] = Field(
        default_factory=list,
        description="Lista de entidades PII ou segredos mascarados",
    )
    original_length: int = Field(description="Comprimento original do texto")
    sanitized_length: int = Field(description="Comprimento do texto após sanitização")


class ProxyAuditMetadata(BaseModel):
    """Metadados de observabilidade, segurança e LLMOps da transação."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    inbound_audit: SecurityGateAudit = Field(
        description="Relatório de segurança do prompt de entrada",
    )
    outbound_audit: SecurityGateAudit | None = Field(
        default=None,
        description="Relatório de segurança da resposta da LLM",
    )
    model_used: str = Field(description="Nome do modelo utilizado na inferência")
    latency_ms: float = Field(
        description="Latência total da requisição em milissegundos",
    )
    prompt_tokens: int | None = Field(
        default=None,
        description="Quantidade de tokens de entrada processados",
    )
    candidate_tokens: int | None = Field(
        default=None,
        description="Quantidade de tokens gerados pelo modelo",
    )
    total_tokens: int | None = Field(
        default=None,
        description="Total de tokens consumidos na requisição",
    )


class ProxyChatResponse(BaseModel):
    """Resposta defensiva entregue pelo GuardLLM ao cliente final."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    output_text: str = Field(
        description="Resposta gerada pela LLM (devidamente higienizada)",
    )
    security: ProxyAuditMetadata = Field(
        description="Metadados completos de segurança e auditoria LLMOps",
    )
