export interface SigilResult {
  output_lines: string[]
  result: unknown
  bindings: Record<string, unknown>
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
