<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useGuardApi } from '~/composables/useGuardApi'
import type { AuditEvent, AuditStats } from '~/types/audit'
import type { HealthResponse } from '~/composables/useGuardApi'

const api = useGuardApi()

const isOnline = ref(false)
const latencyMs = ref(0)
const healthData = ref<HealthResponse | null>(null)
const isRefreshing = ref(false)

const stats = ref<AuditStats | null>(null)
const events = ref<AuditEvent[]>([])
const autoRefresh = ref(true)
let refreshInterval: any = null

const loadData = async (silent = false) => {
  if (!silent) isRefreshing.value = true
  try {
    const health = await api.checkHealth()
    isOnline.value = health.ok
    latencyMs.value = health.latencyMs
    if (health.data) healthData.value = health.data

    const [statsRes, eventsRes] = await Promise.all([
      api.getStats(),
      api.getEvents(50),
    ])

    if (statsRes) stats.value = statsRes
    if (eventsRes) events.value = eventsRes.events
  } finally {
    if (!silent) isRefreshing.value = false
  }
}

const handleClear = async () => {
  const ok = await api.clearEvents()
  if (ok) {
    events.value = []
    await loadData(true)
  }
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
}

onMounted(() => {
  loadData()
  refreshInterval = setInterval(() => {
    if (autoRefresh.value) {
      loadData(true)
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<template>
  <div class="min-h-screen bg-surface-950 text-zinc-100 flex flex-col font-sans selection:bg-emerald-500/20 selection:text-emerald-300">
    <!-- Navbar -->
    <Navbar
      :is-online="isOnline"
      :latency-ms="latencyMs"
      :version="healthData?.version"
      :environment="healthData?.environment"
      :is-refreshing="isRefreshing"
      @refresh="loadData(false)"
    />

    <!-- Main Content Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <!-- SecOps & FinOps KPI Cards -->
      <MetricsCards
        :stats="stats"
        :is-loading="isRefreshing"
      />

      <!-- Security Playground & Dual-Gate Inspector -->
      <SecurityPlayground
        @executed="loadData(true)"
      />

      <!-- Live SIEM Audit Feed -->
      <AuditFeed
        :events="events"
        :is-loading="isRefreshing"
        :auto-refresh="autoRefresh"
        @refresh="loadData(false)"
        @clear="handleClear"
        @toggle-auto-refresh="toggleAutoRefresh"
      />
    </main>

    <!-- Footer -->
    <footer class="border-t border-surface-800 bg-surface-950 py-5 text-center text-xs text-zinc-500 font-mono">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>
          <strong class="text-zinc-300 font-semibold">GuardLLM</strong> — Defensive Security Reverse Proxy for Production LLMs.
        </p>
        <p class="text-zinc-500">
          Clean Architecture • Pydantic V2 Rust Core • Nuxt 3 & Tailwind CSS
        </p>
      </div>
    </footer>
  </div>
</template>
