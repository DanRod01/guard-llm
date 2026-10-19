<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Shield,
  RefreshCw,
  Trash2,
  Eye,
  Copy,
  Check,
  Search,
  FileText,
} from '@lucide/vue'
import type { AuditEvent } from '~/types/audit'

const props = defineProps<{
  events: AuditEvent[]
  isLoading: boolean
  autoRefresh: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'clear'): void
  (e: 'toggle-auto-refresh'): void
}>()

const selectedEvent = ref<AuditEvent | null>(null)
const copiedId = ref<string | null>(null)
const searchQuery = ref('')
const selectedFilter = ref<'ALL' | 'SUCCESS' | 'BLOCKED' | 'PII' | 'ERROR'>('ALL')

const copyId = (id: string) => {
  navigator.clipboard.writeText(id)
  copiedId.value = id
  setTimeout(() => (copiedId.value = null), 2000)
}

const formatTime = (isoString: string) => {
  try {
    const d = new Date(isoString)
    return d.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'UTC',
    }) + ' UTC'
  } catch {
    return isoString
  }
}

const filteredEvents = computed(() => {
  return props.events.filter((ev) => {
    // Type Filter
    if (selectedFilter.value === 'SUCCESS' && ev.event_type !== 'TRANSACTION_SUCCESS') return false
    if (selectedFilter.value === 'BLOCKED' && ev.event_type !== 'PROMPT_INJECTION_BLOCKED') return false
    if (selectedFilter.value === 'PII' && ev.event_type !== 'PII_REDACTED') return false
    if (selectedFilter.value === 'ERROR' && ev.event_type !== 'UPSTREAM_ERROR') return false

    // Search query
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      const matchCid = ev.correlation_id.toLowerCase().includes(q)
      const matchMsg = ev.message.toLowerCase().includes(q)
      const matchType = ev.event_type.toLowerCase().includes(q)
      return matchCid || matchMsg || matchType
    }
    return true
  })
})
</script>

<template>
  <div class="rounded-xl bg-surface-900 border border-surface-800 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b border-surface-800 bg-surface-900 flex flex-col md:flex-row md:items-center justify-between gap-3">
      <div>
        <div class="flex items-center space-x-2">
          <Shield class="w-4 h-4 text-emerald-400" />
          <h2 class="text-sm font-semibold text-white">
            Trilha de Auditoria SIEM em Tempo Real
          </h2>
        </div>
        <p class="text-xs text-zinc-400 mt-0.5">
          Buffer circular em memória com conformidade estrita CWE-532 (Zero Plaintext PII)
        </p>
      </div>

      <!-- Controls & Search -->
      <div class="flex items-center space-x-2 flex-wrap gap-y-2">
        <!-- Search Input -->
        <div class="relative">
          <Search class="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filtrar por trace ou evento..."
            class="pl-8 pr-3 py-1.5 rounded-md bg-surface-950 border border-surface-800 focus:border-zinc-500 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none font-mono transition w-48 sm:w-56"
          />
        </div>

        <!-- Auto-Refresh Toggle -->
        <button
          @click="emit('toggle-auto-refresh')"
          class="px-2.5 py-1.5 text-xs font-mono rounded-md border transition flex items-center gap-1.5"
          :class="autoRefresh
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-surface-850 border-surface-800 text-zinc-500 hover:text-zinc-300'"
        >
          <span class="w-1.5 h-1.5 rounded-full" :class="autoRefresh ? 'bg-emerald-400' : 'bg-zinc-600'" />
          <span>Auto-sync (5s)</span>
        </button>

        <!-- Refresh Button -->
        <button
          @click="emit('refresh')"
          :disabled="isLoading"
          class="p-1.5 rounded-md bg-surface-950 hover:bg-surface-850 text-zinc-400 hover:text-white border border-surface-800 transition disabled:opacity-50"
          title="Recarregar eventos"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" />
        </button>

        <!-- Clear Button -->
        <button
          @click="emit('clear')"
          :disabled="events.length === 0"
          class="p-1.5 rounded-md bg-surface-950 hover:bg-rose-500/10 text-zinc-500 hover:text-rose-400 border border-surface-800 hover:border-rose-500/20 transition disabled:opacity-30 disabled:cursor-not-allowed"
          title="Limpar buffer de auditoria"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Category Filters Tabs -->
    <div class="px-4 py-2 border-b border-surface-800/80 bg-surface-950/60 flex items-center space-x-1 overflow-x-auto text-xs font-mono">
      <button
        v-for="tab in [
          { key: 'ALL', label: 'Todos' },
          { key: 'SUCCESS', label: '200 OK' },
          { key: 'BLOCKED', label: '403 Bloqueados' },
          { key: 'PII', label: 'PII Sanitizada' },
          { key: 'ERROR', label: 'Falhas Upstream' },
        ]"
        :key="tab.key"
        @click="selectedFilter = tab.key as any"
        class="px-2.5 py-1 rounded text-[11px] font-medium transition"
        :class="selectedFilter === tab.key
          ? 'bg-surface-800 text-zinc-100 font-semibold'
          : 'text-zinc-500 hover:text-zinc-300'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs font-mono">
        <thead class="bg-surface-950 text-zinc-400 uppercase tracking-wider text-[11px] border-b border-surface-800">
          <tr>
            <th class="py-2.5 px-4 font-medium">Horário</th>
            <th class="py-2.5 px-4 font-medium">Correlation ID</th>
            <th class="py-2.5 px-4 font-medium">Evento SIEM</th>
            <th class="py-2.5 px-4 font-medium">Severidade</th>
            <th class="py-2.5 px-4 font-medium">HTTP</th>
            <th class="py-2.5 px-4 font-medium">PIIs Higienizadas</th>
            <th class="py-2.5 px-4 font-medium">Latência</th>
            <th class="py-2.5 px-4 font-medium text-right">Inspecionar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-800/60 text-zinc-300">
          <tr
            v-for="ev in filteredEvents"
            :key="ev.correlation_id"
            class="hover:bg-surface-850/40 transition"
          >
            <!-- Horário -->
            <td class="py-2.5 px-4 text-zinc-500 whitespace-nowrap text-[11px]">
              {{ formatTime(ev.timestamp) }}
            </td>

            <!-- Correlation ID -->
            <td class="py-2.5 px-4 whitespace-nowrap">
              <div class="flex items-center space-x-1.5">
                <span class="text-zinc-200">{{ ev.correlation_id.substring(0, 8) }}...</span>
                <button
                  @click="copyId(ev.correlation_id)"
                  class="p-0.5 rounded text-zinc-500 hover:text-white transition"
                  title="Copiar Correlation ID"
                >
                  <Check v-if="copiedId === ev.correlation_id" class="w-3 h-3 text-emerald-400" />
                  <Copy v-else class="w-3 h-3" />
                </button>
              </div>
            </td>

            <!-- Evento SIEM -->
            <td class="py-2.5 px-4 whitespace-nowrap">
              <span
                class="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium"
                :class="{
                  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': ev.event_type === 'TRANSACTION_SUCCESS',
                  'bg-amber-500/10 text-amber-300 border border-amber-500/20': ev.event_type === 'PII_REDACTED',
                  'bg-rose-500/10 text-rose-400 border border-rose-500/20': ev.event_type === 'PROMPT_INJECTION_BLOCKED',
                  'bg-purple-500/10 text-purple-300 border border-purple-500/20': ev.event_type === 'UPSTREAM_ERROR',
                }"
              >
                {{ ev.event_type }}
              </span>
            </td>

            <!-- Severidade -->
            <td class="py-2.5 px-4 whitespace-nowrap">
              <span
                class="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium"
                :class="{
                  'bg-surface-850 text-zinc-400': ev.severity === 'INFO',
                  'bg-amber-500/10 text-amber-400': ev.severity === 'WARNING',
                  'bg-rose-500/10 text-rose-400 font-bold': ev.severity === 'CRITICAL',
                }"
              >
                {{ ev.severity }}
              </span>
            </td>

            <!-- HTTP Status -->
            <td class="py-2.5 px-4 whitespace-nowrap font-bold">
              <span
                :class="{
                  'text-emerald-400': ev.http_status === 200,
                  'text-rose-400': ev.http_status === 403,
                  'text-amber-400': ev.http_status >= 500,
                }"
              >
                {{ ev.http_status }}
              </span>
            </td>

            <!-- PIIs Higienizadas -->
            <td class="py-2.5 px-4 whitespace-nowrap">
              <div v-if="ev.security.inbound_entity_types.length > 0" class="flex flex-wrap gap-1">
                <span
                  v-for="p in ev.security.inbound_entity_types"
                  :key="p"
                  class="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/10 text-amber-300 border border-amber-500/20"
                >
                  {{ p }}
                </span>
              </div>
              <span v-else class="text-zinc-600">-</span>
            </td>

            <!-- Latência -->
            <td class="py-2.5 px-4 whitespace-nowrap text-zinc-400 text-[11px]">
              {{ ev.latency_ms ? `${ev.latency_ms.toFixed(0)}ms` : '-' }}
            </td>

            <!-- Ação: Inspecionar -->
            <td class="py-2.5 px-4 whitespace-nowrap text-right">
              <button
                @click="selectedEvent = ev"
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-surface-850 hover:bg-surface-800 text-zinc-300 hover:text-white border border-surface-800 text-[11px] transition"
              >
                <Eye class="w-3 h-3 text-zinc-400" />
                <span>Payload</span>
              </button>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="filteredEvents.length === 0">
            <td colspan="8" class="py-10 text-center text-zinc-500 font-sans">
              <FileText class="w-6 h-6 mx-auto text-zinc-600 mb-1.5" />
              <p class="text-xs font-medium text-zinc-400">Nenhum evento registrado no buffer</p>
              <p class="text-[11px] text-zinc-600 mt-0.5">
                Envie requisições no Playground para auditar o pipeline em tempo real
              </p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Forensic Modal -->
    <EventModal :event="selectedEvent" @close="selectedEvent = null" />
  </div>
</template>
