# Sigil — Phase 2 Sprint 1: Pattern Matching, Pipeline, Closures

## Where We Are

**Phase 1 is COMPLETE.**

Done:
- Lexer: 91 tests, all 5 examples tokenize
- Parser: 75 tests, all 5 examples parse into ASTs
- Interpreter: 137 tests, tree-walking evaluator (~930 lines), all 5 examples execute correctly
- Type Checker: 39 tests, 5 static checks
- REPL: 31 tests, interactive shell with persistent state
- CLI: `sigil lex`, `sigil parse-ast`, `sigil check`, `sigil run`, `sigil repl` all working
- Grammar: GRAMMAR.peg v0.2 — all 8 implementation gaps documented
- Tooling: ruff clean, mypy clean (0 errors across 21 files)
- Total: **373 tests passing**

What Phase 2 must deliver (from ROADMAP.md):
- Pattern matching in expressions
- Pipeline operator (`|>`) — end to end
- Closures and higher-order functions
- Module system with import/export
- Advanced rules (backward chaining, temporal)
- Standard library (math, text, logic, time, trace, io, types)
- 400+ tests

---

## Sprint 1 Goal

> **Deliver match expression evaluation, full pipeline operator support (parser → evaluator), closures / higher-order functions, and enhanced type checking. Write 6+ new examples that exercise these features.**

### Sprint 1 Exit Criteria
- [ ] Match expressions evaluate correctly with literal, symbol, identifier, and wildcard patterns
- [ ] Pipeline operator `|>` works end-to-end: parser produces `PipelineExpr`, evaluator handles `filter where`, `sort by`, `take first/last`, `map to`
- [ ] Functions are first-class values: can be passed as arguments, returned from compute blocks, stored in variables
- [ ] Lambda/anonymous functions: `compute from x: Number returns Number: return x + 1` inline
- [ ] Type checker extended: match exhaustiveness warnings, return type consistency, pipeline type checking
- [ ] 6+ new example programs demonstrating new features
- [ ] 80+ new tests → 450+ total
- [ ] All existing 373 tests still pass (no regressions)

---

## What Must Be Built

### By Feature (from simplest to most complex)

**Match Expressions** — Evaluate pattern matching:
- Parser already produces `MatchExpr` AST nodes
- Evaluator has NO handler for `MatchExpr` — need to add
- Patterns: literal values, symbols, identifiers (bind), wildcard `_`
- Must produce trace entries for which arm matched

**Pipeline Operator** — Full implementation:
- Lexer already tokenizes `|>` as `TokenType.PIPE`
- AST nodes exist: `PipelineExpr`, `PipeOp`
- Parser does NOT produce pipeline nodes — `_parse_expression()` skips pipeline level
- Evaluator has NO handler for `PipelineExpr`
- Need: parser fix + 5 pipeline operations + evaluator

**Closures & Higher-Order Functions** — Functions as values:
- Currently: compute functions are called by name lookup in `_compute_funcs` dict
- Need: functions as first-class `Value`, captured environments, function call on value
- Need: anonymous functions (lambda compute blocks)
- Need: pass functions to other functions, return functions

**Enhanced Type Checker** — Deeper analysis:
- Currently: 5 checks (undefined var, undefined field, type mismatch, arity, duplicates)
- Need: match exhaustiveness (warn if no wildcard and not all cases covered)
- Need: return type consistency (declared vs actual)
- Need: pipeline source/operation type compatibility

---

## Step-by-Step Implementation Plan

### Step 1: Match Expression Evaluation

**File**: `src/sigil/interpreter/evaluator.py` — add to `eval_expression()`

The parser already handles match expressions. The AST node:

```python
# From nodes.py (already exists)
@dataclass(frozen=True)
class MatchExpr(Expression):
    subject: Expression
    arms: tuple[MatchArm, ...]

@dataclass(frozen=True)
class MatchArm(Node):
    pattern: Expression  # Literal, SymbolLit, Identifier, or Identifier("_") for wildcard
    body: Expression
```

Evaluation rules:

```
eval_expr(MatchExpr):
  1. Evaluate subject expression → subject_val
  2. For each arm in arms:
     a. If pattern is Literal: compare values_equal(subject_val, pattern.value)
     b. If pattern is SymbolLit: compare subject_val == Symbol(pattern.name)
     c. If pattern is Identifier("_"): always matches (wildcard)
     d. If pattern is Identifier(name): always matches, bind name=subject_val in body env
     e. If match found: evaluate body expression in (possibly extended) env, return result
  3. If no match: raise SigilRuntimeError("No matching pattern")
```

Example that exercises this:

```sigil
compute classify_score from score: Number returns Symbol:
  return match score:
    100 -> :perfect
    _ -> :normal
```

Simpler example using symbols:

```sigil
compute get_label from level: Symbol returns Text:
  return match level:
    :high -> "High Priority"
    :medium -> "Medium Priority"
    :low -> "Low Priority"
    _ -> "Unknown"
```

**Tests** (15+):
- Match literal integer
- Match literal string
- Match symbol
- Match wildcard `_`
- Match identifier binding (captures value)
- Match first-wins (multiple matching patterns)
- Match no-match error
- Match in compute function return
- Match nested expressions as body
- Integration: match with rule conditions

### Step 2: Pipeline Operator — Parser Fix

**File**: `src/sigil/parser/parser.py`

Currently the expression precedence chain is:

```
_parse_expression() → _parse_additive() → _parse_multiplicative() → _parse_unary() → _parse_postfix() → _parse_primary()
```

Pipeline should be the LOWEST precedence (below additive), matching the grammar:

```
Expression      <- PipelineExpr
PipelineExpr    <- LogicalExpr (Spacing '|>' Spacing PipeOp)*
```

But we don't have a `_parse_logical()` level either. The parser structure needs:

```
_parse_expression()
  → _parse_pipeline()     # NEW: handles |>
    → _parse_additive()   # existing: handles + -
      → _parse_multiplicative()
        → _parse_unary()
          → _parse_postfix()
            → _parse_primary()
```

Implementation:

```python
def _parse_expression(self) -> ast.Expression:
    return self._parse_pipeline()

def _parse_pipeline(self) -> ast.Expression:
    """Parse pipeline expressions: expr |> op |> op ..."""
    expr = self._parse_additive()

    if not self._check(TokenType.PIPE):
        return expr

    ops: list[ast.PipeOp] = []
    while self._match(TokenType.PIPE):
        op = self._parse_pipe_op()
        ops.append(op)

    return ast.PipelineExpr(
        location=expr.location,
        source=expr,
        operations=tuple(ops),
    )

def _parse_pipe_op(self) -> ast.PipeOp:
    """Parse a single pipeline operation after |>."""
    loc = self._loc()

    if self._match_value("filter"):
        self._expect_value("where")
        condition = self._parse_condition()
        return ast.PipeOp(location=loc, kind="filter", condition=condition)

    if self._match_value("sort"):
        self._expect_value("by")
        field = self._expect(TokenType.IDENTIFIER).value
        direction = "ascending"
        if self._match_value("ascending"):
            direction = "ascending"
        elif self._match_value("descending"):
            direction = "descending"
        return ast.PipeOp(location=loc, kind="sort", args=(field,), direction=direction)

    if self._match_value("take"):
        if self._match_value("first"):
            count = self._parse_expression()
            return ast.PipeOp(location=loc, kind="take_first", args=(count,))
        elif self._match_value("last"):
            count = self._parse_expression()
            return ast.PipeOp(location=loc, kind="take_last", args=(count,))

    if self._match_value("map"):
        self._expect_value("to")
        expr = self._parse_expression()
        return ast.PipeOp(location=loc, kind="map", args=(expr,))

    # Generic identifier pipe op (for future extensions)
    name = self._expect(TokenType.IDENTIFIER).value
    return ast.PipeOp(location=loc, kind=name)
```

Note: Need `_match_value()` and `_expect_value()` helpers if they don't exist.

**Tests** (10+):
- Parse `items |> filter where x exceeds 10`
- Parse `items |> sort by name ascending`
- Parse `items |> take first 5`
- Parse `items |> map to x + 1`
- Parse chained: `items |> filter where ... |> sort by ... |> take first 3`
- Parse error: `|>` without source
- Parse error: unknown pipe operation

### Step 3: Pipeline Operator — Evaluator

**File**: `src/sigil/interpreter/evaluator.py` — add to `eval_expression()`

```python
def _eval_pipeline(self, expr: ast.PipelineExpr, env: Environment) -> Value:
    """Evaluate a pipeline expression."""
    # Evaluate source — must produce a list
    source = self.eval_expression(expr.source, env)
    if not isinstance(source, list):
        msg = f"Pipeline source must be a list, got {type(source).__name__}"
        raise SigilRuntimeError(msg)

    result = source
    for op in expr.operations:
        result = self._eval_pipe_op(op, result, env)
    return result

def _eval_pipe_op(self, op: ast.PipeOp, items: list, env: Environment) -> Value:
    """Evaluate a single pipeline operation."""
    if op.kind == "filter":
        # Filter: keep items where condition is true
        filtered = []
        for item in items:
            # Bind the item as the implicit variable
            # For "filter where x exceeds 10", x must be resolvable
            # If item is Record, spread fields into env; otherwise bind as "it"
            item_env = self._pipeline_item_env(item, env)
            result, _ = self._eval_condition(op.condition, item_env)
            if result:
                filtered.append(item)
        return filtered

    if op.kind == "sort":
        field_name = op.args[0] if op.args else None
        reverse = (op.direction == "descending")
        if field_name and isinstance(field_name, str):
            # Sort by field on records
            return sorted(items, key=lambda r: r.fields.get(field_name, 0)
                          if isinstance(r, Record) else r, reverse=reverse)
        return sorted(items, reverse=reverse)

    if op.kind == "take_first":
        count = self.eval_expression(op.args[0], env) if op.args else 1
        return items[:int(count)]

    if op.kind == "take_last":
        count = self.eval_expression(op.args[0], env) if op.args else 1
        return items[-int(count):]

    if op.kind == "map":
        mapped = []
        for item in items:
            item_env = self._pipeline_item_env(item, env)
            val = self.eval_expression(op.args[0], item_env)
            mapped.append(val)
        return mapped

    msg = f"Unknown pipeline operation: {op.kind}"
    raise SigilRuntimeError(msg)

def _pipeline_item_env(self, item: Value, env: Environment) -> Environment:
    """Create environment for a pipeline item."""
    if isinstance(item, Record):
        # Spread record fields into env
        bindings = dict(item.fields)
        bindings["it"] = item
        return env.extend(bindings)
    return env.set("it", item)
```

Example that exercises pipelines:

```sigil
define scores as [85, 92, 78, 95, 88, 73, 91]

main:
  given high_scores as scores |> filter where it exceeds 80
  given top_3 as high_scores |> sort by it descending |> take first 3
  print(top_3)
```

Pipeline with records:

```sigil
type Student is record:
  name: Text
  grade: Number

main:
  given students as [
    {name: "Alice", grade: 95},
    {name: "Bob", grade: 82},
    {name: "Charlie", grade: 88}
  ]
  given honor_roll as students
    |> filter where grade exceeds 85
    |> sort by grade descending
  print(honor_roll)
```

**Tests** (15+):
- Filter list of numbers
- Filter list of records
- Sort ascending/descending
- Sort by field on records
- Take first N
- Take last N
- Map to expression
- Chained pipeline (filter → sort → take)
- Pipeline on empty list
- Pipeline error: non-list source
- Integration: pipeline in compute block
- Integration: pipeline in main block

### Step 4: Closures and Higher-Order Functions

**File**: `src/sigil/interpreter/values.py` — add `Closure` value type

Functions must become first-class values. Currently they're just looked up by name in `_compute_funcs`. We need:

```python
@dataclass(frozen=True)
class Closure:
    """A function value with captured environment."""
    params: tuple[str, ...]           # parameter names
    body: tuple[Statement, ...]       # function body (statements)
    env: Environment                  # captured environment at definition time
    name: str | None = None           # named compute or anonymous

# Update Value union:
Value = int | float | str | bool | None | Symbol | Record | Variant | list[Any] | Closure
```

**File**: `src/sigil/interpreter/evaluator.py` — changes:

1. When registering compute functions, also create `Closure` values in the environment:

```python
# In eval_program, after registering compute funcs:
for name, decl in self._compute_funcs.items():
    closure = Closure(
        params=tuple(p.name for p in decl.params),
        body=decl.body,
        env=env,
        name=name,
    )
    env = env.set(name, closure)
```

2. When calling a function, check if the value is a `Closure`:

```python
def _eval_func_call(self, expr: ast.FuncCall, env: Environment) -> Value:
    args = [self.eval_expression(a, env) for a in expr.args]

    # Try resolving by name first (for backward compat)
    func_name = self._resolve_func_name(expr.function, env)

    # Check compute functions
    if func_name in self._compute_funcs:
        return self._call_compute(func_name, args, env)

    # Check neural stubs
    if func_name in self._neural_funcs:
        return self._call_neural_stub(func_name)

    # Check builtins
    if func_name in BUILTINS:
        return BUILTINS[func_name](args, self.trace)
    if func_name in DOTTED_BUILTINS:
        return DOTTED_BUILTINS[func_name](args, self.trace)

    # Check if it's a Closure value
    func_val = self.eval_expression(expr.function, env)
    if isinstance(func_val, Closure):
        return self._call_closure(func_val, args)

    msg = f"Undefined function: {func_name}"
    raise SigilRuntimeError(msg)

def _call_closure(self, closure: Closure, args: list[Value]) -> Value:
    """Call a closure with arguments."""
    if len(args) != len(closure.params):
        name = closure.name or "<anonymous>"
        msg = f"{name} expects {len(closure.params)} args, got {len(args)}"
        raise SigilRuntimeError(msg)

    # Bind params in the closure's captured environment
    bindings = dict(zip(closure.params, args, strict=True))
    func_env = closure.env.extend(bindings)

    try:
        for stmt in closure.body:
            _, func_env = self._eval_statement(stmt, [], func_env)
    except ReturnSignal as ret:
        return ret.value

    return None
```

3. Support compute functions as expressions (identifiers that resolve to closures):

When evaluating an `Identifier` that matches a compute function name, return its `Closure` value. This lets functions be passed as arguments:

```sigil
compute apply from f, x: Number returns Number:
  return f(x)

compute double from x: Number returns Number:
  return x * 2

main:
  given result as apply(double, 5)
  print(result)  -- prints 10
```

**File**: `src/sigil/parser/parser.py` — anonymous functions

Support inline anonymous compute blocks as expressions. Syntax:

```sigil
given doubler as compute from x: Number returns Number: return x * 2
```

This requires parsing `compute from ...` as an expression when it appears after `as`:

```python
# In _parse_primary() or _parse_expression():
if self._check(TokenType.COMPUTE) and not self._is_top_level():
    return self._parse_lambda_expr()

def _parse_lambda_expr(self) -> ast.LambdaExpr:
    """Parse an inline anonymous compute expression."""
    loc = self._loc()
    self._expect(TokenType.COMPUTE)

    params: list[ast.Param] = []
    if self._match(TokenType.FROM):
        params = self._parse_param_list()

    return_type = None
    if self._match(TokenType.RETURNS):
        return_type = self._parse_type_ref()

    self._expect(TokenType.COLON)
    # Single expression body (inline)
    body_expr = self._parse_expression()
    body_stmt = ast.ReturnStmt(location=loc, value=body_expr)

    return ast.LambdaExpr(
        location=loc,
        params=tuple(params),
        return_type=return_type,
        body=(body_stmt,),
    )
```

**File**: `src/sigil/ast/nodes.py` — add `LambdaExpr`:

```python
@dataclass(frozen=True)
class LambdaExpr(Expression):
    """Inline anonymous compute expression."""
    params: tuple[Param, ...]
    return_type: TypeRef | None
    body: tuple[Statement, ...]
```

**Tests** (20+):
- Closure creation from compute block
- Closure call with correct args
- Closure call with wrong arity → error
- Closure captures environment (free variables)
- Pass function as argument (higher-order)
- Return function from compute block
- Lambda expression: `compute from x: return x + 1`
- Lambda in given statement
- Lambda passed to higher-order function
- Nested closures
- Recursive compute function
- Integration: closure with pipeline (map to function)
- Integration: closure in rule action

### Step 5: PipeOp AST Node Cleanup

**File**: `src/sigil/ast/nodes.py` — verify/update PipeOp node

Current PipeOp node:

```python
@dataclass(frozen=True)
class PipeOp(Node):
    kind: str
    args: tuple[Expression, ...] = ()
    condition: Condition | None = None
    direction: str | None = None  # for sort
```

This is adequate. Ensure `args` can hold field names as `Literal` or `Identifier` for sort-by.

### Step 6: Enhanced Type Checker

**File**: `src/sigil/types/checker.py` — extend with new checks

Add 3 new checks (8 total):

**Check #6: Match exhaustiveness warning**

```python
def _check_match_exhaustiveness(self, expr: ast.MatchExpr) -> None:
    """Warn if match expression might not be exhaustive."""
    has_wildcard = any(
        isinstance(arm.pattern, ast.Identifier) and arm.pattern.name == "_"
        for arm in expr.arms
    )
    if not has_wildcard:
        self._warning(
            expr.location,
            "Match expression may not be exhaustive — consider adding a wildcard '_' arm",
        )
```

**Check #7: Pipeline source type (best effort)**

```python
def _check_pipeline(self, expr: ast.PipelineExpr, scope: set[str]) -> None:
    """Check pipeline source is potentially a list."""
    self._check_expr(expr.source, scope)
    # Check source is a list literal or known list variable
    if isinstance(expr.source, ast.Literal) and not isinstance(expr.source.value, list):
        self._error(
            expr.source.location,
            "Pipeline source must be a list",
        )
    # Check conditions/expressions in pipe ops
    for op in expr.operations:
        if op.condition:
            self._check_condition(op.condition, scope | {"it"})
        for arg in op.args:
            if isinstance(arg, ast.Expression):
                self._check_expr(arg, scope | {"it"})
```

**Check #8: Closure arity when passed to known functions**

When a closure is passed as an argument to a compute function, check that the arities align if statically determinable.

**Tests** (10+):
- Match without wildcard → warning
- Match with wildcard → no warning
- Pipeline on non-list literal → error
- Pipeline conditions scoped (access to `it`)
- Closure arity mismatch (static check)
- Lambda type check (body expression)
- PipelineExpr in type checker
- MatchExpr in type checker

### Step 7: New Example Programs

Create 6+ new example programs that exercise Sprint 1 features:

**File**: `examples/features/pattern_matching.sigil`

```sigil
-- Pattern matching example
-- Demonstrates: match expressions, symbol matching, wildcard

type Severity is one of:
  critical
  high
  medium
  low

compute severity_label from level: Symbol returns Text:
  return match level:
    :critical -> "CRITICAL - Immediate action required"
    :high -> "HIGH - Action required within 1 hour"
    :medium -> "MEDIUM - Action required within 24 hours"
    :low -> "LOW - No immediate action"
    _ -> "UNKNOWN - Unrecognized severity"

compute priority_score from level: Symbol returns Number:
  return match level:
    :critical -> 100
    :high -> 75
    :medium -> 50
    :low -> 25
    _ -> 0

main:
  given level as :high
  given label as severity_label(level)
  given score as priority_score(level)
  print(label)
  print(score)
```

**File**: `examples/features/pipeline.sigil`

```sigil
-- Pipeline operator example
-- Demonstrates: |> filter, sort, take, map, chaining

type Transaction is record:
  id: Text
  amount: Number
  category: Symbol
  flagged: Boolean

define transactions as [
  {id: "T001", amount: 150, category: :purchase, flagged: false},
  {id: "T002", amount: 5000, category: :transfer, flagged: true},
  {id: "T003", amount: 75, category: :purchase, flagged: false},
  {id: "T004", amount: 12000, category: :transfer, flagged: true},
  {id: "T005", amount: 200, category: :purchase, flagged: false},
  {id: "T006", amount: 8500, category: :wire, flagged: true}
]

main:
  -- Find the top 3 highest flagged transactions
  given flagged_high as transactions
    |> filter where flagged is true
    |> sort by amount descending
    |> take first 3

  print(flagged_high)

  -- Get all purchase amounts
  given purchase_amounts as transactions
    |> filter where category is :purchase
    |> map to amount

  print(purchase_amounts)
```

**File**: `examples/features/higher_order.sigil`

```sigil
-- Higher-order functions example
-- Demonstrates: functions as values, passing functions, closures

compute apply from f, x: Number returns Number:
  return f(x)

compute compose from f, g, x: Number returns Number:
  return f(g(x))

compute double from x: Number returns Number:
  return x * 2

compute increment from x: Number returns Number:
  return x + 1

compute square from x: Number returns Number:
  return x * x

main:
  given a as apply(double, 5)
  print(a)   -- 10

  given b as apply(increment, 5)
  print(b)   -- 6

  given c as compose(double, increment, 5)
  print(c)   -- 12 (double(increment(5)) = double(6) = 12)

  given d as compose(increment, double, 5)
  print(d)   -- 11 (increment(double(5)) = increment(10) = 11)
```

**File**: `examples/features/data_processing.sigil`

```sigil
-- Data processing with pipelines and pattern matching
-- Demonstrates: combining pipeline, match, compute, rules

type Employee is record:
  name: Text
  department: Symbol
  salary: Number
  years: Number

define employees as [
  {name: "Alice", department: :engineering, salary: 120000, years: 8},
  {name: "Bob", department: :marketing, salary: 85000, years: 3},
  {name: "Charlie", department: :engineering, salary: 105000, years: 5},
  {name: "Diana", department: :sales, salary: 92000, years: 7},
  {name: "Eve", department: :engineering, salary: 135000, years: 12},
  {name: "Frank", department: :marketing, salary: 78000, years: 2}
]

compute bonus_rate from dept: Symbol returns Number:
  return match dept:
    :engineering -> 15
    :sales -> 12
    :marketing -> 10
    _ -> 8

main:
  -- Senior engineers (5+ years, engineering dept)
  given senior_engineers as employees
    |> filter where department is :engineering
    |> filter where years exceeds 4
    |> sort by salary descending

  print(senior_engineers)

  -- All engineering salaries
  given eng_salaries as employees
    |> filter where department is :engineering
    |> map to salary

  print(eng_salaries)
```

Additional examples:
- `examples/features/match_rules.sigil` — match expressions inside rule conditions and actions
- `examples/features/functional_pipeline.sigil` — combining closures with pipeline map operations

### Step 8: Tests

**Test files to create/modify:**

```
tests/interpreter/test_match.py          — 15+ tests for match expression evaluation
tests/parser/test_pipeline.py            — 10+ tests for pipeline parsing
tests/interpreter/test_pipeline.py       — 15+ tests for pipeline evaluation
tests/interpreter/test_closures.py       — 20+ tests for closures and higher-order functions
tests/typechecker/test_checker_phase2.py — 10+ tests for new type checks
tests/integration/test_phase2_examples.py — 6+ integration tests for new examples
```

Target: **80+ new tests** → 450+ total

### Step 9: REPL Updates

**File**: `src/sigil/interpreter/repl.py`

Ensure REPL handles new features:
- Match expressions in interactive mode
- Pipeline expressions evaluate correctly
- Closure definitions persist across REPL inputs
- New `:closures` command to list defined closures

### Step 10: Documentation Updates

- Update `ai_docs/STATUS.md` — add Phase 2 Sprint 1 items
- Update `docs/spec/GRAMMAR.peg` — if any grammar changes needed for lambda syntax
- This PRP serves as the sprint plan

---

## Files to Create/Modify

### New files (8+)
```
src/sigil/ast/nodes.py                       — Add LambdaExpr node
tests/interpreter/test_match.py              — Match expression tests
tests/parser/test_pipeline.py                — Pipeline parsing tests
tests/interpreter/test_pipeline.py           — Pipeline evaluation tests
tests/interpreter/test_closures.py           — Closure/higher-order tests
tests/typechecker/test_checker_phase2.py     — Enhanced type checker tests
tests/integration/test_phase2_examples.py    — New example integration tests
examples/features/pattern_matching.sigil     — Match expression example
examples/features/pipeline.sigil             — Pipeline operator example
examples/features/higher_order.sigil         — Higher-order functions example
examples/features/data_processing.sigil      — Combined features example
examples/features/match_rules.sigil          — Match in rules example
examples/features/functional_pipeline.sigil  — Closures + pipeline example
```

### Modified files (6)
```
src/sigil/ast/nodes.py                 — Add LambdaExpr
src/sigil/parser/parser.py             — Pipeline parsing, lambda parsing
src/sigil/interpreter/evaluator.py     — Match eval, pipeline eval, closure eval
src/sigil/interpreter/values.py        — Add Closure value type
src/sigil/types/checker.py             — 3 new checks (match, pipeline, closure)
src/sigil/interpreter/repl.py          — Handle new expression types
```

---

## Implementation Order (3 phases, with pause points)

### Phase A: Match + Pipeline (Steps 1–3)

1. Match expression evaluator (easiest — parser done, just need eval)
2. Pipeline parser fix (connect `|>` in expression precedence chain)
3. Pipeline evaluator (filter, sort, take, map operations)

**PAUSE — test with pattern_matching.sigil and pipeline.sigil manually**

### Phase B: Closures + Type Checker (Steps 4–6)

4. Closure value type and evaluation
5. Lambda expression parsing
6. Higher-order function patterns (pass/return functions)
7. Enhanced type checker (3 new checks)

**PAUSE — test with higher_order.sigil, verify existing examples still work**

### Phase C: Examples + Tests + Polish (Steps 7–10)

8. Write all 6+ new example programs
9. Write 80+ new tests
10. Update REPL for new features
11. Update documentation

**DONE — Sprint 1 complete**

---

## Expected Outputs

### pattern_matching.sigil
```
$ sigil run examples/features/pattern_matching.sigil
HIGH - Action required within 1 hour
75
```

### pipeline.sigil
```
$ sigil run examples/features/pipeline.sigil
[{id: "T004", amount: 12000, ...}, {id: "T006", amount: 8500, ...}, {id: "T002", amount: 5000, ...}]
[150, 75, 200]
```

### higher_order.sigil
```
$ sigil run examples/features/higher_order.sigil
10
6
12
11
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Pipeline item binding (`it` vs record spread) is ambiguous | Medium | Medium | Default to `it` binding, spread record fields as convenience |
| Closures interact with forward chaining in unexpected ways | Medium | Medium | Closures capture env at definition time, not rule-firing time |
| Lambda syntax conflicts with compute declaration | Low | Medium | Use context: lambda only in expression position, compute at top level |
| Pipeline sort on non-comparable values | Medium | Low | Runtime error with clear message |
| Match patterns beyond simple values (nested, guards) | Low | Low | Phase 2 Sprint 1 = simple patterns only; guards/nested = later |
| Existing 373 tests regress from parser changes | Medium | High | Run full test suite after every parser modification |

---

## Definition of Done (Sprint 1)

```bash
# All of these must work:
sigil run examples/features/pattern_matching.sigil       # correct match output
sigil run examples/features/pipeline.sigil               # filtered/sorted output
sigil run examples/features/higher_order.sigil           # function composition works
sigil run examples/features/data_processing.sigil        # combined features
sigil run examples/basics/hello.sigil                    # still works (regression)
sigil run examples/rules/loan_eligibility.sigil --input '{...}'  # still works
sigil check examples/features/pattern_matching.sigil     # type check passes
sigil repl                                                # new features work interactively
pytest tests/ -v                                          # 450+ tests, all passing
ruff check src/ tests/                                    # clean
mypy src/sigil/ --ignore-missing-imports                  # clean
```
