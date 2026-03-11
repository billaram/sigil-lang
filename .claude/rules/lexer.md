---
description: Lexer subsystem patterns and gotchas
globs: ["src/sigil/lexer/**", "tests/lexer/**"]
---

# Lexer Development Guide

## Architecture

- `src/sigil/lexer/tokens.py` — `TokenType` enum (80+ variants), `Token` frozen dataclass, `UNIT_SUFFIXES`
- `src/sigil/lexer/lexer.py` — `tokenize()` function with indentation engine
- Lexer is a **function**, not a class — no mutable state between calls

## Key Patterns

- Indentation tracking: stack-based INDENT/DEDENT generation (Python-style)
- Unit suffixes: number literals consume trailing unit words (e.g., `100 degrees` → NUMBER with unit)
- `seconds`, `minutes`, `degrees`, etc. lex as UNIT tokens, NOT identifiers
- Keywords are case-sensitive, checked against `KEYWORDS` frozenset
- String interpolation: `{expr}` inside strings produces interpolation tokens
- Source location: every token carries `(line, column)` for error reporting

## Gotchas

- `seconds` is a UNIT token — temporal parser must handle this specially (Known Issue #4)
- INDENT/DEDENT must balance — every INDENT needs a matching DEDENT at EOF
- Comment lines (`--`) should not affect indentation tracking

## Test Pattern

```python
def test_lexer_tokenizes_X():
    tokens = tokenize("source text")
    assert tokens[0].type == TokenType.EXPECTED
    assert tokens[-1].type == TokenType.EOF
```

91 tests in `tests/lexer/`.
