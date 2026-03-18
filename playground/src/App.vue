<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import PanelSplitter from '@/components/layout/PanelSplitter.vue'
import SigilEditor from '@/components/editor/SigilEditor.vue'
import InputEditor from '@/components/editor/InputEditor.vue'
import OutputPanel from '@/components/output/OutputPanel.vue'
import { useSigilRuntime } from '@/composables/useSigilRuntime'
import { useExamples } from '@/composables/useExamples'
import { useShare } from '@/composables/useShare'
import { useDarkMode } from '@/composables/useDarkMode'
import type { SigilResult, SigilError } from '@/types/sigil'

const { loading, ready, initError, initialize, run: runSigil } = useSigilRuntime()
const { examples, loadExample } = useExamples()
const { decode, share } = useShare()
const { dark, toggle: toggleDark } = useDarkMode()

const source = ref(examples[0].source)
const inputJson = ref(examples[0].input)
const result = ref<SigilResult | null>(null)
const error = ref<SigilError | null>(null)
const elapsed = ref<number | null>(null)

const editorRef = ref<InstanceType<typeof SigilEditor> | null>(null)

onMounted(async () => {
  // Restore from URL hash if present
  const shared = decode()
  if (shared.source) {
    source.value = shared.source
    inputJson.value = shared.input ?? '{}'
  }

  await initialize()
})

function handleRun() {
  if (!ready.value) return
  editorRef.value?.clearMarkers()

  const start = performance.now()
  const { result: res, error: err } = runSigil(source.value, inputJson.value)
  elapsed.value = performance.now() - start

  if (err) {
    error.value = err
    result.value = null
    // Set Monaco error markers
    if (err.line) {
      editorRef.value?.setMarkers([{
        severity: 8, // MarkerSeverity.Error
        message: err.error,
        startLineNumber: err.line,
        startColumn: err.column ?? 1,
        endLineNumber: err.line,
        endColumn: err.column ? err.column + 1 : 1000,
      }])
    }
  } else {
    result.value = res ?? null
    error.value = null
  }
}

function handleLoadExample(id: string) {
  const ex = loadExample(id)
  if (ex) {
    source.value = ex.source
    inputJson.value = ex.input
    result.value = null
    error.value = null
    elapsed.value = null
    editorRef.value?.clearMarkers()
  }
}

function handleShare() {
  share(source.value, inputJson.value)
}

const exampleList = examples.map((e) => ({
  id: e.id,
  name: e.name,
  description: e.description,
}))
</script>

<template>
  <div class="h-full flex flex-col">
    <AppHeader
      :examples="exampleList"
      :loading="loading"
      @run="handleRun"
      @share="handleShare"
      @toggle-dark="toggleDark"
      @load-example="handleLoadExample"
    />

    <!-- Loading state -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full mx-auto mb-3"></div>
        <p class="text-sm text-slate-500 dark:text-slate-400">Loading Sigil runtime...</p>
      </div>
    </div>

    <!-- Init error -->
    <div v-else-if="initError" class="flex-1 flex items-center justify-center p-8">
      <div class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md">
        <h2 class="font-semibold text-red-700 dark:text-red-300 mb-2">Failed to load WASM runtime</h2>
        <p class="text-sm text-red-600 dark:text-red-400">{{ initError }}</p>
      </div>
    </div>

    <!-- Main editor layout -->
    <PanelSplitter v-else direction="horizontal" :initial-ratio="0.55" class="flex-1 min-h-0">
      <template #first>
        <PanelSplitter direction="vertical" :initial-ratio="0.7" :min-ratio="0.3" :max-ratio="0.9">
          <template #first>
            <SigilEditor
              ref="editorRef"
              v-model:source="source"
              :dark-mode="dark"
              @run="handleRun"
            />
          </template>
          <template #second>
            <InputEditor v-model:input="inputJson" :dark-mode="dark" />
          </template>
        </PanelSplitter>
      </template>
      <template #second>
        <OutputPanel :result="result" :error="error" :elapsed="elapsed" />
      </template>
    </PanelSplitter>
  </div>
</template>
