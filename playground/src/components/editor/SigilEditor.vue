<script setup lang="ts">
import { ref, toRef } from 'vue'
import { useEditor } from '@/composables/useEditor'

const props = defineProps<{
  darkMode: boolean
  initialValue: string
}>()

const emit = defineEmits<{ run: [] }>()
const container = ref<HTMLElement | null>(null)

const { getValue, setValue, setMarkers, clearMarkers } = useEditor(
  container,
  {
    language: 'sigil',
    initialValue: props.initialValue,
    onRun: () => emit('run'),
  },
  toRef(props, 'darkMode'),
)

defineExpose({ getValue, setValue, setMarkers, clearMarkers })
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="px-3 py-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700 select-none">
      Source
    </div>
    <div ref="container" class="flex-1 min-h-0"></div>
  </div>
</template>
