<script setup lang="ts">
import {
  Activity,
  ShieldAlert,
  Lock,
  Cpu,
} from '@lucide/vue'
import type { AuditStats } from '~/types/audit'

const props = defineProps<{
  stats: AuditStats | null
  isLoading: boolean
}>()
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
    <!-- Card 1: Volume de Transações -->
    <div class="p-4 rounded-xl bg-surface-900 border border-surface-800 hover:border-surface-750 transition flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-mono uppercase tracking-wider">
          Volume Transacional
        </span>
        <Activity class="w-3.5 h-3.5 text-zinc-500" />
      </div>

      <div class="mt-3 flex items-baseline justify-between">
        <span class="text-2xl font-bold font-mono text-zinc-100">
          {{ stats?.total_events ?? 0 }}
        </span>
        <span class="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
          {{ stats?.transactions_success ?? 0 }} 200 OK
        </span>
      </div>

      <div class="mt-2 pt-2 border-t border-surface-800/80 text-[11px] text-zinc-500">
        Total auditado no buffer circular
      </div>
    </div>

    <!-- Card 2: Ataques Bloqueados (OWASP LLM01) -->
    <div class="p-4 rounded-xl bg-surface-900 border border-surface-800 hover:border-surface-750 transition flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-mono uppercase tracking-wider">
          Ataques Bloqueados
        </span>
        <ShieldAlert class="w-3.5 h-3.5 text-rose-400" />
      </div>

      <div class="mt-3 flex items-baseline justify-between">
        <span class="text-2xl font-bold font-mono text-rose-400">
          {{ stats?.injections_blocked ?? 0 }}
        </span>
        <span class="text-[11px] font-mono text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
          403 Forbidden
        </span>
      </div>

      <div class="mt-2 pt-2 border-t border-surface-800/80 text-[11px] text-zinc-500">
        Mitigação OWASP LLM01 na borda
      </div>
    </div>

    <!-- Card 3: PIIs Redigidas (LGPD/GDPR) -->
    <div class="p-4 rounded-xl bg-surface-900 border border-surface-800 hover:border-surface-750 transition flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-mono uppercase tracking-wider">
          Privacidade & PII
        </span>
        <Lock class="w-3.5 h-3.5 text-amber-400" />
      </div>

      <div class="mt-3 flex items-baseline justify-between">
        <span class="text-2xl font-bold font-mono text-amber-300">
          {{ stats?.pii_redacted ?? 0 }}
        </span>
        <span class="text-[11px] font-mono text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
          LGPD / GDPR
        </span>
      </div>

      <div class="mt-2 pt-2 border-t border-surface-800/80 text-[11px] text-zinc-500">
        CPFs, Cartões e Segredos mascarados
      </div>
    </div>

    <!-- Card 4: FinOps & Latência -->
    <div class="p-4 rounded-xl bg-surface-900 border border-surface-800 hover:border-surface-750 transition flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-mono uppercase tracking-wider">
          FinOps & Latência
        </span>
        <Cpu class="w-3.5 h-3.5 text-zinc-500" />
      </div>

      <div class="mt-3 flex items-baseline justify-between">
        <span class="text-2xl font-bold font-mono text-zinc-100">
          {{ stats?.total_tokens ?? 0 }}
          <span class="text-xs font-sans text-zinc-500 font-normal">tok</span>
        </span>
        <span class="text-[11px] font-mono text-zinc-300 bg-surface-850 px-1.5 py-0.5 rounded border border-surface-800">
          {{ stats?.average_latency_ms ? `${stats.average_latency_ms}ms` : '0ms' }}
        </span>
      </div>

      <div class="mt-2 pt-2 border-t border-surface-800/80 text-[11px] text-zinc-500">
        Contabilidade de tokens e média de resposta
      </div>
    </div>
  </div>
</template>
