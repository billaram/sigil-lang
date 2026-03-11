---
description: Testing patterns, helpers, and conventions
globs: ["tests/**"]
---

# Testing Guide

## Commands

```bash
pytest tests/ -v                   # All tests (665 total)
pytest tests/lexer/ -v             # Lexer only (91 tests)
pytest tests/parser/ -v            # Parser only (75+ tests)
pytest tests/interpreter/ -v       # Interpreter (137+ tests)
pytest tests/typechecker/ -v       # Type checker (39+ tests)
pytest tests/stdlib/ -v            # Stdlib (all modules)
pytest tests/modules/ -v           # Module system
pytest tests/ -v --tb=short        # Compact output
pytest tests/ -k "test_name" -v    # Run specific test
```

## Test Naming

```python
def test_<what>_<scenario>():
    # test_lexer_tokenizes_integer_literal
    # test_parser_parses_simple_rule
    # test_evaluator_handles_pipeline
```

## Helper Pattern

```python
def run(source, input_data=None):
    tokens = tokenize(source)
    program = parse(tokens)
    return evaluate(program, input_data or {})
```

## Input Data

`dict[str, Value]` where values can be `Record`, `Symbol`, primitives:
```python
result = run(source, {"temperature": 150, "status": Symbol("active")})
```

## Key Patterns

- **Unit tests**: one input, one assertion
- **Integration tests**: full `.sigil` example files
- **Property tests**: `@given(strategy)` with hypothesis for parser/lexer
- **Error tests**: `pytest.raises(SigilError, match="expected message")`
- **Module tests**: use `Evaluator` directly (not `evaluate()`) for loader config
- **Stdlib tests**: call functions directly with `ProgramTrace` fixture

## Unbound Variable Behavior

- Comparisons with unbound vars return `False`
- `is not` with unbound vars returns `True`
- Missing record fields return `_UNBOUND` sentinel
