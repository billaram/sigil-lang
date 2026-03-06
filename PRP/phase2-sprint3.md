# Sigil — Phase 2 Sprint 3: Advanced Rules + Polish

## Prerequisites

**Sprint 2 must be complete** (module system, stdlib — 520+ tests).

---

## Sprint 3 Goal

> **Deliver backward chaining rules, temporal rule foundations, enhanced type inference, stdlib time/trace/io modules, performance benchmarks, and comprehensive documentation. Close Phase 2.**

### Sprint 3 Exit Criteria
- [ ] Backward chaining: `query` keyword triggers goal-driven evaluation
- [ ] Rule composition: rules can reference and compose other rules
- [ ] Temporal rule foundations: `within` duration constraints on conditions
- [ ] Enhanced type checker: gradual type inference, return type checking, unit type awareness
- [ ] Stdlib: `sigil.time`, `sigil.trace`, `sigil.io` modules
- [ ] Performance benchmarks: baseline measurements for lexer, parser, evaluator
- [ ] 10+ total new examples (across all of Phase 2)
- [ ] 80+ new tests → 600+ total (meets ROADMAP target)
- [ ] Full Phase 2 documentation update
- [ ] All existing tests still pass (no regressions)

### Phase 2 Exit Criteria (from ROADMAP.md)
- [x] Loan eligibility example works end-to-end (Phase 1)
- [ ] Module system works (import/export/resolution)
- [ ] Standard library covers basics (math, text, list, logic, time, trace, io)
- [ ] Pattern matching, pipeline, closures all work
- [ ] Advanced rules: backward chaining, temporal foundations
- [ ] 600+ tests passing

---

## What Must Be Built

### Backward Chaining

Forward chaining (Phase 1) is data-driven: "given these facts, what rules fire?"
Backward chaining is goal-driven: "to prove X, what facts/rules do I need?"

This is the core addition for Phase 2 advanced rules.

**Syntax** (from SYNTAX.md):
```sigil
-- Query: try to prove a goal by backward chaining
query loan_approved with applicant
```

Or in main blocks:
```sigil
main:
  given applicant from input
  query loan_approved with applicant
```

**Semantics**:
1. Look up rules that have `loan_approved` as a SetAction target
2. Check if those rules' conditions are satisfiable
3. If a condition references another set-action variable, recursively backward-chain
4. If all conditions of any matching rule are true, the goal succeeds
5. Produce a proof tree in the trace

### Temporal Rule Foundations

Full temporal rules (Phase 3+) need event streams and time windows. For Phase 2, we lay the groundwork:

```sigil
-- Temporal condition: X must be true for at least 5 seconds
rule sustained_alert with priority 50:
  when temperature exceeds 100
  within 5 seconds        -- NEW: temporal constraint
  then trigger alarm
```

For Sprint 3, we implement:
- `within` keyword parsed and stored in AST
- Temporal conditions tracked but evaluated as "point-in-time" (no actual duration tracking)
- `sigil.time` stdlib provides current time, duration arithmetic
- Foundation for Phase 3's event stream processing

### Enhanced Type Inference

Phase 1 type checker does 5 basic checks. Phase 2 needs:

1. **Return type consistency**: If `compute f returns Number`, verify all return paths produce numbers
2. **Gradual inference**: Infer types from context (e.g., `given x as 42` → x is Number)
3. **Unit type awareness**: Warn when mixing `degrees` and `seconds`
4. **Module boundary checks**: Verify imported types match expected signatures
5. **Closure parameter types**: Infer types when passing closures to typed functions

---

## Step-by-Step Implementation Plan

### Step 1: Backward Chaining Engine

**File**: `src/sigil/interpreter/backward.py` (NEW)

```python
@dataclass
class ProofNode:
    """A node in the backward chaining proof tree."""
    goal: str                          # variable name we're trying to prove
    rule: ast.RuleDecl | None         # rule used to prove this goal
    subgoals: list[ProofNode]         # child goals needed
    result: bool                       # whether proof succeeded
    bindings: dict[str, Value]         # variable bindings from proof

class BackwardChainer:
    """Goal-driven rule evaluation via backward chaining."""

    def __init__(
        self,
        rules: list[ast.RuleDecl],
        evaluator: Evaluator,
        env: Environment,
        max_depth: int = 50,
    ) -> None:
        self.rules = rules
        self.evaluator = evaluator
        self.env = env
        self.max_depth = max_depth
        self._rule_index: dict[str, list[ast.RuleDecl]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Index rules by the variables they set (their conclusions)."""
        for rule in self.rules:
            if isinstance(rule.action, ast.SetAction):
                target = self._target_name(rule.action.target)
                if target:
                    self._rule_index.setdefault(target, []).append(rule)

    def query(self, goal: str, depth: int = 0) -> ProofNode:
        """Try to prove a goal by backward chaining.

        1. If goal is already in env (fact), succeed immediately
        2. Find rules that conclude this goal
        3. For each such rule, try to prove all its conditions
        4. If all conditions provable, execute the rule and succeed
        """
        # Base case: already known
        existing = self.env.get(goal)
        if existing is not _UNBOUND and existing is not None:
            return ProofNode(goal=goal, rule=None, subgoals=[], result=True,
                             bindings={goal: existing})

        if depth >= self.max_depth:
            return ProofNode(goal=goal, rule=None, subgoals=[], result=False,
                             bindings={})

        # Find rules that set this goal
        candidate_rules = self._rule_index.get(goal, [])
        # Sort by priority
        candidate_rules = sorted(candidate_rules, key=lambda r: r.priority, reverse=True)

        for rule in candidate_rules:
            proof = self._try_rule(rule, goal, depth)
            if proof.result:
                return proof

        # No rule could prove the goal
        return ProofNode(goal=goal, rule=None, subgoals=[], result=False,
                         bindings={})

    def _try_rule(self, rule: ast.RuleDecl, goal: str, depth: int) -> ProofNode:
        """Try to use a specific rule to prove the goal."""
        subgoals: list[ProofNode] = []

        # Check each condition
        conditions = self.evaluator._flatten_conditions(rule.conditions)
        for cond in conditions:
            # Try to evaluate the condition directly
            result, bindings = self.evaluator._eval_condition(cond, self.env)
            if result:
                continue

            # Condition failed — try to prove required variables
            required_vars = self._extract_required_vars(cond)
            proved_any = False
            for var in required_vars:
                if self.env.get(var) is _UNBOUND:
                    sub_proof = self.query(var, depth + 1)
                    subgoals.append(sub_proof)
                    if sub_proof.result:
                        # Update env with proved bindings
                        for k, v in sub_proof.bindings.items():
                            self.env = self.env.set(k, v)
                        proved_any = True

            # Re-evaluate the condition with updated env
            if proved_any:
                result, _ = self.evaluator._eval_condition(cond, self.env)
                if not result:
                    return ProofNode(goal=goal, rule=rule, subgoals=subgoals,
                                     result=False, bindings={})
            else:
                return ProofNode(goal=goal, rule=rule, subgoals=subgoals,
                                 result=False, bindings={})

        # All conditions satisfied — execute the action
        action_result, self.env = self.evaluator._eval_action(rule.action, self.env)
        all_bindings = {goal: action_result}
        for sg in subgoals:
            all_bindings.update(sg.bindings)

        return ProofNode(goal=goal, rule=rule, subgoals=subgoals,
                         result=True, bindings=all_bindings)

    def _extract_required_vars(self, cond: ast.Condition) -> list[str]:
        """Extract variable names referenced in a condition."""
        vars_found: list[str] = []
        self._walk_for_vars(cond, vars_found)
        return vars_found

    def _walk_for_vars(self, node: object, vars_found: list[str]) -> None:
        if isinstance(node, ast.Identifier):
            vars_found.append(node.name)
        if hasattr(node, "__dataclass_fields__"):
            for fname in node.__dataclass_fields__:
                child = getattr(node, fname)
                if isinstance(child, tuple):
                    for item in child:
                        self._walk_for_vars(item, vars_found)
                elif hasattr(child, "__dataclass_fields__"):
                    self._walk_for_vars(child, vars_found)

    @staticmethod
    def _target_name(expr: ast.Expression) -> str | None:
        if isinstance(expr, ast.Identifier):
            return expr.name
        return None
```

**File**: `src/sigil/interpreter/evaluator.py` — add query evaluation

```python
# New statement type or expression:
def _eval_query(self, goal: str, rules: list[ast.RuleDecl], env: Environment) -> tuple[Value, Environment]:
    """Evaluate a backward chaining query."""
    from sigil.interpreter.backward import BackwardChainer
    chainer = BackwardChainer(rules, self, env)
    proof = chainer.query(goal)

    # Record proof tree in trace
    self.trace.add_proof_tree(proof)

    if proof.result:
        # Update env with all proved bindings
        for k, v in proof.bindings.items():
            env = env.set(k, v)
        return proof.bindings.get(goal), env

    return None, env
```

**File**: `src/sigil/ast/nodes.py` — add `QueryStmt`

```python
@dataclass(frozen=True)
class QueryStmt(Statement):
    """Query statement for backward chaining: 'query goal_name with expr'."""
    goal: str
    argument: Expression | None = None
```

**File**: `src/sigil/parser/parser.py` — parse `query` statements

### Step 2: Temporal Rule Foundations

**File**: `src/sigil/ast/nodes.py` — add temporal condition

```python
@dataclass(frozen=True)
class TemporalConstraint(Node):
    """Temporal constraint on a rule: 'within 5 seconds'."""
    duration: Expression
    unit: str  # "seconds", "milliseconds", "minutes"
```

Add to `RuleDecl`:
```python
@dataclass(frozen=True)
class RuleDecl(Declaration):
    # ... existing fields ...
    temporal: TemporalConstraint | None = None
```

**File**: `src/sigil/parser/parser.py` — parse `within` clause

After conditions, before `then`:
```python
# In _parse_rule_decl, after conditions:
temporal = None
if self._match_value("within"):
    duration = self._parse_expression()
    unit = self._expect(TokenType.IDENTIFIER).value  # seconds, milliseconds, minutes
    temporal = ast.TemporalConstraint(location=loc, duration=duration, unit=unit)
```

**File**: `src/sigil/interpreter/evaluator.py` — temporal awareness

For Sprint 3, temporal constraints are stored but evaluated as instant (point-in-time). The interpreter logs a warning if temporal constraints are present:

```python
if rule.temporal:
    self.trace.add_warning(
        f"Temporal constraint 'within {rule.temporal.duration} {rule.temporal.unit}' "
        "is stored but not enforced in Phase 2 (requires event stream in Phase 3)"
    )
```

### Step 3: Standard Library — time module

**File**: `src/sigil/stdlib/_builtins.py` — add time functions

```python
import time as _time

def stdlib_now(_args, _trace):
    """Current time as Unix timestamp (seconds)."""
    return _time.time()

def stdlib_now_ms(_args, _trace):
    """Current time as Unix timestamp (milliseconds)."""
    return _time.time() * 1000

def stdlib_duration_seconds(args, _trace):
    """Create a duration value in seconds."""
    return args[0]

def stdlib_format_timestamp(args, _trace):
    """Format a Unix timestamp as ISO 8601 string."""
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(args[0], tz=timezone.utc)
    return dt.isoformat()

def stdlib_elapsed(args, _trace):
    """Calculate elapsed seconds between two timestamps."""
    return args[1] - args[0]

STDLIB_TIME = {
    "now": stdlib_now,
    "now_ms": stdlib_now_ms,
    "duration_seconds": stdlib_duration_seconds,
    "format_timestamp": stdlib_format_timestamp,
    "elapsed": stdlib_elapsed,
}
```

### Step 4: Standard Library — trace module

**File**: `src/sigil/stdlib/_builtins.py` — add trace functions

```python
import json

def stdlib_trace_to_json(args, trace):
    """Export the current program trace as a JSON string."""
    data = {
        "rules": [
            {
                "name": rt.rule_name,
                "priority": rt.priority,
                "fired": rt.fired,
                "conditions": [
                    {"description": ct.description, "result": ct.result}
                    for ct in rt.conditions
                ],
                "explain": rt.explain,
                "duration_ms": rt.duration_ms,
            }
            for rt in trace.rule_traces
        ],
        "total_duration_ms": trace.total_duration_ms,
    }
    return json.dumps(data, indent=2)

def stdlib_trace_fired_rules(_args, trace):
    """Get list of rule names that fired."""
    return [rt.rule_name for rt in trace.rule_traces if rt.fired]

def stdlib_trace_rule_count(_args, trace):
    """Get total number of rules evaluated."""
    return len(trace.rule_traces)

def stdlib_trace_duration_ms(_args, trace):
    """Get total execution duration in milliseconds."""
    return trace.total_duration_ms

STDLIB_TRACE = {
    "to_json": stdlib_trace_to_json,
    "fired_rules": stdlib_trace_fired_rules,
    "rule_count": stdlib_trace_rule_count,
    "duration_ms": stdlib_trace_duration_ms,
}
```

### Step 5: Standard Library — io module

**File**: `src/sigil/stdlib/_builtins.py` — add io functions

```python
def stdlib_read_file(args, _trace):
    """Read a text file and return its contents."""
    path = args[0]
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        raise SigilRuntimeError(f"File not found: {path}")
    except PermissionError:
        raise SigilRuntimeError(f"Permission denied: {path}")

def stdlib_write_file(args, _trace):
    """Write text to a file."""
    path, content = args[0], args[1]
    Path(path).write_text(content)
    return None

def stdlib_file_exists(args, _trace):
    """Check if a file exists."""
    return Path(args[0]).exists()

def stdlib_parse_json(args, _trace):
    """Parse a JSON string into Sigil values."""
    data = json.loads(args[0])
    return _json_to_value(data)

def stdlib_to_json(args, _trace):
    """Convert a Sigil value to a JSON string."""
    return json.dumps(_value_to_json(args[0]), indent=2)

STDLIB_IO = {
    "read_file": stdlib_read_file,
    "write_file": stdlib_write_file,
    "file_exists": stdlib_file_exists,
    "parse_json": stdlib_parse_json,
    "to_json": stdlib_to_json,
}
```

### Step 6: Enhanced Type Checker

**File**: `src/sigil/types/checker.py` — extend

**Check #9: Return type consistency**

```python
def _check_return_type(self, compute: ast.ComputeDecl, scope: set[str]) -> None:
    """Check that all return paths match the declared return type."""
    if not compute.return_type:
        return

    declared = self._type_name(compute.return_type)
    returns = self._collect_returns(compute.body)

    for ret in returns:
        if isinstance(ret.value, ast.Literal):
            actual = self._infer_literal_type(ret.value)
            if actual and declared and actual != declared:
                self._warning(
                    ret.location,
                    f"Return type mismatch: declared '{declared}' but returning '{actual}'",
                )
```

**Check #10: Gradual type inference on given statements**

```python
def _infer_given_type(self, stmt: ast.GivenStmt, scope: dict[str, str]) -> str | None:
    """Infer the type of a given statement's value."""
    if isinstance(stmt.value, ast.Literal):
        return self._infer_literal_type(stmt.value)
    if isinstance(stmt.value, ast.FuncCall):
        func_name = self._resolve_func_name(stmt.value.function)
        if func_name in self._compute_return_types:
            return self._compute_return_types[func_name]
    return None
```

**Check #11: Unit type awareness (warning-level)**

```python
def _check_unit_mismatch(self, left: ast.Expression, right: ast.Expression) -> None:
    """Warn if comparing values with different unit suffixes."""
    left_unit = self._get_unit_suffix(left)
    right_unit = self._get_unit_suffix(right)
    if left_unit and right_unit and left_unit != right_unit:
        self._warning(
            left.location,
            f"Unit mismatch: comparing '{left_unit}' with '{right_unit}'",
        )
```

### Step 7: Performance Benchmarks

**File**: `benchmarks/bench_lexer.py` (NEW)

```python
"""Benchmark lexer performance."""
import time
from sigil.lexer import tokenize

def bench_lex_file(path: str, iterations: int = 100) -> dict:
    source = open(path).read()
    start = time.perf_counter_ns()
    for _ in range(iterations):
        tokenize(source, path)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

    lines = source.count("\n") + 1
    return {
        "file": path,
        "lines": lines,
        "iterations": iterations,
        "total_ms": elapsed_ms,
        "per_iteration_ms": elapsed_ms / iterations,
        "lines_per_second": lines * iterations / (elapsed_ms / 1000),
    }
```

**File**: `benchmarks/bench_evaluator.py` (NEW)

```python
"""Benchmark interpreter performance."""
def bench_run_file(path: str, input_data=None, iterations: int = 100) -> dict:
    # Lex + parse once
    source = open(path).read()
    tokens = tokenize(source, path)
    program = parse(tokens, path)

    start = time.perf_counter_ns()
    for _ in range(iterations):
        evaluate(program, input_data)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

    return {
        "file": path,
        "iterations": iterations,
        "total_ms": elapsed_ms,
        "per_iteration_ms": elapsed_ms / iterations,
    }
```

**File**: `benchmarks/run_benchmarks.py` — runner script

Target performance (from ARCHITECTURE.md):
- Lexing + parsing: <10ms for 1000 lines
- Type checking: <50ms for 1000 lines
- Rule evaluation (symbolic): <1ms per decision
- Trace generation: <0.1ms overhead per rule

### Step 8: Backward Chaining Example

**File**: `examples/rules/backward_chaining.sigil`

```sigil
-- Backward chaining example
-- Goal: prove "can_fly" for different objects

define birds as ["eagle", "sparrow", "penguin"]
define penguins as ["penguin"]

rule is_bird with priority 10:
  when animal in birds
  then is_bird is true

rule is_penguin with priority 20:
  when animal in penguins
  then is_penguin is true

rule can_fly with priority 5:
  when is_bird is true
  and not is_penguin is true
  then can_fly is true
  explain "Birds can fly unless they are penguins"

main:
  given animal as "eagle"
  -- Forward chaining: evaluate all rules
  evaluate all rules with animal

  -- Backward chaining: try to prove can_fly
  query can_fly
  print(can_fly)
```

### Step 9: Comprehensive Example Programs

Ensure 10+ total new examples across Phase 2:

```
examples/features/pattern_matching.sigil       (Sprint 1)
examples/features/pipeline.sigil               (Sprint 1)
examples/features/higher_order.sigil           (Sprint 1)
examples/features/data_processing.sigil        (Sprint 1)
examples/features/match_rules.sigil            (Sprint 1)
examples/features/functional_pipeline.sigil    (Sprint 1)
examples/modules/math_utils.sigil              (Sprint 2)
examples/modules/scoring.sigil                 (Sprint 2)
examples/modules/main_scoring.sigil            (Sprint 2)
examples/rules/backward_chaining.sigil         (Sprint 3)
examples/advanced/temporal_monitor.sigil       (Sprint 3)
examples/advanced/proof_tree.sigil             (Sprint 3)
```

### Step 10: Tests

**Test files:**

```
tests/interpreter/test_backward.py    — 20+ tests for backward chaining
tests/interpreter/test_temporal.py    — 5+ tests for temporal constraint parsing
tests/stdlib/test_time.py             — 5+ tests for time stdlib
tests/stdlib/test_trace.py            — 5+ tests for trace stdlib
tests/stdlib/test_io.py               — 5+ tests for io stdlib
tests/typechecker/test_inference.py   — 15+ tests for enhanced type inference
tests/integration/test_backward_examples.py — 5+ integration tests
benchmarks/bench_lexer.py             — lexer benchmarks
benchmarks/bench_evaluator.py         — evaluator benchmarks
```

Target: **80+ new tests** → 600+ total (meets ROADMAP target)

### Step 11: Documentation Updates

- Update `ai_docs/STATUS.md` — mark Phase 2 complete
- Update `docs/ROADMAP.md` — check off Phase 2 milestones
- Write Phase 2 retrospective
- Update `CLAUDE.md` project structure with new directories
- Update `docs/spec/GRAMMAR.peg` with query, within, export, lambda syntax

---

## Files to Create/Modify

### New files (15+)
```
src/sigil/interpreter/backward.py          — Backward chaining engine
src/sigil/modules/__init__.py              — (if not from Sprint 2)
tests/interpreter/test_backward.py
tests/interpreter/test_temporal.py
tests/stdlib/test_time.py
tests/stdlib/test_trace.py
tests/stdlib/test_io.py
tests/typechecker/test_inference.py
tests/integration/test_backward_examples.py
benchmarks/__init__.py
benchmarks/bench_lexer.py
benchmarks/bench_evaluator.py
benchmarks/run_benchmarks.py
examples/rules/backward_chaining.sigil
examples/advanced/temporal_monitor.sigil
examples/advanced/proof_tree.sigil
```

### Modified files (6)
```
src/sigil/ast/nodes.py               — QueryStmt, TemporalConstraint
src/sigil/parser/parser.py           — query, within parsing
src/sigil/interpreter/evaluator.py   — query evaluation, temporal awareness
src/sigil/types/checker.py           — 3 new checks (return type, inference, units)
src/sigil/stdlib/_builtins.py        — time, trace, io modules
src/sigil/stdlib/__init__.py         — register new modules
```

---

## Implementation Order

### Phase A: Backward Chaining (Steps 1, 8)

1. Backward chaining engine
2. Query parsing and evaluation
3. Backward chaining example

**PAUSE — test backward chaining with simple rules**

### Phase B: Temporal + Stdlib + Types (Steps 2–6)

4. Temporal constraint parsing (stored, not enforced)
5. Time, trace, io stdlib modules
6. Enhanced type checker (3 new checks)

**PAUSE — test stdlib in REPL, verify type checker on all examples**

### Phase C: Benchmarks + Polish + Docs (Steps 7, 9–11)

7. Performance benchmarks
8. All remaining example programs
9. Full test suite (80+ new tests)
10. Documentation updates
11. Phase 2 retrospective

**DONE — Phase 2 complete**

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Backward chaining infinite recursion | Medium | High | Max depth limit (50), cycle detection on goals |
| Backward chaining interacts poorly with forward chaining | Medium | Medium | Keep them separate: forward = evaluate, backward = query |
| Temporal rules need event streams (Phase 3) | Expected | Low | Sprint 3 only adds parsing + stub evaluation |
| Type inference is a rabbit hole | High | Medium | Keep inference simple: literals and function returns only |
| Performance benchmarks reveal bottlenecks | Medium | Low | Document but defer optimization to Phase 3 |
| 600 test target is ambitious | Low | Low | Already at 520+, need 80 more |
| IO stdlib security concerns | Medium | Medium | File I/O only, no network, sandboxing docs |

---

## Definition of Done (Sprint 3 / Phase 2)

```bash
# All of these must work:
sigil run examples/rules/backward_chaining.sigil        # backward chaining works
sigil run examples/advanced/temporal_monitor.sigil       # temporal parsing works
sigil run examples/modules/main_scoring.sigil            # modules still work
sigil run examples/features/pipeline.sigil               # Sprint 1 still works
sigil run examples/basics/hello.sigil                    # Phase 1 still works
sigil run examples/rules/loan_eligibility.sigil --input '{...}'  # Phase 1 still works
sigil check examples/rules/backward_chaining.sigil       # type check passes
sigil repl                                                # all features work
pytest tests/ -v                                          # 600+ tests, all passing
ruff check src/ tests/                                    # clean
mypy src/sigil/ --ignore-missing-imports                  # clean
python benchmarks/run_benchmarks.py                       # benchmarks recorded
```

---

## Phase 2 Summary

| Sprint | Focus | New Tests | Total | Key Deliverables |
|--------|-------|-----------|-------|-----------------|
| Sprint 1 | Language Features | 80+ | 450+ | Match, Pipeline, Closures |
| Sprint 2 | Infrastructure | 70+ | 520+ | Modules, Stdlib (math/text/list/logic) |
| Sprint 3 | Advanced + Polish | 80+ | 600+ | Backward chaining, Temporal, Stdlib (time/trace/io), Benchmarks |

After Phase 2, Sigil has:
- Full expression language (match, pipeline, closures, higher-order functions)
- Module system with import/export and circular dependency detection
- 7 standard library modules (math, text, list, logic, time, trace, io)
- Forward AND backward chaining rule evaluation
- Temporal rule foundations
- 11 type checker checks
- 600+ tests
- Performance benchmarks
- 15+ example programs

**Next**: Phase 3 — Python FFI (real), Neural Bridge (real models), Rust Core (performance)
