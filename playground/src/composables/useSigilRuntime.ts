import { ref } from 'vue'
import { initWasm, getRuntime } from '@/lib/wasm-loader'
import type { SigilResult, SigilError } from '@/types/sigil'

const loading = ref(true)
const ready = ref(false)
const initError = ref<string | null>(null)

let initPromise: Promise<void> | null = null

function parseLineColumn(msg: string): { line?: number; column?: number } {
  const m = msg.match(/line (\d+)/i) || msg.match(/(\d+):(\d+)/)
  if (m) {
    return { line: parseInt(m[1]), column: m[2] ? parseInt(m[2]) : undefined }
  }
  return {}
}

export function useSigilRuntime() {
  async function initialize() {
    if (initPromise) return initPromise
    initPromise = (async () => {
      try {
        console.log('[sigil] Initializing WASM runtime...')
        await initWasm()
        ready.value = true
        console.log('[sigil] WASM runtime ready')
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e)
        initError.value = msg
        console.error('[sigil] WASM init failed:', msg)
      } finally {
        loading.value = false
      }
    })()
    return initPromise
  }

  function run(source: string, inputJson: string): { result?: SigilResult; error?: SigilError } {
    if (!ready.value) return { error: { error: 'WASM runtime not ready' } }

    try {
      const runtime = getRuntime()
      console.log('[sigil] Running program...')
      const json = runtime.run(source, inputJson || '{}')
      const parsed = JSON.parse(json)

      if (parsed.error) {
        console.log('[sigil] Program error:', parsed.error)
        const lc = parseLineColumn(parsed.error)
        return { error: { error: parsed.error, ...lc } }
      }

      const result: SigilResult = {
        output_lines: parsed.output_lines ?? [],
        result: parsed.result,
        bindings: parsed.bindings ?? {},
        trace: parsed.trace ?? [],
      }
      console.log('[sigil] Program completed:', result.output_lines.length, 'output lines,', result.trace.length, 'trace entries')
      return { result }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      console.error('[sigil] Runtime error:', msg)
      return { error: { error: msg, ...parseLineColumn(msg) } }
    }
  }

  return { loading, ready, initError, initialize, run }
}
