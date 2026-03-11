---
description: Standard library patterns — adding and testing stdlib functions
globs: ["src/sigil/stdlib/**", "tests/stdlib/**"]
---

# Standard Library Development Guide

## Architecture

- `src/sigil/stdlib/_builtins.py` — All Python-backed stdlib functions
- `src/sigil/stdlib/__init__.py` — Registry with `get_stdlib_module()`

## Available Modules

| Module | Functions |
|--------|-----------|
| `sigil.math` | sqrt, abs, floor, ceil, round, pow, log, sin, cos, PI, E |
| `sigil.text` | length, substring, split, join, lowercase, uppercase, trim, replace, starts_with, ends_with |
| `sigil.list` | range, reverse, flatten, unique, zip, sum, count, length |
| `sigil.logic` | xor, implies, nand, type_of, is_number, is_text, is_list |
| `sigil.time` | now, now_ms, format_timestamp, elapsed, duration_seconds |
| `sigil.trace` | to_json, fired_rules, rule_count, duration_ms |
| `sigil.io` | read_file, write_file, file_exists, parse_json, to_json |

## Function Signature Pattern

All stdlib functions use this signature:
```python
def my_func(args: list[Value], trace: ProgramTrace) -> Value:
    ...
```

## Adding a New Stdlib Function

1. Add function to `_builtins.py` following the signature pattern
2. Register in the module dict within `get_stdlib_module()`
3. Add unit tests in `tests/stdlib/`
4. Update this doc

## Test Pattern

Tests call functions directly with a `ProgramTrace` fixture:
```python
def test_math_sqrt(trace_fixture):
    result = stdlib_sqrt([25.0], trace_fixture)
    assert result == 5.0
```
