<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    direction?: 'horizontal' | 'vertical'
    initialRatio?: number
    minRatio?: number
    maxRatio?: number
  }>(),
  {
    direction: 'horizontal',
    initialRatio: 0.5,
    minRatio: 0.2,
    maxRatio: 0.8,
  },
)

const ratio = ref(props.initialRatio)
const dragging = ref(false)
const container = ref<HTMLElement | null>(null)

const isHorizontal = computed(() => props.direction === 'horizontal')

const firstStyle = computed(() =>
  isHorizontal.value
    ? { width: `${ratio.value * 100}%` }
    : { height: `${ratio.value * 100}%` },
)

const secondStyle = computed(() =>
  isHorizontal.value
    ? { width: `${(1 - ratio.value) * 100}%` }
    : { height: `${(1 - ratio.value) * 100}%` },
)

function onMouseDown(e: MouseEvent) {
  e.preventDefault()
  dragging.value = true
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

function onMouseMove(e: MouseEvent) {
  if (!dragging.value || !container.value) return
  const rect = container.value.getBoundingClientRect()
  let newRatio: number
  if (isHorizontal.value) {
    newRatio = (e.clientX - rect.left) / rect.width
  } else {
    newRatio = (e.clientY - rect.top) / rect.height
  }
  ratio.value = Math.min(props.maxRatio, Math.max(props.minRatio, newRatio))
}

function onMouseUp() {
  dragging.value = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
}
</script>

<template>
  <div
    ref="container"
    :class="['flex h-full w-full overflow-hidden', isHorizontal ? 'flex-row' : 'flex-col']"
  >
    <div :style="firstStyle" class="overflow-hidden min-w-0 min-h-0">
      <slot name="first" />
    </div>
    <div
      :class="[
        'shrink-0 bg-slate-200 dark:bg-slate-700 hover:bg-sky-400 dark:hover:bg-sky-500 transition-colors z-10',
        isHorizontal ? 'w-1 cursor-col-resize' : 'h-1 cursor-row-resize',
        dragging ? 'bg-sky-400 dark:bg-sky-500' : '',
      ]"
      @mousedown="onMouseDown"
    />
    <div :style="secondStyle" class="overflow-hidden min-w-0 min-h-0">
      <slot name="second" />
    </div>
  </div>
</template>
