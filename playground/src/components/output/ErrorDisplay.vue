<script setup lang="ts">
import type { SigilError } from '@/types/sigil'

defineProps<{
  error: SigilError
}>()
</script>

<template>
  <div class="h-full overflow-auto p-3">
    <div class="rounded-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-3">
      <div class="flex items-start gap-2">
        <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
        </svg>
        <div class="flex-1 min-w-0">
          <div v-if="error.line" class="text-xs text-red-600 dark:text-red-400 mb-1">
            Line {{ error.line }}<span v-if="error.column">, Column {{ error.column }}</span>
          </div>
          <pre class="text-sm text-red-700 dark:text-red-300 font-mono whitespace-pre-wrap break-words">{{ error.error }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
