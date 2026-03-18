import init, { SigilRuntime } from '../../wasm/_sigil_core'

let initialized = false
let runtime: SigilRuntime | null = null

export async function initWasm(): Promise<void> {
  if (initialized) return
  await init()
  runtime = new SigilRuntime()
  initialized = true
}

export function getRuntime(): SigilRuntime {
  if (!runtime) throw new Error('WASM not initialized — call initWasm() first')
  return runtime
}
