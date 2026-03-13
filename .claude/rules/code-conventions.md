---
description: Code style, naming, and patterns for all Sigil development
---

# Code Conventions

@ai_docs/CONVENTIONS.md

## Quick Reference

- **Python 3.11+** — dataclasses, type hints everywhere, `|` unions
- **Immutable AST**: `@dataclass(frozen=True)`, tuples not lists for sequences
- **Functions over classes** — lexer is a function, not a stateful class
- **Error hierarchy**: `SigilError` → `SigilLexError` / `SigilParseError` / `SigilTypeError` / `SigilRuntimeError`
- **Error messages**: source location + problematic text + what went wrong + fix suggestion
- **Naming**: modules=snake_case, classes=PascalCase, functions=snake_case, constants=UPPER_SNAKE, private=_leading_underscore
- **One concept per file**, max 400 lines, no circular imports
- **Linting**: `ruff check src/ tests/` must pass. Format: `ruff format src/ tests/`
- **Type checking**: `mypy src/sigil/` must pass
- **Tests alongside implementation** — never ship code without tests
- **Docstrings**: module-level required, function-level for public API only. Type hints ARE the docs.
- **Comments**: only *why*, never *what*
