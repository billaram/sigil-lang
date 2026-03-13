---
description: Sigil language syntax quick reference
globs: ["**/*.sigil", "src/sigil/parser/**", "src/sigil/lexer/**"]
---

# Sigil Language Quick Reference

@docs/design/SYNTAX.md
@docs/spec/GRAMMAR.peg

## Syntax at a Glance

```sigil
-- Comments start with --
-- ~30 keywords: rule, when, then, and, or, not, if, else, given, define,
--   as, is, exceeds, below, between, any, all, none, in,
--   import, export, module, type, neural, explain, with,
--   true, false, using, from, compute, return, trace, match,
--   for, each, evaluate, main

rule example_rule with priority 10:
  when x exceeds 100
  and y is between 10 and 50
  and status is :active
  then trigger alert with severity :critical
  explain "X exceeded threshold"

compute add from a: Number, b: Number returns Number:
  return a + b

neural classify from text: Text:
  model "classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  fallback to :unknown

type Person is record:
  name: Text
  age: Number

define MAX_TEMP as 100 degrees
```

## Key Syntax Patterns

- **Symbols**: `:active`, `:critical` — prefixed with colon
- **Units**: `100 degrees`, `30 seconds` — number followed by unit word
- **Field access**: `reading temperature` (space-based) or `reading.temperature` (dot)
- **Pipeline**: `data |> transform |> filter`
- **Match**: `match x: when :a then 1, when :b then 2`
- **Lambda**: `(x) => x + 1`
- **String interpolation**: `"Value is {variable}"`
- **Indentation**: significant whitespace, spaces only (Python-style)
