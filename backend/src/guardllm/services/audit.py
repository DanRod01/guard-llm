import json
import logging
from collections import deque
from threading import Lock
from typing import Any

from guardllm.core.middleware import get_correlation_id
from guardllm.schemas.audit import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditStats,
    SecurityAuditDetails,
    TokenUsage,
)
from guardllm.schemas.injection import InjectionVerdict
from guardllm.schemas.proxy import ProxyChatResponse

logger = logging.getLogger("guardllm.audit")


class AuditLogger:
    """Emissor defensivo de logs de auditoria estruturados em JSON para SIEM.

    Garante conformidade com LGPD/GDPR e mitiga CWE-532 (proibição absoluta
    de gravação de credenciais ou dados sensíveis em texto claro nos logs).
    Mantém também um buffer circular (ring buffer) de telemetria em memória
    para consulta pelo Dashboard de Monitoramento da Fase 6.
    """

    def __init__(self, max_events: int = 100) -> None:
        self._events: deque[AuditEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def emit_event(self, event: AuditEvent) -> None:
        """Serializa o evento em JSON estrito e o armazena no buffer de telemetria."""
        with self._lock:
            self._events.appendleft(event)

        payload: dict[str, Any] = event.model_dump(mode="json")
        json_log = json.dumps(payload, ensure_ascii=False)

        if event.severity == AuditSeverity.CRITICAL:
            logger.critical("%s", json_log)
        elif event.severity == AuditSeverity.WARNING:
            logger.warning("%s", json_log)
        else:
            logger.info("%s", json_log)

    def get_recent_events(self, limit: int = 50) -> list[AuditEvent]:
        """Retorna os eventos mais recentes do buffer circular (mais novos primeiro)."""
        with self._lock:
            clamped_limit = max(1, min(limit, len(self._events)))
            return list(self._events)[:clamped_limit]

    def get_stats(self) -> AuditStats:
        """Calcula métricas agregadas dos eventos contidos no buffer circular."""
        with self._lock:
            events = list(self._events)

        total_events = len(events)
        if total_events == 0:
            return AuditStats()

        transactions_success = 0
        injections_blocked = 0
        pii_redacted = 0
        upstream_errors = 0
        total_tokens = 0
        latencies: list[float] = []

        for e in events:
            if e.event_type == AuditEventType.TRANSACTION_SUCCESS:
                transactions_success += 1
            elif e.event_type == AuditEventType.PROMPT_INJECTION_BLOCKED:
                injections_blocked += 1
            elif e.event_type == AuditEventType.PII_REDACTED:
                pii_redacted += 1
            elif e.event_type == AuditEventType.UPSTREAM_ERROR:
                upstream_errors += 1

            if e.token_usage and e.token_usage.total_tokens is not None:
                total_tokens += e.token_usage.total_tokens

            if e.latency_ms is not None:
                latencies.append(e.latency_ms)

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return AuditStats(
            total_events=total_events,
            transactions_success=transactions_success,
            injections_blocked=injections_blocked,
            pii_redacted=pii_redacted,
            upstream_errors=upstream_errors,
            total_tokens=total_tokens,
            average_latency_ms=round(avg_latency, 2),
        )

    def clear(self) -> None:
        """Limpa o buffer em memória (útil para suíte de testes)."""
        with self._lock:
            self._events.clear()

    def log_injection_blocked(
        self,
        verdict: InjectionVerdict,
        client_ip: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Emite evento de segurança crítico para Prompt Injection neutralizado."""
        cid = correlation_id or get_correlation_id()
        security_details = SecurityAuditDetails(
            injection_detected=True,
            injection_risk_score=verdict.risk_score,
            injection_categories=[c.value for c in verdict.categories],
        )

        event = AuditEvent(
            correlation_id=cid,
            event_type=AuditEventType.PROMPT_INJECTION_BLOCKED,
            severity=AuditSeverity.CRITICAL,
            http_status=403,
            client_ip=client_ip,
            security=security_details,
            message=(
                f"Ataque de Prompt Injection neutralizado na borda. "
                f"Score: {verdict.risk_score:.2f} | Categorias: {verdict.categories}"
            ),
        )
        self.emit_event(event)
        return event

    def log_transaction_success(
        self,
        response: ProxyChatResponse,
        http_status: int = 200,
        client_ip: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Emite evento de transação bem-sucedida com telemetria FinOps e segurança."""
        cid = correlation_id or get_correlation_id()
        sec = response.security

        inbound_entities = [
            e.entity_type.value for e in sec.inbound_audit.entities_redacted
        ]
        outbound_entities = (
            [e.entity_type.value for e in sec.outbound_audit.entities_redacted]
            if sec.outbound_audit
            else []
        )

        has_pii = sec.inbound_audit.sanitized or (
            sec.outbound_audit is not None and sec.outbound_audit.sanitized
        )
        event_type = (
            AuditEventType.PII_REDACTED
            if has_pii
            else AuditEventType.TRANSACTION_SUCCESS
        )
        severity = AuditSeverity.WARNING if has_pii else AuditSeverity.INFO

        security_details = SecurityAuditDetails(
            inbound_entities_count=len(inbound_entities),
            inbound_entity_types=inbound_entities,
            outbound_entities_count=len(outbound_entities),
            outbound_entity_types=outbound_entities,
            injection_detected=sec.injection_audit.is_injection,
            injection_risk_score=sec.injection_audit.risk_score,
            injection_categories=[c.value for c in sec.injection_audit.categories],
        )

        token_usage = TokenUsage(
            prompt_tokens=sec.prompt_tokens,
            candidate_tokens=sec.candidate_tokens,
            total_tokens=sec.total_tokens,
        )

        event = AuditEvent(
            correlation_id=cid,
            event_type=event_type,
            severity=severity,
            http_status=http_status,
            client_ip=client_ip,
            model=sec.model_used,
            latency_ms=sec.latency_ms,
            security=security_details,
            token_usage=token_usage,
            message=(
                f"Transação LLM concluída. Latência: {sec.latency_ms:.1f}ms | "
                f"Tokens: {sec.total_tokens} | "
                f"PIIs: {len(inbound_entities) + len(outbound_entities)}"
            ),
        )
        self.emit_event(event)
        return event

    def log_upstream_error(
        self,
        status_code: int,
        error_message: str,
        client_ip: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Emite evento de erro upstream sem vazar dados confidenciais."""
        cid = correlation_id or get_correlation_id()
        severity = (
            AuditSeverity.WARNING if status_code < 500 else AuditSeverity.CRITICAL
        )
        event = AuditEvent(
            correlation_id=cid,
            event_type=AuditEventType.UPSTREAM_ERROR,
            severity=severity,
            http_status=status_code,
            client_ip=client_ip,
            security=SecurityAuditDetails(),
            message=f"Falha de comunicação upstream com LLM: {error_message}",
        )
        self.emit_event(event)
        return event


audit_logger = AuditLogger()
