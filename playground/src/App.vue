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

const result = ref<SigilResult | null>(null)
const error = ref<SigilError | null>(null)
const elapsed = ref<number | null>(null)

const editorRef = ref<InstanceType<typeof SigilEditor> | null>(null)
const inputRef = ref<InstanceType<typeof InputEditor> | null>(null)

// Initial values — may be overridden by URL hash
let initialSource = examples[0].source
let initialInput = examples[0].input
const shared = decode()
if (shared.source) {
  initialSource = shared.source
  initialInput = shared.input ?? '{}'
}

onMounted(async () => {
  console.log('[sigil] App mounted, initializing...')
  await initialize()
})

function handleRun() {
  if (!ready.value) return
  editorRef.value?.clearMarkers()

  const source = editorRef.value?.getValue() ?? ''
  const input = inputRef.value?.getValue() ?? '{}'

  console.log('[sigil] Run clicked, source length:', source.length)

  const start = performance.now()
  const { result: res, error: err } = runSigil(source, input)
  elapsed.value = performance.now() - start

  if (err) {
    error.value = err
    result.value = null
    if (err.line) {
      editorRef.value?.setMarkers([{
        message: err.error,
        line: err.line,
        column: err.column ?? undefined,
      }])
    }
  } else {
    result.value = res ?? null
    error.value = null
  }
}

function handleLoadExample(id: string) {
  console.log('[sigil] Loading example:', id)
  const ex = loadExample(id)
  if (ex) {
    editorRef.value?.setValue(ex.source)
    inputRef.value?.setValue(ex.input)
    result.value = null
    error.value = null
    elapsed.value = null
    editorRef.value?.clearMarkers()
    console.log('[sigil] Example loaded:', id)
  }
}

function handleShare() {
  const source = editorRef.value?.getValue() ?? ''
  const input = inputRef.value?.getValue() ?? '{}'
  const url = share(source, input)
  console.log('[sigil] Shared URL:', url)
}

const exampleList = examples.map((e) => ({
  id: e.id,
  name: e.name,
  description: e.description,
}))
</script>

<template>
  <div class="h-full flex flex-col relative">
    <AppHeader
      :examples="exampleList"
      :loading="loading"
      @run="handleRun"
      @share="handleShare"
      @toggle-dark="toggleDark"
      @load-example="handleLoadExample"
    />

    <!-- Main editor layout — always rendered -->
    <PanelSplitter direction="horizontal" :initial-ratio="0.55" class="flex-1 min-h-0">
      <template #first>
        <PanelSplitter direction="vertical" :initial-ratio="0.7" :min-ratio="0.3" :max-ratio="0.9">
          <template #first>
            <SigilEditor
              ref="editorRef"
              :initial-value="initialSource"
              :dark-mode="dark"
              @run="handleRun"
            />
          </template>
          <template #second>
            <InputEditor
              ref="inputRef"
              :initial-value="initialInput"
              :dark-mode="dark"
            />
          </template>
        </PanelSplitter>
      </template>
      <template #second>
        <OutputPanel :result="result" :error="error" :elapsed="elapsed" />
      </template>
    </PanelSplitter>

    <!-- Loading overlay -->
    <div v-if="loading" class="absolute inset-0 top-11 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 z-50">
      <div class="text-center">
        <div class="animate-spin w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full mx-auto mb-3"></div>
        <p class="text-sm text-slate-500 dark:text-slate-400">Loading Sigil runtime...</p>
      </div>
    </div>

    <!-- Init error overlay -->
    <div v-if="initError" class="absolute inset-0 top-11 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 z-50 p-8">
      <div class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md">
        <h2 class="font-semibold text-red-700 dark:text-red-300 mb-2">Failed to load WASM runtime</h2>
        <p class="text-sm text-red-600 dark:text-red-400">{{ initError }}</p>
      </div>
    </div>
  </div>
</template>
