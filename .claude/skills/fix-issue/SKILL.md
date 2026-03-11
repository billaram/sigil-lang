---
description: Structured reproduce-diagnose-test-fix-verify workflow for bug fixing
model_invocable: true
---

# Fix Issue

Structured workflow for diagnosing and fixing bugs in Sigil.

## Steps

1. **Reproduce**: Write a minimal `.sigil` snippet or test case that triggers the bug. Run it:
   ```bash
   source .venv/bin/activate && sigil run <file_or_snippet> 2>&1
   ```

2. **Diagnose**: Trace through the pipeline to find where the bug originates:
   - Lexer issue? Run `sigil lex <file>` and inspect tokens
   - Parser issue? Run `sigil parse-ast <file>` and inspect AST
   - Type checker issue? Run `sigil check <file>` and inspect diagnostics
   - Interpreter issue? Run `sigil run <file> --trace` and inspect trace

3. **Test first**: Write a failing test that captures the bug:
   ```python
   def test_issue_description():
       # This should work but currently fails
       result = run("minimal reproduction")
       assert result == expected
   ```

4. **Fix**: Make the minimal code change to fix the issue. Prefer targeted fixes over broad refactors.

5. **Verify**: Run the full test suite to ensure no regressions:
   ```bash
   source .venv/bin/activate && pytest tests/ -v --tb=short 2>&1
   ```

6. **Document**: If the bug reveals a pattern worth remembering, add it to `.claude/rules/known-issues.md` and the Known Issues table in CLAUDE.md.
