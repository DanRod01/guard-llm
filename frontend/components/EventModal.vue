<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { X, Copy, Check, ShieldCheck, Terminal } from '@lucide/vue'
import type { AuditEvent } from '~/types/audit'

const props = defineProps<{
  event: AuditEvent | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const copied = ref(false)

const copyJson = () => {
  if (!props.event) return
  navigator.clipboard.writeText(JSON.stringify(props.event, null, 2))
  copied.value = true
  setTimeout(() => (copied.value = false), 2000)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.event) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div
    v-if="event"
    role="dialog"
    aria-modal="true"
    aria-label="Inspeção Forense SIEM"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div class="w-full max-w-2xl rounded-xl bg-surface-900 border border-surface-800 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
      <!-- Modal Header -->
      <div class="p-4 border-b border-surface-800 bg-surface-950 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <Terminal class="w-4 h-4 text-emerald-400" />
          <h3 class="text-xs font-semibold text-zinc-100 font-mono uppercase tracking-wider">
            Inspeção Forense SIEM (CWE-532)
          </h3>
          <span
            class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold"
            :class="{
              'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': event.severity === 'INFO',
              'bg-amber-500/10 text-amber-400 border border-amber-500/20': event.severity === 'WARNING',
              'bg-rose-500/10 text-rose-400 border border-rose-500/20': event.severity === 'CRITICAL',
            }"
          >
            {{ event.severity }}
          </span>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="copyJson"
            class="px-2.5 py-1 text-xs font-mono rounded bg-surface-850 hover:bg-surface-800 text-zinc-300 hover:text-white border border-surface-800 transition flex items-center gap-1.5"
          >
            <Check v-if="copied" class="w-3 h-3 text-emerald-400" />
            <Copy v-else class="w-3 h-3" />
            <span>{{ copied ? 'Copiado' : 'Copiar' }}</span>
          </button>
          <button
            @click="emit('close')"
            class="p-1 rounded text-zinc-400 hover:text-white hover:bg-surface-800 transition"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Security Notice -->
      <div class="px-4 py-2.5 bg-emerald-950/20 border-b border-emerald-900/30 flex items-center gap-2 text-xs text-emerald-300">
        <ShieldCheck class="w-4 h-4 text-emerald-400 shrink-0" />
        <span class="text-[11px] leading-relaxed">
          <strong>Conformidade CWE-532:</strong> Nenhum dado confidencial, segredo de nuvem ou prompt bruto em texto claro foi gravado neste log.
        </span>
      </div>

      <!-- JSON Viewer -->
      <div class="p-4 overflow-y-auto flex-1 bg-surface-950 font-mono text-[11px]">
        <pre class="text-zinc-300 leading-relaxed">{{ JSON.stringify(event, null, 2) }}</pre>
      </div>

      <!-- Modal Footer -->
      <div class="p-3 border-t border-surface-800 bg-surface-950 flex items-center justify-between text-xs text-zinc-500 font-mono">
        <span>Correlation ID: <code class="text-zinc-300">{{ event.correlation_id }}</code></span>
        <button
          @click="emit('close')"
          class="px-3 py-1 rounded bg-surface-850 hover:bg-surface-800 text-zinc-300 text-xs font-sans transition"
        >
          Fechar
        </button>
      </div>
    </div>
  </div>
</template>
