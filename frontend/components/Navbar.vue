<script setup lang="ts">
import {
  ShieldCheck,
  BookOpen,
  RefreshCw,
} from '@lucide/vue'

const props = defineProps<{
  isOnline: boolean
  latencyMs: number
  version?: string
  environment?: string
  isRefreshing: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()
</script>

<template>
  <header class="border-b border-surface-800 bg-surface-950/80 backdrop-blur-md sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
      <!-- Branding / Minimal Identity -->
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-surface-900 border border-surface-800 flex items-center justify-center text-emerald-400">
          <ShieldCheck class="w-4 h-4" />
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-sm font-semibold tracking-tight text-white">
            GuardLLM
          </span>
          <span class="text-xs text-zinc-500 font-mono">/</span>
          <span class="text-xs text-zinc-400 font-medium">
            Security Gateway
          </span>
          <span class="px-1.5 py-0.5 text-[10px] font-mono text-zinc-400 rounded bg-surface-850 border border-surface-800">
            v{{ version || '0.1.0' }}
          </span>
        </div>
      </div>

      <!-- System Status & Actions -->
      <div class="flex items-center space-x-3">
        <!-- Live Health Status Indicator -->
        <div
          class="flex items-center space-x-2 px-2.5 py-1 rounded-md border text-xs font-mono transition"
          :class="isOnline
            ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400'
            : 'bg-rose-500/5 border-rose-500/20 text-rose-400'"
        >
          <span class="relative flex h-1.5 w-1.5">
            <span
              v-if="isOnline"
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"
            />
            <span
              class="relative inline-flex rounded-full h-1.5 w-1.5"
              :class="isOnline ? 'bg-emerald-500' : 'bg-rose-500'"
            />
          </span>
          <span class="font-medium tracking-tight">
            {{ isOnline ? 'Operacional' : 'Indisponível' }}
          </span>
          <span v-if="isOnline" class="text-zinc-500 border-l border-zinc-800 pl-2">
            {{ latencyMs }}ms
          </span>
        </div>

        <!-- Sync Button -->
        <button
          @click="emit('refresh')"
          :disabled="isRefreshing"
          class="p-1.5 rounded-md bg-surface-900 hover:bg-surface-850 border border-surface-800 text-zinc-400 hover:text-zinc-200 transition disabled:opacity-50"
          title="Sincronizar telemetria"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isRefreshing }" />
        </button>

        <!-- Documentation & Repo Links -->
        <div class="hidden sm:flex items-center space-x-1 border-l border-surface-800 pl-3">
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            class="flex items-center space-x-1.5 px-2.5 py-1 text-xs text-zinc-400 hover:text-zinc-200 rounded-md hover:bg-surface-850 transition"
          >
            <BookOpen class="w-3.5 h-3.5 text-zinc-500" />
            <span>API Docs</span>
          </a>

          <a
            href="https://github.com/DanRod01/guard-llm"
            target="_blank"
            rel="noopener noreferrer"
            class="flex items-center space-x-1.5 px-2.5 py-1 text-xs text-zinc-400 hover:text-zinc-200 rounded-md hover:bg-surface-850 transition"
          >
            <svg class="w-3.5 h-3.5 text-zinc-500 fill-current" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            <span>Repositório</span>
          </a>
        </div>
      </div>
    </div>
  </header>
</template>
