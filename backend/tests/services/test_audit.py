import json
import logging

import pytest

from guardllm.schemas.audit import AuditEventType, AuditSeverity
from guardllm.schemas.injection import InjectionCategory, InjectionVerdict
from guardllm.schemas.proxy import (
    ProxyAuditMetadata,
    ProxyChatResponse,
    SecurityGateAudit,
)
from guardllm.schemas.sanitization import PIIType, RedactedEntity
from guardllm.services.audit import AuditLogger


def test_audit_logger_log_injection_blocked(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = AuditLogger()
    verdict = InjectionVerdict(
        is_injection=True,
        risk_score=0.98,
        categories=[InjectionCategory.ROLEPLAY_JAILBREAK],
        matched_patterns=["JAILBREAK_DAN_PERSONA"],
    )

    with caplog.at_level(logging.CRITICAL, logger="guardllm.audit"):
        event = logger.log_injection_blocked(
            verdict=verdict,
            client_ip="192.168.1.50",
            correlation_id="test-corr-id-123",
        )

    assert event.event_type == AuditEventType.PROMPT_INJECTION_BLOCKED
    assert event.severity == AuditSeverity.CRITICAL
    assert event.http_status == 403
    assert event.client_ip == "192.168.1.50"
    assert event.security.injection_detected is True
    assert event.security.injection_risk_score == 0.98

    # Verifica se a mensagem foi emitida como JSON válido no logger
    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    parsed_json = json.loads(log_record.message)
    assert parsed_json["correlation_id"] == "test-corr-id-123"
    assert parsed_json["event_type"] == "PROMPT_INJECTION_BLOCKED"


def test_audit_logger_cwe_532_compliance_no_plaintext_pii_leaks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = AuditLogger()
    sensitive_cpf = "529.982.247-25"
    sensitive_email = "confidencial@empresa.com.br"

    inbound_audit = SecurityGateAudit(
        sanitized=True,
        entities_redacted=[
            RedactedEntity(
                entity_type=PIIType.CPF,
                masked_value="[REDACTED_CPF]",
                start_index=0,
                end_index=14,
            ),
            RedactedEntity(
                entity_type=PIIType.EMAIL,
                masked_value="[REDACTED_EMAIL]",
                start_index=15,
                end_index=42,
            ),
        ],
        original_length=50,
        sanitized_length=30,
    )

    injection_verdict = InjectionVerdict(
        is_injection=False,
        risk_score=0.0,
        categories=[],
        matched_patterns=[],
    )

    metadata = ProxyAuditMetadata(
        inbound_audit=inbound_audit,
        outbound_audit=None,
        injection_audit=injection_verdict,
        model_used="gemini-1.5-flash",
        latency_ms=150.5,
        prompt_tokens=25,
        candidate_tokens=10,
        total_tokens=35,
    )

    response = ProxyChatResponse(
        output_text="Resposta segura e higienizada.",
        security=metadata,
    )

    with caplog.at_level(logging.WARNING, logger="guardllm.audit"):
        event = logger.log_transaction_success(
            response=response,
            client_ip="10.0.0.1",
            correlation_id="trace-no-leak-999",
        )

    # 1. Verifica evento estruturado
    assert event.event_type == AuditEventType.PII_REDACTED
    assert event.severity == AuditSeverity.WARNING
    assert event.security.inbound_entities_count == 2
    assert "CPF" in event.security.inbound_entity_types
    assert "EMAIL" in event.security.inbound_entity_types

    # 2. Mitigação CWE-532: O log JSON NUNCA deve conter o CPF ou o e-mail real
    raw_log = caplog.records[0].message
    assert sensitive_cpf not in raw_log
    assert sensitive_email not in raw_log


def test_audit_logger_log_upstream_error(caplog: pytest.LogCaptureFixture) -> None:
    logger = AuditLogger()

    with caplog.at_level(logging.CRITICAL, logger="guardllm.audit"):
        event = logger.log_upstream_error(
            status_code=504,
            error_message="Gateway Timeout ao chamar modelo",
            client_ip="172.16.0.1",
            correlation_id="trace-timeout-504",
        )

    assert event.event_type == AuditEventType.UPSTREAM_ERROR
    assert event.severity == AuditSeverity.CRITICAL
    assert event.http_status == 504
    assert "Gateway Timeout" in event.message
