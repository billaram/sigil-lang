<script setup lang="ts">
defineProps<{
  lines: string[]
}>()
</script>

<template>
  <div class="h-full overflow-auto p-3 font-mono text-sm">
    <template v-if="lines.length">
      <div
        v-for="(line, i) in lines"
        :key="i"
        class="text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed"
      >{{ line }}</div>
    </template>
    <div v-else class="text-slate-400 dark:text-slate-500 italic">
      No output. Click Run or press Ctrl+Enter.
    </div>
  </div>
</template>
