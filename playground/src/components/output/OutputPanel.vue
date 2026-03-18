<script setup lang="ts">
import { ref } from 'vue'
import TabBar from '@/components/ui/TabBar.vue'
import OutputTab from './OutputTab.vue'
import BindingsTab from './BindingsTab.vue'
import TraceTab from './TraceTab.vue'
import ErrorDisplay from './ErrorDisplay.vue'
import type { SigilResult, SigilError } from '@/types/sigil'

defineProps<{
  result: SigilResult | null
  error: SigilError | null
  elapsed: number | null
}>()

const tabs = ['Output', 'Trace', 'Bindings']
const activeTab = ref('Output')
</script>

<template>
  <div class="h-full flex flex-col bg-white dark:bg-slate-900">
    <div class="flex items-center shrink-0">
      <TabBar :tabs="tabs" :active="activeTab" @select="activeTab = $event" />
      <div class="flex-1" />
      <span v-if="elapsed !== null" class="text-[10px] text-slate-400 dark:text-slate-500 pr-3">
        {{ elapsed.toFixed(1) }}ms
      </span>
    </div>

    <div class="flex-1 min-h-0">
      <ErrorDisplay v-if="error" :error="error" />
      <template v-else-if="result">
        <OutputTab v-if="activeTab === 'Output'" :lines="result.output_lines" />
        <TraceTab v-if="activeTab === 'Trace'" :trace="result.trace" />
        <BindingsTab v-if="activeTab === 'Bindings'" :bindings="result.bindings" />
      </template>
      <div v-else class="p-3 text-sm text-slate-400 dark:text-slate-500 italic">
        Click Run or press Ctrl+Enter to execute.
      </div>
    </div>
  </div>
</template>
