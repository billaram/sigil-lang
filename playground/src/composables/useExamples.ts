import { EXAMPLES } from '@/lib/examples'
import type { ExampleProgram } from '@/types/sigil'

export function useExamples() {
  const examples = EXAMPLES

  function loadExample(id: string): ExampleProgram | undefined {
    return examples.find((e) => e.id === id)
  }

  return { examples, loadExample }
}
