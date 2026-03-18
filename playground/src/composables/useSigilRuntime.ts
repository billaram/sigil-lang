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
        await initWasm()
        ready.value = true
      } catch (e) {
        initError.value = e instanceof Error ? e.message : String(e)
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
      const json = runtime.run(source, inputJson || '{}')
      const parsed = JSON.parse(json)

      if (parsed.error) {
        const lc = parseLineColumn(parsed.error)
        return { error: { error: parsed.error, ...lc } }
      }

      return {
        result: {
          output_lines: parsed.output_lines ?? [],
          result: parsed.result,
          bindings: parsed.bindings ?? {},
        },
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return { error: { error: msg, ...parseLineColumn(msg) } }
    }
  }

  function compile(source: string): { programId?: number; error?: SigilError } {
    if (!ready.value) return { error: { error: 'WASM runtime not ready' } }
    try {
      const runtime = getRuntime()
      const id = runtime.compile(source)
      return { programId: id }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return { error: { error: msg, ...parseLineColumn(msg) } }
    }
  }

  function execute(programId: number, inputJson: string): { result?: SigilResult; error?: SigilError } {
    if (!ready.value) return { error: { error: 'WASM runtime not ready' } }
    try {
      const runtime = getRuntime()
      const json = runtime.execute(programId, inputJson || '{}')
      const parsed = JSON.parse(json)
      if (parsed.error) {
        return { error: { error: parsed.error, ...parseLineColumn(parsed.error) } }
      }
      return {
        result: {
          output_lines: parsed.output_lines ?? [],
          result: parsed.result,
          bindings: parsed.bindings ?? {},
        },
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      return { error: { error: msg, ...parseLineColumn(msg) } }
    }
  }

  return { loading, ready, initError, initialize, run, compile, execute }
}
