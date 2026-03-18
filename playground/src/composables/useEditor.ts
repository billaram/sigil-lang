import { onMounted, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import * as monaco from 'monaco-editor'
import { registerSigilLanguage } from '@/components/editor/sigil-language'

export function useEditor(
  container: Ref<HTMLElement | null>,
  options: {
    language: string
    value: Ref<string>
    readOnly?: boolean
    onRun?: () => void
  },
  darkMode: Ref<boolean>,
) {
  const editor = ref<monaco.editor.IStandaloneCodeEditor | null>(null)

  registerSigilLanguage()

  onMounted(() => {
    if (!container.value) return

    const ed = monaco.editor.create(container.value, {
      value: options.value.value,
      language: options.language,
      theme: darkMode.value ? 'sigil-dark' : 'sigil-light',
      minimap: { enabled: false },
      fontSize: 14,
      tabSize: 2,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      automaticLayout: true,
      padding: { top: 8, bottom: 8 },
      renderLineHighlight: 'line',
      overviewRulerLanes: 0,
      hideCursorInOverviewRuler: true,
      scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
    })

    ed.onDidChangeModelContent(() => {
      const val = ed.getValue()
      if (val !== options.value.value) {
        options.value.value = val
      }
    })

    if (options.onRun) {
      const run = options.onRun
      ed.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run)
    }

    editor.value = ed
  })

  watch(options.value, (newVal) => {
    if (editor.value && editor.value.getValue() !== newVal) {
      editor.value.setValue(newVal)
    }
  })

  watch(darkMode, (dark) => {
    monaco.editor.setTheme(dark ? 'sigil-dark' : 'sigil-light')
  })

  onBeforeUnmount(() => {
    editor.value?.dispose()
  })

  function setMarkers(markers: monaco.editor.IMarkerData[]) {
    const model = editor.value?.getModel()
    if (model) {
      monaco.editor.setModelMarkers(model, 'sigil', markers)
    }
  }

  function clearMarkers() {
    setMarkers([])
  }

  return { editor, setMarkers, clearMarkers }
}
