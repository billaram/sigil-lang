import { onMounted, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { EditorView, keymap } from '@codemirror/view'
import { EditorState, Compartment } from '@codemirror/state'
import { basicSetup } from 'codemirror'
import { json } from '@codemirror/lang-json'
import { setDiagnostics, type Diagnostic } from '@codemirror/lint'
import { sigilLanguage, sigilLightTheme, sigilDarkTheme } from '@/components/editor/sigil-language'

export interface MarkerData {
  message: string
  line: number
  column?: number
  severity?: 'error' | 'warning' | 'info'
}

export function useEditor(
  container: Ref<HTMLElement | null>,
  options: {
    language: string
    initialValue: string
    onRun?: () => void
  },
  darkMode: Ref<boolean>,
) {
  const view = ref<EditorView | null>(null)
  const themeCompartment = new Compartment()

  onMounted(() => {
    if (!container.value) {
      console.warn('[sigil] Editor container not found on mount')
      return
    }

    const langExtension = options.language === 'sigil' ? sigilLanguage : json()
    const theme = darkMode.value ? sigilDarkTheme : sigilLightTheme

    const keymaps = options.onRun
      ? keymap.of([{ key: 'Mod-Enter', run: () => { options.onRun!(); return true } }])
      : keymap.of([])

    const state = EditorState.create({
      doc: options.initialValue,
      extensions: [
        basicSetup,
        langExtension,
        themeCompartment.of(theme),
        keymaps,
        EditorView.theme({
          '.cm-content': {
            fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
            fontSize: '14px',
            padding: '8px 0',
          },
          '.cm-scroller': {
            overflow: 'auto',
          },
          '&': {
            height: '100%',
          },
        }),
        EditorState.tabSize.of(2),
      ],
    })

    view.value = new EditorView({
      state,
      parent: container.value,
    })

    console.log('[sigil] CodeMirror editor ready:', options.language)
  })

  watch(darkMode, (dark) => {
    if (!view.value) return
    const theme = dark ? sigilDarkTheme : sigilLightTheme
    view.value.dispatch({
      effects: themeCompartment.reconfigure(theme),
    })
  })

  onBeforeUnmount(() => {
    view.value?.destroy()
    view.value = null
  })

  function getValue(): string {
    return view.value?.state.doc.toString() ?? options.initialValue
  }

  function setValue(content: string) {
    if (!view.value) return
    const current = view.value.state.doc.toString()
    if (current !== content) {
      view.value.dispatch({
        changes: { from: 0, to: current.length, insert: content },
      })
    }
  }

  function setMarkers(markers: MarkerData[]) {
    if (!view.value) return
    const doc = view.value.state.doc
    const diagnostics: Diagnostic[] = markers.map((m) => {
      const line = Math.min(m.line, doc.lines)
      const lineObj = doc.line(line)
      const col = m.column ? Math.min(m.column - 1, lineObj.length) : 0
      const from = lineObj.from + col
      const to = Math.min(from + 1, lineObj.to)
      const severity = m.severity === 'warning' ? 'warning'
        : m.severity === 'info' ? 'info'
        : 'error'
      return { from, to, severity, message: m.message }
    })
    view.value.dispatch(setDiagnostics(view.value.state as any, diagnostics))
  }

  function clearMarkers() {
    if (!view.value) return
    view.value.dispatch(setDiagnostics(view.value.state as any, []))
  }

  return { getValue, setValue, setMarkers, clearMarkers }
}
