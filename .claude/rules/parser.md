---
description: Parser and AST subsystem patterns
globs: ["src/sigil/parser/**", "tests/parser/**", "src/sigil/ast/**"]
---

# Parser Development Guide

@docs/spec/GRAMMAR.peg

## Architecture

- `src/sigil/ast/nodes.py` — 40+ frozen dataclasses for AST nodes
- `src/sigil/parser/parser.py` — Hand-written recursive descent parser
- PEG-based: unambiguous, linear-time, maximum control
- **No external parser libraries** — deliberate design choice

## Key Patterns

- All AST nodes use `@dataclass(frozen=True)` with `tuple` for sequences
- Parser methods: `_parse_X()` returns AST node, `_expect(TokenType)` for mandatory tokens
- Expression precedence: `_parse_expression()` → `_parse_or()` → ... → `_parse_primary()`
- Condition parser uses `_parse_additive()` NOT `_parse_expression()` to avoid consuming `|>` tokens
- Keyword-safe dotted names: `_expect_identifier_or_keyword()` allows `sigil.list` etc.

## Grammar Gaps (Fixed)

8 gaps found between GRAMMAR.peg and examples in Phase 1:
1. Space-based field access (`reading temperature`)
2. Parameterless compute
3. `becomes` keyword
4. `empty list` / `empty` expression
5. `is not assigned` condition
6. Nested inline records
7. Actions as variable setting (SetAction)
8. Multi-word actions with positional args

## Adding New Syntax

1. Add token type to `TokenType` enum if needed
2. Add AST node to `nodes.py` (frozen dataclass)
3. Add parser method `_parse_X()`
4. Wire into the appropriate precedence level
5. Add tests for happy path + error cases
6. Update `docs/spec/GRAMMAR.peg`

75+ tests in `tests/parser/`.
