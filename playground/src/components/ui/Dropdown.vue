<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  label: string
  options: { id: string; name: string; description?: string }[]
}>()

const emit = defineEmits<{ select: [id: string] }>()

const open = ref(false)

function select(id: string) {
  open.value = false
  emit('select', id)
}

function delayedClose() {
  globalThis.setTimeout(() => { open.value = false }, 150)
}
</script>

<template>
  <div class="relative">
    <button
      class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 transition-colors select-none"
      @click="open = !open"
      @blur="delayedClose()"
    >
      {{ label }}
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
    </button>
    <div
      v-if="open"
      class="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50 overflow-hidden"
    >
      <button
        v-for="opt in options"
        :key="opt.id"
        class="block w-full text-left px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        @mousedown.prevent="select(opt.id)"
      >
        <div class="font-medium text-slate-800 dark:text-slate-200">{{ opt.name }}</div>
        <div v-if="opt.description" class="text-xs text-slate-500 dark:text-slate-400">{{ opt.description }}</div>
      </button>
    </div>
  </div>
</template>
