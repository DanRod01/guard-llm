export interface RedactedEntity {
  entity_type: string
  masked_value: string
  start_index: number
  end_index: number
}

export interface SecurityGateAudit {
  sanitized: boolean
  entities_redacted: RedactedEntity[]
  original_length: number
  sanitized_length: number
  sanitized_preview?: string | null
}

export interface InjectionVerdict {
  is_injection: boolean
  risk_score: number
  categories: string[]
  matched_patterns: string[]
}

export interface ProxyAuditMetadata {
  inbound_audit: SecurityGateAudit
  outbound_audit?: SecurityGateAudit | null
  injection_audit: InjectionVerdict
  model_used: string
  latency_ms: number
  prompt_tokens?: number | null
  candidate_tokens?: number | null
  total_tokens?: number | null
}

export interface ProxyChatResponse {
  output_text: string
  security: ProxyAuditMetadata
}

export interface PromptInjectionBlockedResponse {
  detail: string
  security: InjectionVerdict
}

export interface ProxyChatRequest {
  prompt?: string | null
  model?: string | null
  temperature?: number | null
  sanitize_outbound?: boolean
  block_on_injection?: boolean
  simulate_upstream?: boolean
}
