---
description: Run the Sigil test suite with appropriate flags
model_invocable: true
---

# Run Tests

Run the Sigil test suite. Accepts an optional subsystem argument.

## Usage

`/run-tests` — run all tests
`/run-tests lexer` — run lexer tests only
`/run-tests parser` — run parser tests only
`/run-tests interpreter` — run interpreter tests only
`/run-tests typechecker` — run type checker tests only
`/run-tests stdlib` — run stdlib tests only
`/run-tests modules` — run module system tests only

## Steps

1. Determine the test path based on the argument:
   - No argument → `tests/`
   - `lexer` → `tests/lexer/`
   - `parser` → `tests/parser/`
   - `interpreter` → `tests/interpreter/`
   - `typechecker` → `tests/typechecker/`
   - `stdlib` → `tests/stdlib/`
   - `modules` → `tests/modules/`
   - Any other value → use as-is (e.g., `tests/integration/`)

2. Run the test command:
   ```bash
   source .venv/bin/activate && pytest <test_path> -v --tb=short 2>&1
   ```

3. Report results:
   - Number of tests passed/failed/skipped
   - If failures: show the failing test names and short tracebacks
   - If all pass: confirm with count
