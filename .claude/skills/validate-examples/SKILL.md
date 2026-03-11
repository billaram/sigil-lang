---
description: Run all .sigil example programs and integration tests
model_invocable: true
---

# Validate Examples

Run all `.sigil` example programs to verify they lex, parse, and execute correctly.

## Steps

1. Find all example files:
   ```bash
   find examples/ -name "*.sigil" | sort
   ```

2. Run each example through the CLI:
   ```bash
   source .venv/bin/activate && for f in examples/**/*.sigil; do
     echo "=== $f ==="
     sigil run "$f" 2>&1 || echo "FAILED: $f"
     echo
   done
   ```

3. Run integration tests:
   ```bash
   source .venv/bin/activate && pytest tests/integration/ -v --tb=short 2>&1
   ```

4. Report results:
   - List all examples with pass/fail status
   - Show errors for any failures
   - Confirm total count of working examples
