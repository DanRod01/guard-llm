export type AuditEventType =
  | 'TRANSACTION_SUCCESS'
  | 'PROMPT_INJECTION_BLOCKED'
  | 'PII_REDACTED'
  | 'UPSTREAM_ERROR'

export type AuditSeverity = 'INFO' | 'WARNING' | 'CRITICAL'

export interface TokenUsage {
  prompt_tokens?: number | null
  candidate_tokens?: number | null
  total_tokens?: number | null
}

export interface SecurityAuditDetails {
  inbound_entities_count: number
  inbound_entity_types: string[]
  outbound_entities_count: number
  outbound_entity_types: string[]
  injection_detected: boolean
  injection_risk_score?: number | null
  injection_categories: string[]
}

export interface AuditEvent {
  timestamp: string
  correlation_id: string
  event_type: AuditEventType
  severity: AuditSeverity
  http_status: number
  client_ip?: string | null
  model?: string | null
  latency_ms?: number | null
  security: SecurityAuditDetails
  token_usage?: TokenUsage | null
  message: string
}

export interface AuditStats {
  total_events: number
  transactions_success: number
  injections_blocked: number
  pii_redacted: number
  upstream_errors: number
  total_tokens: number
  average_latency_ms: number
}

export interface AuditEventsListResponse {
  total: number
  events: AuditEvent[]
}
