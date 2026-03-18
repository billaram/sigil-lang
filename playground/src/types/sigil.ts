export interface TraceEntry {
  rule: string
  priority: number
  fired: boolean
  explain: string
}

export interface SigilResult {
  output_lines: string[]
  result: unknown
  bindings: Record<string, unknown>
  trace: TraceEntry[]
}

export interface SigilError {
  error: string
  line?: number
  column?: number
}

export interface ExampleProgram {
  id: string
  name: string
  description: string
  source: string
  input: string
}
