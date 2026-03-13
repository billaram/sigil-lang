---
description: Known issues, their causes, and fixes — check before debugging
---

# Known Issues

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | `--trace` shows only `print()` output, no rule trace | `format_trace()` only rendered forward chaining `rule_traces`. Backward chaining `proof_trees` never rendered. | Added `_format_proof_node()` recursive formatter and "Backward Chaining" section to `format_trace()` in `trace.py`. |
| 2 | `print()` shows `<object object at 0x...>` on failed query | Failed `query` left goal as `_UNBOUND` sentinel. `format_value()` fell through to `repr()`. | `_eval_query` binds goal to `None` on failure. `format_value` handles `_UNBOUND` as `"none"`. |
| 3 | `--trace` shows `FAILED (from environment)` for unproved queries | `_format_proof_node` used `(from environment)` for any `ProofNode` without a rule. | Three-way display: `via <rule>` / `(from environment)` / `(no matching rule)`. |
| 4 | `within 30 seconds` parse error: expected IDENTIFIER got UNIT | `seconds` lexed as UNIT token, not IDENTIFIER. Temporal parser didn't accept UNIT. | Temporal parser checks: unit on literal, UNIT token, then falls back to identifier. |
| 5 | `return` in `main:` raises unhandled `ReturnSignal` | `_eval_main()` doesn't catch `ReturnSignal`. | Use `given` + `print()` in main blocks. Documented as language constraint. |
