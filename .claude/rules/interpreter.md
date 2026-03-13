---
description: Interpreter subsystem patterns — evaluator, chaining, values
globs: ["src/sigil/interpreter/**", "tests/interpreter/**"]
---

# Interpreter Development Guide

@docs/spec/SEMANTICS.md

## Architecture

- `evaluator.py` (~1230 lines) — Main tree-walking evaluator
- `backward.py` — Backward chaining engine (goal-driven `query`)
- `values.py` — Symbol, Record, Variant, Closure, Value union, `format_value`, `values_equal`
- `environment.py` — Immutable environment with scope chain
- `trace.py` — ConditionTrace, RuleTrace, ProgramTrace, TraceTimer, `format_trace`
- `builtins.py` — print, max, min, len builtins
- `repl.py` — Interactive REPL (~200 lines)

## Key Patterns

- **Forward chaining**: iterative until fixed point, max 100 iterations, `fired_rules` set prevents re-firing
- **Backward chaining**: `query <goal>` drives goal-directed evaluation; max depth 50, cycle detection via `_proving` set
- **`_UNBOUND` sentinel**: missing record fields return `_UNBOUND`, not errors — enables optional field patterns
- **`ReturnSignal`**: compute functions use exception-based return. Only `_call_compute` catches it. `main:` blocks do NOT catch it.
- **Neural stubs**: if variable already bound AND expression is neural call, keep existing value. Returns fallback values.
- **`given X from input`**: keeps existing env value. **`given X as expr`**: evaluates expression.
- **Block actions** (`then:`) use statement syntax (`given`, `return`, `for`, `becomes`), NOT set-action syntax (`x is value`)
- **Traces**: every rule evaluation produces auditable ConditionTrace + RuleTrace

## Test Helper

```python
def run(source, input_data=None):
    tokens = tokenize(source)
    program = parse(tokens)
    return evaluate(program, input_data or {})
```

137+ interpreter tests, 15 backward chaining tests.
