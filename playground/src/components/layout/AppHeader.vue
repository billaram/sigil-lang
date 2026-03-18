<script setup lang="ts">
import IconButton from '@/components/ui/IconButton.vue'
import Dropdown from '@/components/ui/Dropdown.vue'

defineProps<{
  examples: { id: string; name: string; description?: string }[]
  loading: boolean
}>()

defineEmits<{
  run: []
  share: []
  toggleDark: []
  loadExample: [id: string]
}>()
</script>

<template>
  <header class="flex items-center gap-3 px-4 py-2 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 select-none shrink-0">
    <!-- Logo -->
    <div class="flex items-center gap-2 mr-2">
      <div class="w-7 h-7 rounded bg-sky-500 flex items-center justify-center">
        <span class="text-white font-bold text-sm">S</span>
      </div>
      <span class="font-semibold text-slate-800 dark:text-slate-100 hidden sm:inline">Sigil Playground</span>
    </div>

    <!-- Examples -->
    <Dropdown
      label="Examples"
      :options="examples"
      @select="$emit('loadExample', $event)"
    />

    <div class="flex-1" />

    <!-- Actions -->
    <IconButton variant="primary" title="Run (Ctrl+Enter)" :disabled="loading" @click="$emit('run')">
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.8A1.5 1.5 0 004 4.1v11.8a1.5 1.5 0 002.3 1.3l9.2-5.9a1.5 1.5 0 000-2.6L6.3 2.8z" /></svg>
      <span class="hidden sm:inline">Run</span>
    </IconButton>

    <IconButton title="Share" @click="$emit('share')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
    </IconButton>

    <IconButton title="Toggle dark mode" @click="$emit('toggleDark')">
      <svg class="w-4 h-4 dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
      <svg class="w-4 h-4 hidden dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
    </IconButton>
  </header>
</template>
