<script setup lang="ts">
defineProps<{
  title?: string
  variant?: 'default' | 'primary'
}>()

defineEmits<{ click: [] }>()
</script>

<template>
  <button
    :title="title"
    :class="[
      'inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors select-none',
      variant === 'primary'
        ? 'bg-sky-500 hover:bg-sky-600 text-white'
        : 'bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200',
    ]"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>
