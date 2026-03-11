---
description: Type checker subsystem patterns
globs: ["src/sigil/types/**", "tests/typechecker/**"]
---

# Type Checker Development Guide

@docs/design/TYPE_SYSTEM.md

## Architecture

- `src/sigil/types/checker.py` (~550 lines) — Two-phase type checker

## Two-Phase Design

**Phase 1 — Scan**: Walk declarations, build symbol table, collect settable names
**Phase 2 — Check**: Walk bodies, produce diagnostics

## 11 Check Types

1. Undefined variables
2. Undefined fields (on typed compute params)
3. Comparison type mismatches
4. Function arity
5. Duplicate declarations
6. Match exhaustiveness
7. Pipeline validation
8. Lambda type checking
9. Return type consistency
10. Gradual type inference from `given` literals
11. Unit awareness — warn on unit suffix mismatches

## Gradual Typing

- Type annotations optional in general, required at boundaries (function params, exports)
- Annotations use `: Type` syntax: `Number`, `Text`, `Symbol`, `Bool`, record types
- Type checker produces diagnostics (errors + warnings), does NOT block execution

## Adding a New Check

1. Define new diagnostic type/message
2. Add detection logic to Phase 2 walk
3. Add tests in `tests/typechecker/`
4. Update this doc and STATUS.md

39+ Phase 1 tests, 12 Phase 2 tests, 15 enhanced inference tests.
