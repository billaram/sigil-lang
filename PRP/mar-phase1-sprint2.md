# Sigil — Phase 1 Sprint 2: Type Checker + Interpreter

## Where We Are

**Sprint 1 (Lexer + Parser) is COMPLETE.**

Done:
- Lexer: 91 tests, all 5 examples tokenize
- Parser: 75 tests, all 5 examples parse into ASTs
- CLI: `sigil lex` and `sigil parse-ast` working
- Maturin + PyO3 build: Rust crate compiles and loads
- Total: 166 tests passing, `ruff check` clean

What's missing to close Phase 1:
- No runtime values or environment
- No rule evaluation or condition matching
- No expression evaluation
- No trace generation
- No type checking
- `sigil run` prints "not yet implemented"
- No REPL

---

## Sprint 2 Goal

> **Deliver a working tree-walking interpreter that can execute all 5 example programs, produce execution traces, and a basic type checker. Close Phase 1.**

### Phase 1 Exit Criteria (from ROADMAP.md)
- [x] Can lex all examples (Sprint 1)
- [x] Can parse all examples (Sprint 1)
- [ ] Can type-check basic programs
- [ ] Can evaluate rules: condition matching, action execution
- [ ] Can run `sigil run examples/basics/hello.sigil` → prints "Hello from Sigil!"
- [ ] Can run `sigil run examples/basics/temperature.sigil` with input → correct rule fires
- [ ] Execution trace produced for every rule evaluation
- [ ] REPL works interactively
- [ ] 180+ tests passing

---

## What the Interpreter Must Handle

### By Example (from simplest to most complex)

**hello.sigil** — Baseline:
- Evaluate constant (`define greeting as "Hello from Sigil!"`)
- Evaluate rule with `when true` → always fires
- Execute `print greeting` action
- Generate trace

**temperature.sigil** — Core rule engine:
- Record type definitions (store schema, validate field access)
- Field access via space syntax: `reading temperature` → `reading.temperature`
- Comparison conditions: `exceeds`, `is below`, `is between`
- Symbol comparison: `reading status is :active`
- Compound conditions: `and` with short-circuit
- Rule priorities: highest-priority matching rule wins
- Actions: `shutdown_system`, `trigger alert with severity :high`, `log status :normal`
- String interpolation in `explain`

**loan_eligibility.sigil** — Full program:
- Enum/sum types (`Decision is one of: approved | denied | review`)
- Rules that set boolean facts (`then age_eligible is true`)
- Rules depending on other rules' outputs (`when age_eligible is true and ...`)
- Compute blocks with `given` bindings, arithmetic, `return`
- Function calls: `calculate_rate(applicant)`, `math.max(rate, 2.5)`
- Block actions (`then:` with indented body)
- `becomes` statement (list append)
- Constructor expressions: `approved with rate: rate`
- Trace metadata: `category :lending`, `compliance [...]`

**medical_triage.sigil** — Quantifiers + neural stub:
- Quantified conditions: `any symptom in patient.symptoms is in IMMEDIATE_SYMPTOMS`
- `or` conditions with short-circuit
- Nested field access: `patient.vital_signs.oxygen_saturation`
- `is not empty`, `is not assigned` conditions
- `main:` block with `evaluate all rules with patient`
- Neural declarations → return fallback value (no real model)
- `given ... from input` → accept input data

**compliance_checker.sigil** — Membership + string interpolation:
- `in` for list membership: `jurisdiction in HIGH_RISK_JURISDICTIONS`
- Boolean field conditions: `sender_sanctions_match is true`
- String interpolation with field access: `"High-risk jurisdiction: {transaction.recipient_jurisdiction}"`
- `is not assigned` for default rule (`when risk is not assigned`)
- `clear` variant (no-field enum constructor)

---

## Step-by-Step Implementation Plan

### Step 1: Runtime Values and Environment

**File**: `src/sigil/interpreter/values.py`

The runtime value system — what Sigil programs operate on at runtime.

```python
# Value types (Python representations)
# Number  → int | float
# Text    → str
# Boolean → bool
# Symbol  → Symbol("active")  (distinct from str)
# None    → None
# List    → list[Value]
# Record  → Record(type_name, {field: value})
# Variant → Variant(type_name, variant_name, {field: value})

@dataclass(frozen=True)
class Symbol:
    name: str

@dataclass(frozen=True)
class Record:
    type_name: str | None  # named type or anonymous
    fields: dict[str, Value]

@dataclass(frozen=True)
class Variant:
    type_name: str
    variant_name: str
    fields: dict[str, Value]

Value = int | float | str | bool | None | Symbol | Record | Variant | list
```

**File**: `src/sigil/interpreter/environment.py`

Immutable environment (scope chain):

```python
class Environment:
    def __init__(self, bindings=None, parent=None):
        self._bindings = dict(bindings or {})
        self._parent = parent

    def get(self, name: str) -> Value | _Unbound
    def set(self, name: str, value: Value) -> Environment  # returns NEW env
    def extend(self, bindings: dict) -> Environment  # returns NEW child env
    def has(self, name: str) -> bool
```

Key: `set()` returns a NEW environment. Environments are never mutated.
Exception: `becomes` statements mutate the current scope (controlled mutability within compute blocks).

### Step 2: Trace Infrastructure

**File**: `src/sigil/interpreter/trace.py`

Trace is a first-class output, not debugging. Every evaluation produces trace entries.

```python
@dataclass
class TraceEntry:
    kind: str          # "condition", "action", "expression", "rule"
    description: str   # human-readable: "reading.temperature (105) exceeds SAFE_THRESHOLD (100)"
    result: Value      # the evaluated result
    source: str        # "symbolic" or "neural"
    timestamp_ms: float

@dataclass
class RuleTrace:
    rule_name: str
    priority: int
    fired: bool
    conditions: list[ConditionTrace]
    action_result: Value | None
    explain: str | None
    metadata: dict[str, Value]  # trace fields
    duration_ms: float

@dataclass
class ConditionTrace:
    description: str
    result: bool
    skipped: bool      # True if short-circuited
    bindings: dict[str, Value]

@dataclass
class ProgramTrace:
    rule_traces: list[RuleTrace]
    final_result: Value | None
    total_duration_ms: float
```

### Step 3: Expression Evaluator

**File**: `src/sigil/interpreter/evaluator.py`

Start with expressions — the simplest building block.

```
eval_expr(Literal)      → return literal value (int/float/str/bool/None)
eval_expr(SymbolLit)    → return Symbol(name)
eval_expr(Identifier)   → lookup in environment
eval_expr(FieldAccess)  → evaluate object, access field on Record
eval_expr(BinaryOp)     → evaluate left & right, apply operator (+,-,*,/)
eval_expr(UnaryOp)      → evaluate operand, apply operator (-, not)
eval_expr(FuncCall)     → evaluate args, lookup function, call
eval_expr(ListExpr)     → evaluate elements, return list
eval_expr(RecordExpr)   → evaluate field values, return Record
eval_expr(EmptyExpr)    → return [] (empty list)
eval_expr(ConstructorExpr) → return Variant(name, fields)
```

List concatenation: `list + list` → Python list concatenation.

### Step 4: Condition Evaluator

Handle all 12 condition types from the AST:

```
eval_cond(ComparisonCond)  → evaluate left/right, apply operator
  "exceeds"    → left > right
  "is below"   → left < right
  "is between" → right <= left <= right2
  "is at least" → left >= right
  "is at most"  → left <= right
  "is" / "equals" → left == right (structural)
  "is not"      → left != right

eval_cond(MembershipCond)  → element in collection (list)
eval_cond(BooleanCond)     → evaluate expr, check == value (true/false)
eval_cond(CompoundCond)    → AND: short-circuit; OR: short-circuit
eval_cond(NotCond)         → negate inner condition
eval_cond(QuantifiedCond)  → any/all/none over collection
eval_cond(IsAssignedCond)  → check if variable is bound in env
eval_cond(IsEmptyCond)     → check if list is empty
eval_cond(ContainsCond)    → check if collection contains element
eval_cond(HasCountCond)    → check collection length
eval_cond(StringCond)      → starts with / ends with / contains / matches
```

Short-circuit AND:
```
if left is false → return (false, [left_trace, skipped(right)])
```

Short-circuit OR:
```
if left is true → return (true, [left_trace, skipped(right)])
```

### Step 5: Rule Evaluator

The heart of Sigil — rule-based evaluation with priority.

```
eval_rules(rules, env):
  1. Sort rules by priority (highest first)
  2. For each rule:
     a. Evaluate all conditions against env
     b. Record trace (even if rule doesn't fire)
     c. If all conditions true:
        - Execute action
        - If action is SetAction: update env with new binding
        - If action is SimpleAction: call built-in function
        - If action is BlockAction: execute statement block
        - Record as fired
  3. Return (final_env, program_trace)
```

**Important**: Rules like `age_check` set facts (`age_eligible is true`) that later rules (`full_eligibility`) depend on. So rules must execute in priority order and later rules see earlier rules' outputs.

This is **forward chaining**: each rule that fires can add facts that enable subsequent rules.

### Step 6: Action Evaluator

Three action types:

```
eval_action(SimpleAction):
  # "alert", "shutdown_system", "print greeting"
  # "trigger alert with severity :high"
  If target: look up target as built-in function, call with params
  Else: look up name as built-in function, call

eval_action(SetAction):
  # "age_eligible is true", "risk is block with reason: ..."
  Evaluate value expression, bind target in environment

eval_action(BlockAction):
  # "then:" with indented body
  Execute statements in sequence, return last result
```

### Step 7: Statement Evaluator

For compute blocks and block actions:

```
eval_stmt(GivenStmt):     bind name = eval_expr(value) in env
eval_stmt(ReturnStmt):    eval_expr(value), signal return
eval_stmt(IfStmt):        eval condition, execute matching branch
eval_stmt(ForStmt):       iterate over list, execute body for each
eval_stmt(BecomeStmt):    target = eval_expr(value), MUTATE current scope
eval_stmt(EvaluateStmt):  "evaluate all rules with X" → run rule engine
eval_stmt(ExprStmt):      eval expression, discard result
```

`becomes` is the ONE place we allow mutation — within compute blocks, for list accumulation patterns like:
```sigil
reasons becomes reasons + ["Age outside eligible range"]
```

### Step 8: Compute Function Evaluator

User-defined functions:

```
eval_compute(ComputeDecl, args, env):
  1. Create new child environment
  2. Bind parameters to argument values
  3. Execute body statements in sequence
  4. Return the value from ReturnStmt
```

### Step 9: Program Evaluator (Top-Level)

Tie it all together:

```
eval_program(Program, input_data):
  1. Create global environment
  2. Process constants: bind each ConstDecl name → value
  3. Process type declarations: store schemas (for type checking & record construction)
  4. Register compute functions (don't evaluate yet)
  5. Register neural functions → stub that returns fallback value
  6. If main block exists:
     a. Execute main statements (given ... from input, evaluate all rules, etc.)
     b. Return result + trace
  7. If no main block:
     a. Require input_data
     b. Run all rules against input_data (forward chaining)
     c. Return result + trace
```

### Step 10: Built-in Functions

**File**: `src/sigil/interpreter/builtins.py`

Minimal set needed for the 5 examples:

```python
# I/O
print(value)              → print to stdout, return None

# Math (sigil.math module)
math.max(a, b)            → max(a, b)
math.min(a, b)            → min(a, b)

# Rule actions (special handling)
trigger(target, **params)  → record action in trace
log(target, **params)      → record action in trace
shutdown_system()          → record action in trace
alert(**params)            → record action in trace

# Neural stubs (return fallback)
extract_symptoms(text)     → returns [] (empty list, fallback)
parse_transaction(text)    → returns manual_review placeholder
build_patient_record(...)  → returns a mock record (or require input)
```

### Step 11: String Interpolation

Evaluate `{expr}` placeholders in explain strings and string literals:

```python
def interpolate(template: str, env: Environment) -> str:
    # Find {identifier} and {expr.field} patterns
    # Evaluate each expression in env
    # Replace with string representation of result
```

Needed for explain clauses like:
```sigil
explain "Temperature {reading.temperature} exceeds critical threshold of {CRITICAL_THRESHOLD}"
```

### Step 12: Basic Type Checker (Milestone 1.3)

**File**: `src/sigil/types/checker.py`

Light type checking — catch obvious errors before execution. NOT full type inference.

What to check:
1. **Undefined variables**: Reference to a name that's never defined
2. **Undefined fields**: `record.field` where field doesn't exist on the type
3. **Comparison type mismatches**: `exceeds` with a non-number
4. **Function arity**: Wrong number of arguments to compute functions
5. **Duplicate declarations**: Same rule/constant/type name declared twice

What to DEFER to Phase 2:
- Full type inference
- Unit type checking (degrees vs seconds)
- Generic type validation
- Neural return type verification

### Step 13: CLI Integration

**File**: `src/sigil/cli.py` — update existing

```bash
# Run a program with input data (JSON on stdin or --input flag)
sigil run examples/basics/hello.sigil
sigil run examples/basics/temperature.sigil --input '{"reading": {"sensor_id": "S1", "temperature": 105, "status": "active"}}'

# Run with trace output
sigil run examples/basics/temperature.sigil --input '...' --trace

# Type check only (no execution)
sigil check examples/rules/loan_eligibility.sigil

# Interactive REPL
sigil repl
```

### Step 14: REPL

**File**: `src/sigil/interpreter/repl.py`

Interactive shell that:
1. Accepts Sigil expressions and evaluates them
2. Accepts constant definitions
3. Accepts rule definitions and evaluates them
4. Shows results and traces
5. Maintains environment between inputs

```
sigil> define x as 42
sigil> x + 10
52
sigil> x exceeds 40
true
sigil> rule test:
...>   when x exceeds 40
...>   then print "big number"
[rule test] fired → print "big number"
```

### Step 15: Tests

**File**: `tests/interpreter/test_values.py` — 10+ tests for Value/Environment
**File**: `tests/interpreter/test_evaluator.py` — 40+ tests for expression/condition/rule evaluation
**File**: `tests/interpreter/test_integration.py` — 10+ tests running all 5 examples
**File**: `tests/types/test_checker.py` — 10+ tests for type checking
**File**: `tests/interpreter/test_repl.py` — 5+ tests for REPL

Target: 75+ new tests → 240+ total (exceeds ROADMAP's 180+ target)

### Step 16: Documentation Updates

- Update `ai_docs/STATUS.md` — mark Phase 1 complete
- Update `docs/ROADMAP.md` — check off Phase 1 milestones
- Write `PRP/sprint2.md` (this file) retrospective notes

---

## Files to Create/Modify

### New files (10)
```
src/sigil/interpreter/values.py      — Runtime values + Symbol + Record + Variant
src/sigil/interpreter/environment.py — Immutable environment (scope chain)
src/sigil/interpreter/trace.py       — Trace dataclasses
src/sigil/interpreter/evaluator.py   — Tree-walking evaluator (main engine)
src/sigil/interpreter/builtins.py    — Built-in functions (print, math, stubs)
src/sigil/interpreter/repl.py        — Interactive REPL
src/sigil/types/checker.py           — Basic type checker
tests/interpreter/__init__.py        — Test package
tests/interpreter/test_evaluator.py  — Evaluator tests (50+)
tests/types/test_checker.py          — Type checker tests (10+)
```

### Modified files (3)
```
src/sigil/interpreter/__init__.py    — Export public API
src/sigil/types/__init__.py          — Export public API
src/sigil/cli.py                     — Add run, check, repl commands
```

---

## Implementation Order (3 phases, with pause points)

### Phase A: Core Evaluator (Steps 1–8)

Build the evaluation engine from bottom up:

1. Values + Environment + Trace infrastructure
2. Expression evaluator (literals, identifiers, field access, binary ops, calls)
3. Condition evaluator (all 12 types)
4. Rule evaluator (priority, short-circuit, forward chaining)
5. Action evaluator (simple, set, block)
6. Statement evaluator (given, return, if, for, becomes, evaluate)
7. Compute function evaluator
8. Program evaluator

**PAUSE — test with hello.sigil and temperature.sigil manually**

### Phase B: Integration + Tests (Steps 9–12)

1. Built-in functions
2. String interpolation
3. Basic type checker
4. 75+ tests, all 5 examples run

**PAUSE — verify all examples produce correct output + traces**

### Phase C: CLI + REPL + Polish (Steps 13–16)

1. `sigil run` with --input and --trace flags
2. `sigil check` command
3. REPL implementation
4. Documentation updates

**DONE — Phase 1 complete**

---

## Expected Outputs

### hello.sigil
```
$ sigil run examples/basics/hello.sigil
Hello from Sigil!

$ sigil run examples/basics/hello.sigil --trace
[rule hello_world] FIRED (priority 0)
  when true → true
  then print greeting → "Hello from Sigil!"
  explain: "This is the simplest possible Sigil program"

Result: Hello from Sigil!
```

### temperature.sigil
```
$ sigil run examples/basics/temperature.sigil --input '{"reading": {"sensor_id": "S1", "temperature": 105, "status": "active"}}'

$ sigil run examples/basics/temperature.sigil --input '...' --trace
[rule emergency_shutdown] NOT FIRED (priority 100)
  when reading.temperature (105) exceeds CRITICAL_THRESHOLD (150) → false

[rule temperature_alert] FIRED (priority 10)
  when reading.temperature (105) exceeds SAFE_THRESHOLD (100) → true
  and reading.status (:active) is :active → true
  then trigger alert with severity :high
  explain: "Temperature 105 exceeded safe threshold on sensor S1"

Result: alert triggered (severity: :high)
```

### loan_eligibility.sigil
```
$ sigil run examples/rules/loan_eligibility.sigil --input '{"applicant": {"name": "Alice", "age": 35, "income": 85000, "credit_score": 740, "debt_to_income": 28, "employment_years": 5, "loan_amount": 250000}}'

[rule age_check] FIRED → age_eligible = true
[rule income_check] FIRED → income_eligible = true
[rule credit_check] FIRED → credit_eligible = true
[rule dti_check] FIRED → dti_eligible = true
[rule employment_check] FIRED → employment_eligible = true
[rule full_eligibility] FIRED → loan_approved = true
[rule approve_decision] FIRED → approved with rate: 3.55

Result: Decision.approved(rate=3.55)
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Forward chaining gets complex | Medium | Medium | Start with single-pass rule eval, add iteration if needed |
| `becomes` mutability conflicts with immutable env | Medium | Low | Isolated to compute blocks only — use mutable local dict |
| Neural stubs are too simplistic | Low | Low | Just return fallback value. Real neural = Phase 3 |
| String interpolation edge cases | Medium | Low | Start with simple {identifier} and {a.b}, defer complex expr |
| REPL multi-line input is tricky | Medium | Low | Start with single-line, add multi-line later |
| Test count target (180+) is ambitious | Low | Low | Already at 166, need only 14+ more. Targeting 75+ new |

---

## Definition of Done (Sprint 2 / Phase 1)

```bash
# All of these must work:
sigil run examples/basics/hello.sigil                    # prints "Hello from Sigil!"
sigil run examples/basics/temperature.sigil --input '{...}'  # correct rule fires
sigil run examples/rules/loan_eligibility.sigil --input '{...}'  # approved/denied
sigil run examples/basics/hello.sigil --trace            # shows execution trace
sigil check examples/rules/loan_eligibility.sigil        # type check passes
sigil repl                                                # interactive shell works
pytest tests/ -v                                          # 240+ tests, all passing
ruff check src/ tests/                                    # clean
```
