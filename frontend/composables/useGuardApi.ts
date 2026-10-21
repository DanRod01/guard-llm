import type { AuditEventsListResponse, AuditStats } from '~/types/audit'
import type {
  PromptInjectionBlockedResponse,
  ProxyChatRequest,
  ProxyChatResponse,
} from '~/types/proxy'

export interface HealthResponse {
  status: string
  version: string
  environment: string
  timestamp: string
}

export interface ChatExecutionResult {
  success: boolean
  blocked?: boolean
  data?: ProxyChatResponse
  blockedData?: PromptInjectionBlockedResponse
  error?: string
  correlationId?: string
  statusCode: number
}

interface OfetchErrorShape {
  message?: string
  response?: {
    status?: number
    headers?: Headers
    _data?: {
      detail?: string
      security?: PromptInjectionBlockedResponse['security']
    }
  }
}

export const useGuardApi = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBaseUrl

  const checkHealth = async (): Promise<{ ok: boolean; data?: HealthResponse; latencyMs: number }> => {
    const start = performance.now()
    try {
      const data = await $fetch<HealthResponse>(`${baseUrl}/health`, {
        timeout: 5000,
      })
      const latencyMs = Math.round(performance.now() - start)
      return { ok: true, data, latencyMs }
    } catch {
      const latencyMs = Math.round(performance.now() - start)
      return { ok: false, latencyMs }
    }
  }

  const getStats = async (): Promise<AuditStats | null> => {
    try {
      return await $fetch<AuditStats>(`${baseUrl}/audit/stats`)
    } catch (err) {
      console.error('Falha ao buscar estatísticas de auditoria:', err)
      return null
    }
  }

  const getEvents = async (limit = 50): Promise<AuditEventsListResponse | null> => {
    try {
      return await $fetch<AuditEventsListResponse>(`${baseUrl}/audit/events?limit=${limit}`)
    } catch (err) {
      console.error('Falha ao buscar eventos de auditoria:', err)
      return null
    }
  }

  const clearEvents = async (): Promise<boolean> => {
    try {
      await $fetch(`${baseUrl}/audit/events`, { method: 'DELETE' })
      return true
    } catch (err) {
      console.error('Falha ao limpar eventos:', err)
      return false
    }
  }

  const executeChat = async (request: ProxyChatRequest): Promise<ChatExecutionResult> => {
    try {
      let correlationId = ''
      const res = await $fetch.raw<ProxyChatResponse>(`${baseUrl}/proxy/chat`, {
        method: 'POST',
        body: request,
      })

      correlationId = res.headers.get('x-correlation-id') || ''
      return {
        success: true,
        data: res._data ?? undefined,
        correlationId,
        statusCode: res.status,
      }
    } catch (err: unknown) {
      const fetchErr = err as OfetchErrorShape
      const status = fetchErr.response?.status || 500
      const correlationId = fetchErr.response?.headers?.get('x-correlation-id') || ''
      const errorData = fetchErr.response?._data

      if (status === 403 && errorData?.security) {
        return {
          success: false,
          blocked: true,
          blockedData: {
            detail: errorData.detail || 'Prompt Injection bloqueado preventivamente pelo GuardLLM.',
            security: errorData.security,
          },
          correlationId,
          statusCode: 403,
        }
      }

      return {
        success: false,
        blocked: false,
        error: errorData?.detail || fetchErr.message || 'Erro desconhecido',
        correlationId,
        statusCode: status,
      }
    }
  }

  return {
    checkHealth,
    getStats,
    getEvents,
    clearEvents,
    executeChat,
  }
}
