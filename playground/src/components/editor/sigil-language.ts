import * as monaco from 'monaco-editor'

const SIGIL_KEYWORDS = [
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

const SIGIL_UNITS = [
  'degrees', 'percent', 'seconds', 'milliseconds', 'dollars', 'confidence', 'years',
]

const SIGIL_TYPES = ['Number', 'Text', 'Symbol', 'Bool', 'List']

let registered = false

export function registerSigilLanguage() {
  if (registered) return
  registered = true

  monaco.languages.register({ id: 'sigil', extensions: ['.sigil'] })

  monaco.languages.setMonarchTokensProvider('sigil', {
    keywords: SIGIL_KEYWORDS,
    units: SIGIL_UNITS,
    typeKeywords: SIGIL_TYPES,

    tokenizer: {
      root: [
        // Doc comments
        [/---.*$/, 'comment.doc'],
        // Multi-line comments
        [/\{-/, 'comment', '@comment'],
        // Single-line comments
        [/--.*$/, 'comment'],

        // Strings with interpolation
        [/"/, 'string', '@string'],

        // Symbols (:name)
        [/:[a-zA-Z_]\w*/, 'variable.symbol'],

        // Numbers with optional unit
        [/\d+\.\d+/, 'number.float'],
        [/\d+/, 'number'],

        // Identifiers and keywords
        [/[a-zA-Z_]\w*/, {
          cases: {
            '@typeKeywords': 'type',
            '@keywords': 'keyword',
            '@units': 'keyword.unit',
            '@default': 'identifier',
          },
        }],

        // Operators
        [/\|>/, 'operator.pipe'],
        [/->/, 'operator.arrow'],
        [/>=|<=|!=/, 'operator.comparison'],
        [/[+\-*/><]=?/, 'operator'],
        [/\./, 'delimiter.dot'],
        [/::/, 'delimiter.scope'],

        // Delimiters
        [/[()[\]{}]/, 'delimiter.bracket'],
        [/[,:]/, 'delimiter'],
      ],

      comment: [
        [/[^{}-]+/, 'comment'],
        [/-\}/, 'comment', '@pop'],
        [/./, 'comment'],
      ],

      string: [
        [/\{/, 'string.interpolation', '@interpolation'],
        [/[^"\\{]+/, 'string'],
        [/\\./, 'string.escape'],
        [/"/, 'string', '@pop'],
      ],

      interpolation: [
        [/\}/, 'string.interpolation', '@pop'],
        [/[^}]+/, 'variable'],
      ],
    },
  })

  monaco.languages.setLanguageConfiguration('sigil', {
    comments: {
      lineComment: '--',
      blockComment: ['{-', '-}'],
    },
    brackets: [
      ['(', ')'],
      ['[', ']'],
      ['{', '}'],
    ],
    autoClosingPairs: [
      { open: '(', close: ')' },
      { open: '[', close: ']' },
      { open: '{', close: '}' },
      { open: '"', close: '"' },
    ],
    indentationRules: {
      increaseIndentPattern: /:\s*$/,
      decreaseIndentPattern: /^\s*(else|then)\b/,
    },
  })

  monaco.languages.registerCompletionItemProvider('sigil', {
    provideCompletionItems(model, position) {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }

      const keywordSuggestions = SIGIL_KEYWORDS.map((kw) => ({
        label: kw,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: kw,
        range,
      }))

      const snippets = [
        {
          label: 'rule',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'rule ${1:name}:\n  when ${2:condition}\n  then ${3:action}\n  explain "${4:reason}"',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define a new rule',
          range,
        },
        {
          label: 'compute',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'compute ${1:name} from ${2:param}: ${3:Number} returns ${4:Number}:\n  return ${5:expression}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define a compute function',
          range,
        },
        {
          label: 'main',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'main:\n  ${1:given x as 42}\n  ${2:print(x)}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define the main block',
          range,
        },
        {
          label: 'define',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'define ${1:NAME} as ${2:value}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define a constant',
          range,
        },
        {
          label: 'type record',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'type ${1:Name} is record:\n  ${2:field}: ${3:Number}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define a record type',
          range,
        },
        {
          label: 'match',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'match ${1:expr}:\n  ${2::value} -> ${3:result}\n  _ -> ${4:default}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Match expression',
          range,
        },
      ]

      return { suggestions: [...keywordSuggestions, ...snippets] }
    },
  })

  // Light theme
  monaco.editor.defineTheme('sigil-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '1d4ed8', fontStyle: 'bold' },
      { token: 'keyword.unit', foreground: 'b45309' },
      { token: 'variable.symbol', foreground: '7c3aed' },
      { token: 'string', foreground: '15803d' },
      { token: 'string.interpolation', foreground: '0891b2' },
      { token: 'string.escape', foreground: '15803d', fontStyle: 'bold' },
      { token: 'number', foreground: 'c2410c' },
      { token: 'number.float', foreground: 'c2410c' },
      { token: 'comment', foreground: '64748b', fontStyle: 'italic' },
      { token: 'comment.doc', foreground: '475569', fontStyle: 'italic bold' },
      { token: 'type', foreground: '0e7490', fontStyle: 'bold' },
      { token: 'operator', foreground: '475569' },
      { token: 'operator.pipe', foreground: '7c3aed', fontStyle: 'bold' },
      { token: 'operator.arrow', foreground: '7c3aed' },
      { token: 'delimiter', foreground: '64748b' },
      { token: 'identifier', foreground: '1e293b' },
    ],
    colors: {
      'editor.background': '#ffffff',
      'editor.foreground': '#1e293b',
      'editor.lineHighlightBackground': '#f8fafc',
      'editorLineNumber.foreground': '#94a3b8',
      'editorCursor.foreground': '#0ea5e9',
    },
  })

  // Dark theme
  monaco.editor.defineTheme('sigil-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '38bdf8', fontStyle: 'bold' },
      { token: 'keyword.unit', foreground: 'fbbf24' },
      { token: 'variable.symbol', foreground: 'a78bfa' },
      { token: 'string', foreground: '34d399' },
      { token: 'string.interpolation', foreground: '22d3ee' },
      { token: 'string.escape', foreground: '34d399', fontStyle: 'bold' },
      { token: 'number', foreground: 'fb923c' },
      { token: 'number.float', foreground: 'fb923c' },
      { token: 'comment', foreground: '64748b', fontStyle: 'italic' },
      { token: 'comment.doc', foreground: '94a3b8', fontStyle: 'italic bold' },
      { token: 'type', foreground: '22d3ee', fontStyle: 'bold' },
      { token: 'operator', foreground: '94a3b8' },
      { token: 'operator.pipe', foreground: 'a78bfa', fontStyle: 'bold' },
      { token: 'operator.arrow', foreground: 'a78bfa' },
      { token: 'delimiter', foreground: '64748b' },
      { token: 'identifier', foreground: 'e2e8f0' },
    ],
    colors: {
      'editor.background': '#0f172a',
      'editor.foreground': '#e2e8f0',
      'editor.lineHighlightBackground': '#1e293b',
      'editorLineNumber.foreground': '#475569',
      'editorCursor.foreground': '#0ea5e9',
    },
  })
}
