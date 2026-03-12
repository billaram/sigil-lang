# Phase 4 Testing Guide

A hands-on walkthrough to verify every Phase 4 feature. Work through each section in order.

---

## Prerequisites

```bash
cd sigil-lang
source .venv/bin/activate
pip install -e ".[dev]"
maturin develop
```

---

## 1. Error Suggestions

All errors now include `hint:` messages with actionable fix suggestions.

### Test 1.1 — Lexer tab error
```bash
printf '\trule bad:\n' > /tmp/test_tab.sigil
sigil run /tmp/test_tab.sigil
```
**Expected**: Error mentioning tabs, with `hint: use spaces (2 per level) instead of tabs`

### Test 1.2 — Parser missing colon
```bash
printf 'rule check\n  when x exceeds 100\n  then alert\n' > /tmp/test_colon.sigil
sigil run /tmp/test_colon.sigil
```
**Expected**: Parse error with `hint: add ':' after the declaration header`

### Test 1.3 — Parser missing indent
```bash
printf 'rule check:\nwhen x exceeds 100\nthen alert\n' > /tmp/test_indent.sigil
sigil run /tmp/test_indent.sigil
```
**Expected**: Error with `hint: add 2 spaces of indentation for the block body`

---

## 2. Parser Error Recovery

The parser now collects multiple errors instead of stopping at the first one.

### Test 2.1 — Multiple errors reported
```bash
cat > /tmp/test_multi_error.sigil << 'EOF'
rule bad1
  when x exceeds 100
  then alert

rule bad2
  when y exceeds 200
  then notify

define X as 42
EOF
sigil run /tmp/test_multi_error.sigil
```
**Expected**: Two parse errors reported (one for each broken rule), not just the first one. The valid `define X as 42` is still parsed.

---

## 3. Did-You-Mean Suggestions

Undefined function calls now suggest the closest match.

### Test 3.1 — Typo in function name
```bash
cat > /tmp/test_didyoumean.sigil << 'EOF'
compute calculate from x: Number returns Number:
  return x * 2

main:
  given result as calculat(5)
  print(result)
EOF
sigil run /tmp/test_didyoumean.sigil
```
**Expected**: Runtime error for `calculat` with `hint: did you mean 'calculate'?`

---

## 4. Unused Declaration Warnings

The type checker now warns about unused constants and compute functions.

### Test 4.1 — Unused constant
```bash
cat > /tmp/test_unused.sigil << 'EOF'
define THRESHOLD as 100
define UNUSED_CONST as 999

main:
  print(THRESHOLD)
EOF
sigil check /tmp/test_unused.sigil
```
**Expected**: Warning about `UNUSED_CONST` being defined but never used.

### Test 4.2 — Warnings as errors
```bash
sigil check /tmp/test_unused.sigil --warnings-as-errors
```
**Expected**: Exit code 1 (the unused warning is treated as an error).

---

## 5. Call Stack Traces

Runtime errors now show the Sigil call stack.

### Test 5.1 — Error inside nested compute call
```bash
cat > /tmp/test_stack.sigil << 'EOF'
compute inner from x: Number returns Number:
  return x / 0

compute outer from x: Number returns Number:
  return inner(x)

main:
  given result as outer(5)
  print(result)
EOF
sigil run /tmp/test_stack.sigil
```
**Expected**: Runtime error with a call stack showing `outer` and `inner`.

---

## 6. Formatter

`sigil fmt` reformats Sigil source code via AST round-trip.

### Test 6.1 — Format a file
```bash
sigil fmt examples/basics/hello.sigil
```
**Expected**: Well-formatted Sigil source printed to stdout with consistent 2-space indentation and blank lines between declarations.

### Test 6.2 — Format check (already formatted)
```bash
sigil fmt examples/getting_started/calculator.sigil --check
```
**Expected**: Message saying file is already formatted (or needs formatting). Exit code 0 if formatted, 1 if not.

### Test 6.3 — Round-trip test
```bash
sigil fmt examples/basics/temperature.sigil > /tmp/formatted.sigil
sigil fmt /tmp/formatted.sigil --check
```
**Expected**: Second command exits 0 — formatting is idempotent.

---

## 7. Linter

`sigil lint` runs semantic checks beyond the type checker.

### Test 7.1 — Clean file
```bash
sigil lint examples/getting_started/calculator.sigil
```
**Expected**: `no issues found`

### Test 7.2 — Neural confidence out of range
```bash
cat > /tmp/test_lint.sigil << 'EOF'
neural classify from text: Text:
  model "hf:some-model"
  returns Symbol
  confidence_threshold 1.5
  fallback to :unknown
EOF
sigil lint /tmp/test_lint.sigil
```
**Expected**: Warning about `confidence_threshold 1.5` being out of range [0.0, 1.0], with hint to set between 0.0 and 1.0.

### Test 7.3 — Strict mode
```bash
sigil lint /tmp/test_lint.sigil --strict
```
**Expected**: Exit code 1 (warning treated as error in strict mode).

---

## 8. REPL — History and Tab Completion

### Test 8.1 — Basic REPL session
```bash
sigil repl
```
Then type:
```
sigil> :help
sigil> define MAX as 100
sigil> MAX + 50
sigil> :env
sigil> exit
```
**Expected**:
- `:help` shows all commands
- `MAX + 50` prints `=> 150`
- `:env` shows `MAX = 100`

### Test 8.2 — History persistence
```bash
sigil repl
```
Type a few expressions, then `exit`. Start again:
```bash
sigil repl
```
Press the **up arrow** key.

**Expected**: Previous session's inputs appear (history loaded from `~/.sigil_history`).

### Test 8.3 — Tab completion
```bash
sigil repl
```
Type `def` then press **Tab**.

**Expected**: Completes to `define` (or shows completion candidates).

Type `:` then press **Tab**.

**Expected**: Shows `:env`, `:rules`, `:funcs`, `:types`, `:trace`, `:reset`, `:help`.

### Test 8.4 — Multi-line input
```bash
sigil repl
```
Type:
```
sigil> rule test:
  ...>   when x exceeds 10
  ...>   then alert
  ...>
```
**Expected**: Prompt changes to `  ...>` for continuation lines. Empty line submits the block.

### Test 8.5 — REPL state commands
```bash
sigil repl
```
```
sigil> compute double from x: Number returns Number:
  ...>   return x * 2
  ...>
sigil> :funcs
sigil> double(21)
sigil> :reset
sigil> :funcs
sigil> exit
```
**Expected**:
- `:funcs` shows `double(x)` after defining it
- `double(21)` prints `=> 42`
- After `:reset`, `:funcs` shows `(no functions)`

---

## 9. NL-to-Sigil Generator

Requires `pip install anthropic` and `ANTHROPIC_API_KEY` set.

### Test 9.1 — Basic generation (no API key needed for error check)
```bash
sigil parse "a rule that alerts when temperature exceeds 100 degrees"
```
**Expected without API key**: Error message about `anthropic` package or missing API key.

### Test 9.2 — With API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
sigil parse "a rule that flags high-risk transactions over 10000 dollars from accounts less than 30 days old"
```
**Expected**: Valid Sigil code printed to stdout, with `-- [sigil] Generated code is valid.` on stderr.

### Test 9.3 — Interactive refinement
```bash
sigil parse "a neural sentiment classifier that analyzes customer reviews using a HuggingFace model and returns positive, negative, or neutral" --interactive
```
**Expected**: Generated code. If first attempt has issues, the generator automatically refines (up to 3 tries). Final output shows whether code is valid.

### Test 9.4 — Complex generation
```bash
sigil parse "a loan eligibility system: approve if credit score above 700 and debt ratio below 0.4, deny if credit score below 500, with a compute function for monthly payment from principal rate and term"
```
**Expected**: Multi-declaration Sigil program with rules, compute function, and constants.

---

## 10. CLI Commands — Quick Smoke Test

Run all of these and verify no crashes:

```bash
# Help
sigil --help

# Lex
sigil lex examples/basics/hello.sigil

# Parse AST
sigil parse-ast examples/getting_started/calculator.sigil

# Run
sigil run examples/getting_started/calculator.sigil

# Run with trace
sigil run examples/patterns/backward_chaining.sigil --trace

# Check
sigil check examples/getting_started/hello.sigil

# Format
sigil fmt examples/basics/temperature.sigil

# Lint
sigil lint examples/getting_started/calculator.sigil
```

**Expected**: All commands complete without crashes. Each produces appropriate output.

---

## 11. Example Programs

Verify the new Phase 4 examples run correctly:

```bash
sigil run examples/getting_started/hello.sigil
sigil run examples/getting_started/calculator.sigil
sigil run examples/patterns/backward_chaining.sigil
```

**Expected output for calculator.sigil**:
```
3 + 4 = 7
5 * 6 = 30
7^2 = 49
```

**Expected output for backward_chaining.sigil**:
```
Covered: true
```

---

## 12. Full Test Suite

```bash
pytest tests/ -v --tb=short 2>&1 | tail -5
```

**Expected**: `942 passed` (some may be skipped if optional deps missing).

---

## Summary Checklist

| # | Feature | Status |
|---|---------|--------|
| 1 | Error suggestions (hint messages) | |
| 2 | Parser error recovery (multiple errors) | |
| 3 | Did-you-mean for typos | |
| 4 | Unused declaration warnings | |
| 5 | Call stack traces | |
| 6 | `sigil fmt` (formatter) | |
| 7 | `sigil lint` (linter) | |
| 8 | REPL history + tab completion | |
| 9 | `sigil parse` (NL generator) | |
| 10 | CLI smoke test (all commands) | |
| 11 | New example programs | |
| 12 | Full test suite passes | |
