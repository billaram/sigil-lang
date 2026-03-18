<script setup lang="ts">
defineProps<{
  tabs: string[]
  active: string
}>()

defineEmits<{ select: [tab: string] }>()
</script>

<template>
  <div class="flex gap-0 border-b border-slate-200 dark:border-slate-700">
    <button
      v-for="tab in tabs"
      :key="tab"
      :class="[
        'px-3 py-1.5 text-xs font-medium transition-colors select-none border-b-2 -mb-px',
        tab === active
          ? 'text-sky-600 dark:text-sky-400 border-sky-500'
          : 'text-slate-500 dark:text-slate-400 border-transparent hover:text-slate-700 dark:hover:text-slate-300',
      ]"
      @click="$emit('select', tab)"
    >
      {{ tab }}
    </button>
  </div>
</template>
