<script setup lang="ts">
import type { TraceEntry } from '@/types/sigil'

defineProps<{
  trace: TraceEntry[]
}>()
</script>

<template>
  <div class="h-full overflow-auto p-3">
    <template v-if="trace.length">
      <div
        v-for="(entry, i) in trace"
        :key="i"
        :class="[
          'mb-2 rounded-md border p-2.5 text-sm font-mono',
          entry.fired
            ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30'
            : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30 opacity-60',
        ]"
      >
        <div class="flex items-center gap-2 mb-1">
          <span
            :class="[
              'inline-block w-2 h-2 rounded-full',
              entry.fired ? 'bg-emerald-500' : 'bg-slate-400',
            ]"
          />
          <span class="font-semibold text-slate-800 dark:text-slate-200">{{ entry.rule }}</span>
          <span class="text-xs text-slate-500 dark:text-slate-400">
            priority {{ entry.priority }}
          </span>
          <span
            :class="[
              'text-xs font-medium px-1.5 py-0.5 rounded',
              entry.fired
                ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400',
            ]"
          >
            {{ entry.fired ? 'FIRED' : 'SKIPPED' }}
          </span>
        </div>
        <div v-if="entry.explain" class="text-xs text-slate-600 dark:text-slate-400 pl-4 italic">
          {{ entry.explain }}
        </div>
      </div>
    </template>
    <div v-else class="text-slate-400 dark:text-slate-500 italic text-sm">
      No rules to trace. Programs with rules will show execution trace here.
    </div>
  </div>
</template>
