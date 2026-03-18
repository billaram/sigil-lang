import { StreamLanguage, LanguageSupport } from '@codemirror/language'
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language'
import { tags } from '@lezer/highlight'
import { autocompletion, snippet, type CompletionContext, type Completion } from '@codemirror/autocomplete'
import { EditorView } from '@codemirror/view'

// ---------------------------------------------------------------------------
// Keyword / token sets
// ---------------------------------------------------------------------------

const SIGIL_KEYWORDS = new Set([
  'rule', 'when', 'then', 'and', 'or', 'not', 'if', 'else',
  'given', 'define', 'as', 'is', 'exceeds', 'below', 'between',
  'any', 'all', 'none', 'in',
  'import', 'export', 'from', 'module', 'type', 'neural', 'explain', 'with',
  'true', 'false', 'using', 'compute', 'return', 'trace', 'match',
  'for', 'each', 'evaluate', 'main',
  'has', 'have', 'private', 'mutable', 'try', 'on', 'error',
  'fallback', 'to', 'returns', 'record', 'one', 'of', 'priority',
  'at', 'least', 'most', 'becomes', 'empty',
  'contains', 'starts', 'ends', 'matches', 'pattern', 'equals',
  'python', 'rust', 'list', 'Option', 'filter', 'where', 'sort', 'by',
  'take', 'first', 'last', 'map', 'ascending', 'descending',
  'assigned', 'count', 'query', 'within',
])

const SIGIL_UNITS = new Set([
  'degrees', 'percent', 'seconds', 'milliseconds', 'dollars', 'confidence', 'years',
])

const SIGIL_TYPES = new Set(['Number', 'Text', 'Symbol', 'Bool', 'List'])

// ---------------------------------------------------------------------------
// StreamLanguage tokenizer
// ---------------------------------------------------------------------------

interface SigilState {
  context: 'root' | 'blockComment' | 'string' | 'interpolation'
  commentDepth: number
}

const sigilStreamParser = StreamLanguage.define<SigilState>({
  startState(): SigilState {
    return { context: 'root', commentDepth: 0 }
  },

  token(stream, state): string | null {
    switch (state.context) {
      case 'blockComment':
        return tokenBlockComment(stream, state)
      case 'string':
        return tokenString(stream, state)
      case 'interpolation':
        return tokenInterpolation(stream, state)
      default:
        return tokenRoot(stream, state)
    }
  },

  languageData: {
    commentTokens: { line: '--', block: { open: '{-', close: '-}' } },
    closeBrackets: { brackets: ['(', '[', '{', '"'] },
    indentOnInput: /:\s*$/,
  },
})

function tokenRoot(stream: any, state: SigilState): string | null {
  // Whitespace
  if (stream.eatSpace()) return null

  // Doc comments (--- ...)
  if (stream.match('---')) {
    stream.skipToEnd()
    return 'docComment'
  }

  // Block comment start
  if (stream.match('{-')) {
    state.context = 'blockComment'
    state.commentDepth = 1
    return 'blockComment'
  }

  // Line comment (-- ...)
  if (stream.match('--')) {
    stream.skipToEnd()
    return 'lineComment'
  }

  // String start
  if (stream.match('"')) {
    state.context = 'string'
    return 'string'
  }

  // Symbols (:name)
  if (stream.match(/^:[a-zA-Z_]\w*/)) {
    return 'atom'
  }

  // Numbers (float then int)
  if (stream.match(/^\d+\.\d+/)) {
    return 'number'
  }
  if (stream.match(/^\d+/)) {
    return 'number'
  }

  // Pipe operator
  if (stream.match('|>')) {
    return 'operatorKeyword'
  }

  // Arrow operator
  if (stream.match('->')) {
    return 'operator'
  }

  // Lambda arrow
  if (stream.match('=>')) {
    return 'operator'
  }

  // Multi-char comparison operators
  if (stream.match('>=') || stream.match('<=') || stream.match('!=')) {
    return 'operator'
  }

  // Scope operator
  if (stream.match('::')) {
    return 'operator'
  }

  // Single-char operators
  if (stream.match(/^[+\-*/><]=?/)) {
    return 'operator'
  }

  // Dot
  if (stream.eat('.')) {
    return 'operator'
  }

  // Delimiters
  if (stream.match(/^[()[\]{}]/)) {
    return 'bracket'
  }

  if (stream.match(/^[,;]/)) {
    return 'punctuation'
  }

  if (stream.eat(':')) {
    return 'punctuation'
  }

  // Identifiers / keywords
  if (stream.match(/^[a-zA-Z_]\w*/)) {
    const word = stream.current()
    if (SIGIL_TYPES.has(word)) return 'typeName'
    if (SIGIL_KEYWORDS.has(word)) return 'keyword'
    if (SIGIL_UNITS.has(word)) return 'unit'
    return 'variableName'
  }

  // Advance on unknown char
  stream.next()
  return null
}

function tokenBlockComment(stream: any, state: SigilState): string {
  while (!stream.eol()) {
    if (stream.match('-}')) {
      state.commentDepth--
      if (state.commentDepth <= 0) {
        state.context = 'root'
        return 'blockComment'
      }
    } else if (stream.match('{-')) {
      state.commentDepth++
    } else {
      stream.next()
    }
  }
  return 'blockComment'
}

function tokenString(stream: any, state: SigilState): string {
  // Interpolation start
  if (stream.eat('{')) {
    state.context = 'interpolation'
    return 'meta'
  }

  // Escape sequence
  if (stream.match(/^\\./)) {
    return 'escape'
  }

  // End of string
  if (stream.eat('"')) {
    state.context = 'root'
    return 'string'
  }

  // String content
  if (stream.match(/^[^"\\{]+/)) {
    return 'string'
  }

  stream.next()
  return 'string'
}

function tokenInterpolation(stream: any, state: SigilState): string {
  if (stream.eat('}')) {
    state.context = 'string'
    return 'meta'
  }
  if (stream.match(/^[^}]+/)) {
    return 'variableName'
  }
  stream.next()
  return 'variableName'
}

// ---------------------------------------------------------------------------
// Themes
// ---------------------------------------------------------------------------

const lightHighlightStyle = HighlightStyle.define([
  { tag: tags.keyword, color: '#1d4ed8', fontWeight: 'bold' },
  { tag: tags.unit, color: '#b45309' },
  { tag: tags.atom, color: '#7c3aed' },
  { tag: tags.string, color: '#15803d' },
  { tag: tags.meta, color: '#0891b2' },
  { tag: tags.escape, color: '#15803d', fontWeight: 'bold' },
  { tag: tags.number, color: '#c2410c' },
  { tag: tags.lineComment, color: '#64748b', fontStyle: 'italic' },
  { tag: tags.docComment, color: '#475569', fontStyle: 'italic', fontWeight: 'bold' },
  { tag: tags.blockComment, color: '#64748b', fontStyle: 'italic' },
  { tag: tags.typeName, color: '#0e7490', fontWeight: 'bold' },
  { tag: tags.operator, color: '#475569' },
  { tag: tags.operatorKeyword, color: '#7c3aed', fontWeight: 'bold' },
  { tag: tags.variableName, color: '#1e293b' },
  { tag: tags.bracket, color: '#64748b' },
  { tag: tags.punctuation, color: '#64748b' },
])

const lightEditorTheme = EditorView.theme({
  '&': {
    backgroundColor: '#ffffff',
    color: '#1e293b',
  },
  '.cm-content': {
    caretColor: '#0ea5e9',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
    fontSize: '14px',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: '#0ea5e9',
  },
  '.cm-activeLine': {
    backgroundColor: '#f8fafc',
  },
  '.cm-gutters': {
    backgroundColor: '#ffffff',
    color: '#94a3b8',
    borderRight: '1px solid #e2e8f0',
  },
  '.cm-activeLineGutter': {
    backgroundColor: '#f8fafc',
  },
  '.cm-selectionBackground, &.cm-focused .cm-selectionBackground': {
    backgroundColor: '#dbeafe',
  },
  '.cm-tooltip': {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
  },
  '.cm-tooltip-autocomplete': {
    '& > ul > li[aria-selected]': {
      backgroundColor: '#dbeafe',
      color: '#1e293b',
    },
  },
}, { dark: false })

const darkHighlightStyle = HighlightStyle.define([
  { tag: tags.keyword, color: '#38bdf8', fontWeight: 'bold' },
  { tag: tags.unit, color: '#fbbf24' },
  { tag: tags.atom, color: '#a78bfa' },
  { tag: tags.string, color: '#34d399' },
  { tag: tags.meta, color: '#22d3ee' },
  { tag: tags.escape, color: '#34d399', fontWeight: 'bold' },
  { tag: tags.number, color: '#fb923c' },
  { tag: tags.lineComment, color: '#64748b', fontStyle: 'italic' },
  { tag: tags.docComment, color: '#94a3b8', fontStyle: 'italic', fontWeight: 'bold' },
  { tag: tags.blockComment, color: '#64748b', fontStyle: 'italic' },
  { tag: tags.typeName, color: '#22d3ee', fontWeight: 'bold' },
  { tag: tags.operator, color: '#94a3b8' },
  { tag: tags.operatorKeyword, color: '#a78bfa', fontWeight: 'bold' },
  { tag: tags.variableName, color: '#e2e8f0' },
  { tag: tags.bracket, color: '#64748b' },
  { tag: tags.punctuation, color: '#64748b' },
])

const darkEditorTheme = EditorView.theme({
  '&': {
    backgroundColor: '#0f172a',
    color: '#e2e8f0',
  },
  '.cm-content': {
    caretColor: '#0ea5e9',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
    fontSize: '14px',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: '#0ea5e9',
  },
  '.cm-activeLine': {
    backgroundColor: '#1e293b',
  },
  '.cm-gutters': {
    backgroundColor: '#0f172a',
    color: '#475569',
    borderRight: '1px solid #1e293b',
  },
  '.cm-activeLineGutter': {
    backgroundColor: '#1e293b',
  },
  '.cm-selectionBackground, &.cm-focused .cm-selectionBackground': {
    backgroundColor: '#1e3a5f',
  },
  '.cm-tooltip': {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    color: '#e2e8f0',
  },
  '.cm-tooltip-autocomplete': {
    '& > ul > li[aria-selected]': {
      backgroundColor: '#334155',
      color: '#e2e8f0',
    },
  },
}, { dark: true })

export const sigilLightTheme = [lightEditorTheme, syntaxHighlighting(lightHighlightStyle)]
export const sigilDarkTheme = [darkEditorTheme, syntaxHighlighting(darkHighlightStyle)]

// ---------------------------------------------------------------------------
// Completions + snippets
// ---------------------------------------------------------------------------

const KEYWORD_LIST = [
  'rule', 'when', 'then', 'and', 'or', 'not', 'if', 'else',
  'given', 'define', 'as', 'is', 'exceeds', 'below', 'between',
  'any', 'all', 'none', 'in',
  'import', 'export', 'from', 'module', 'type', 'neural', 'explain', 'with',
  'true', 'false', 'using', 'compute', 'return', 'trace', 'match',
  'for', 'each', 'evaluate', 'main',
  'has', 'have', 'private', 'mutable', 'try', 'on', 'error',
  'fallback', 'to', 'returns', 'record', 'one', 'of', 'priority',
  'at', 'least', 'most', 'becomes', 'empty',
  'contains', 'starts', 'ends', 'matches', 'pattern', 'equals',
  'python', 'rust', 'list', 'Option', 'filter', 'where', 'sort', 'by',
  'take', 'first', 'last', 'map', 'ascending', 'descending',
  'assigned', 'count', 'query', 'within',
]

const snippetCompletions: Completion[] = [
  {
    label: 'rule',
    type: 'snippet',
    detail: 'Define a new rule',
    apply: snippet('rule ${name}:\n  when ${condition}\n  then ${action}\n  explain "${reason}"'),
  },
  {
    label: 'compute',
    type: 'snippet',
    detail: 'Define a compute function',
    apply: snippet('compute ${name} from ${param}: ${Number} returns ${Number}:\n  return ${expression}'),
  },
  {
    label: 'main',
    type: 'snippet',
    detail: 'Define the main block',
    apply: snippet('main:\n  given ${x} as ${42}\n  print(${x})'),
  },
  {
    label: 'define',
    type: 'snippet',
    detail: 'Define a constant',
    apply: snippet('define ${NAME} as ${value}'),
  },
  {
    label: 'type record',
    type: 'snippet',
    detail: 'Define a record type',
    apply: snippet('type ${Name} is record:\n  ${field}: ${Number}'),
  },
  {
    label: 'match',
    type: 'snippet',
    detail: 'Match expression',
    apply: snippet('match ${expr}:\n  ${:value} -> ${result}\n  _ -> ${default}'),
  },
]

function sigilCompletions(context: CompletionContext) {
  const word = context.matchBefore(/[a-zA-Z_]\w*/)
  if (!word) return null
  if (word.from === word.to && !context.explicit) return null

  const keywordItems: Completion[] = KEYWORD_LIST.map((kw) => ({
    label: kw,
    type: 'keyword',
  }))

  return {
    from: word.from,
    options: [...keywordItems, ...snippetCompletions],
  }
}

// ---------------------------------------------------------------------------
// Exported LanguageSupport
// ---------------------------------------------------------------------------

export const sigilLanguage = new LanguageSupport(sigilStreamParser, [
  autocompletion({ override: [sigilCompletions] }),
])
