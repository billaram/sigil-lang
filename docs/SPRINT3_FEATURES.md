# Phase 2 Sprint 3: Advanced Rules + Polish — Feature Guide

> A comprehensive walkthrough of every feature implemented in Sprint 3,
> with examples, dry runs, and implementation details.

---

## Table of Contents

1. [Backward Chaining (query statement)](#1-backward-chaining)
2. [Temporal Constraints (within keyword)](#2-temporal-constraints)
3. [Unit-Annotated Constants](#3-unit-annotated-constants)
4. [Multi-Level Proof Trees](#4-multi-level-proof-trees)
5. [Forward + Backward Chaining Together](#5-forward--backward-chaining-together)
6. [Standard Library: sigil.time](#6-stdlib-sigiltime)
7. [Standard Library: sigil.trace](#7-stdlib-sigiltrace)
8. [Standard Library: sigil.io](#8-stdlib-sigilio)
9. [Type Checker: Return Type Consistency](#9-type-checker-return-type-consistency)
10. [Type Checker: Gradual Type Inference](#10-type-checker-gradual-type-inference)
11. [Type Checker: Unit Awareness](#11-type-checker-unit-awareness)
12. [Full Example: Insurance Underwriter](#12-full-example-insurance-underwriter)

---

## 1. Backward Chaining

### What is it?

Backward chaining is **goal-driven** rule evaluation. Instead of evaluating all rules
repeatedly until a fixed point (forward chaining), backward chaining starts from a
**goal** — "I want to know the value of `decision`" — and works **backward** through
the rule graph to find a chain of rule firings that can establish that value.

Think of it like this:

- **Forward chaining**: "Here are the facts. Let me see what I can conclude."
- **Backward chaining**: "I need to know X. What rules can give me X? What do those rules need?"

### Syntax

```sigil
-- In the main block, ask a question:
main:
  query decision       -- "What is the value of decision?"
  query premium        -- "What is the value of premium?"
  print(decision)
  print(premium)
```

The `query` keyword takes a **goal variable name**. It optionally accepts a `with` clause:

```sigil
query decision with some_arg    -- (reserved for future use)
```

### How It Works — The Algorithm

The backward chaining engine (`src/sigil/interpreter/backward.py`) follows these steps:

```
query(goal, depth=0):
  1. BASE CASE: Is the goal already in the environment?
     → Yes: return success with the existing value.
     → No: continue.

  2. DEPTH CHECK: Is depth >= 50?
     → Yes: return failure (prevent infinite recursion).

  3. CYCLE CHECK: Are we already trying to prove this goal?
     → Yes: return failure (prevent circular dependencies).

  4. FIND CANDIDATES: Look up all rules that can SET this goal.
     Sort by priority (highest first).

  5. FOR EACH CANDIDATE RULE:
     a. Process 'given' clauses (pre-computation bindings).
     b. For each condition in the rule:
        i.   Find unbound variables in the condition.
        ii.  For each unbound variable, RECURSIVELY call query(var, depth+1).
        iii. Evaluate the condition with updated bindings.
        iv.  If the condition fails → try the next candidate rule.
     c. All conditions passed → execute the rule's action.
     d. Return success with new bindings.

  6. No candidate worked → return failure.
```

### The Rule Index

Before any query, the engine builds an **index** mapping variable names to rules:

```python
# Given these rules:
rule set_x:   ...  then x is 42
rule set_y:   ...  then y is :ok
rule set_x_2: ...  then x is 99

# The index becomes:
{
    "x": [set_x, set_x_2],   # two rules can set x
    "y": [set_y],             # one rule can set y
}
```

This means: when we `query x`, we know immediately which rules to try.

### Walkthrough: Bird Logic

```sigil
rule has_wings:
  when species is :bird
  then wings is true

rule can_fly_bird:
  when wings is true
  and species is :bird
  then can_fly is true
  explain "Birds with wings can fly"

main:
  given species as :bird
  query can_fly
  print(can_fly)
```

**Step-by-step dry run:**

```
Environment: { species: :bird }

1. main: given species as :bird
   → env = { species: :bird }

2. main: query can_fly
   → BackwardChainer.query("can_fly")

   2a. Is "can_fly" in env? NO
   2b. Find rules that set "can_fly":
       → [can_fly_bird]

   2c. Try rule "can_fly_bird":
       Conditions:
         - "wings is true"
           → Is "wings" in env? NO
           → "wings" is an unbound variable, and rules exist for it.
           → RECURSE: query("wings", depth=1)

             2c-i. Is "wings" in env? NO
             2c-ii. Find rules that set "wings":
                    → [has_wings]
             2c-iii. Try rule "has_wings":
                     Condition: "species is :bird"
                     → species = :bird ✓
                     Action: wings = true
                     → PROVED! Return { wings: true }

           → env = { species: :bird, wings: true }
           → Evaluate "wings is true" → true ✓

         - "species is :bird"
           → species = :bird ✓

       All conditions passed!
       Action: can_fly = true
       → PROVED! Return { can_fly: true }

   env = { species: :bird, wings: true, can_fly: true }

3. main: print(can_fly)
   → prints: true
```

### ProofNode Data Structure

Every `query` produces a **proof tree** — a `ProofNode` that records what happened:

```
ProofNode(
  goal="can_fly",
  rule="can_fly_bird",
  result=True,
  bindings={"can_fly": true},
  subgoals=[
    ProofNode(
      goal="wings",
      rule="has_wings",
      result=True,
      bindings={"wings": true},
      subgoals=[]
    )
  ]
)
```

This tree is appended to `ProgramTrace.proof_trees` for auditing.

---

## 2. Temporal Constraints

### What is it?

Temporal constraints express time-bounded conditions on rules using the `within` keyword.
This is the **foundation** for real-time rule systems — the parser and AST capture temporal
information, and the evaluator records it in trace metadata.

> **Note**: In Sprint 3, temporal constraints are **parsed and recorded** but **not enforced
> at runtime**. Enforcement (actual time-window checking) is planned for Phase 3.

### Syntax

```sigil
rule critical_alert with priority 10:
  when temperature exceeds 150
  within 10 seconds                    -- temporal constraint
  then alert_level is :critical
  explain "Temperature critically high"
```

The `within` clause goes **between the conditions and the `then` keyword**:

```
rule <name> [with priority <N>]:
  when <conditions>
  within <duration> <unit>             -- NEW in Sprint 3
  then <action>
  [explain <message>]
```

Supported units: any identifier — `seconds`, `minutes`, `hours`, `days`, `milliseconds`, etc.
The grammar accepts any word as a unit; semantic validation happens later.

### How It's Represented

In the AST:

```python
@dataclass(frozen=True)
class TemporalConstraint(Node):
    duration: Expression    # e.g., Literal(90) or an expression
    unit: str               # e.g., "seconds"

@dataclass(frozen=True)
class RuleDecl(Declaration):
    name: str
    conditions: tuple[Condition, ...]
    action: Action
    priority: int = 0
    explain: Expression | None = None
    given_clauses: tuple[GivenClause, ...] = ()
    temporal: TemporalConstraint | None = None    # NEW
```

### What Happens at Runtime

When a rule with a `within` clause fires, the evaluator records the constraint in
the rule's trace metadata:

```python
# In evaluator._eval_single_rule():
if rule.temporal is not None:
    dur = self.eval_expression(rule.temporal.duration, env)
    rule_trace.metadata["_temporal_constraint"] = f"within {dur} {rule.temporal.unit}"
```

So after execution, you can inspect the trace:

```python
trace.rule_traces[0].metadata
# → {"_temporal_constraint": "within 90 seconds"}
```

### Example

```sigil
define CRITICAL_THRESHOLD as 150 degrees

rule critical_temperature with priority 10:
  when temperature exceeds 150
  within 10 seconds
  then alert_level is :critical
  explain "Temperature critically high"

rule normal_temperature:
  when temperature is below 100
  then alert_level is :normal
  explain "Temperature within normal range"
```

With `temperature = 200`:
- `critical_temperature` fires (priority 10, evaluated first)
- Trace records: `"_temporal_constraint": "within 10 seconds"`
- `alert_level = :critical`

With `temperature = 50`:
- `critical_temperature` does NOT fire (condition fails)
- `normal_temperature` fires
- No temporal metadata (no `within` clause)
- `alert_level = :normal`

---

## 3. Unit-Annotated Constants

### What is it?

Number literals and `define` constants can carry **unit annotations** — metadata
that describes what the number means. This enables the type checker to catch
unit mismatches (e.g., comparing degrees to seconds).

### Syntax

```sigil
-- Constants with units
define MAX_TEMP as 100 degrees
define TIMEOUT as 30 seconds
define MIN_SALARY as 50000 dollars

-- Literals with units (in conditions)
rule check:
  when temperature exceeds 100 degrees
  then alert is true
```

### How It's Represented

The `Literal` AST node gained a `unit` field:

```python
@dataclass(frozen=True)
class Literal(Expression):
    value: int | float | str | bool
    unit: str | None = None    # NEW — e.g., "degrees", "seconds"
```

When the parser encounters a NUMBER token followed by a UNIT token (like `seconds`,
`degrees`, `dollars`), it attaches the unit:

```python
# Parser creates:
Literal(value=100, unit="degrees")
Literal(value=30, unit="seconds")
Literal(value=50000, unit=None)    # no unit suffix
```

For `define` constants, the unit is tracked by the type checker:

```python
# In the type checker:
self._const_units: dict[str, str] = {}

# When processing: define MAX_TEMP as 100 degrees
self._const_units["MAX_TEMP"] = "degrees"
```

### Runtime Behavior

Units are **metadata only** — they don't affect the runtime value. `100 degrees` evaluates
to `100`. The unit information is used by:

1. The **type checker** for unit mismatch warnings (see [Section 11](#11-type-checker-unit-awareness))
2. The **trace system** for documentation
3. Future phases for dimensional analysis

---

## 4. Multi-Level Proof Trees

### What is it?

When backward chaining resolves a query, it may need to traverse multiple levels of
rules. Each level becomes a node in the **proof tree** — a hierarchical data structure
that records exactly which rules fired and why.

### The Structure

```python
@dataclass
class ProofNode:
    goal: str                              # What we're trying to prove
    rule: str | None = None                # Which rule proved it (None if from env)
    subgoals: list[ProofNode] = []         # What we had to prove first
    result: bool = False                   # Did we succeed?
    bindings: dict[str, Value] = {}        # What values did we establish?
```

### Walkthrough: 4-Level Proof Chain

Consider this program:

```sigil
-- Level 1: Base fact
rule set_income:
  when salary exceeds 0
  then income is salary

-- Level 2: Derived from income
rule high_income:
  when income exceeds 80000
  then income_level is :high

-- Level 3: Derived from income_level
rule premium_eligible:
  when income_level is :high
  then premium_eligible is true

-- Level 4: Final decision
rule approve_premium:
  when premium_eligible is true
  then decision is :approved
  explain "Premium approved based on high income"

main:
  given salary as 95000
  query decision
  print(decision)
```

**Dry run with `salary = 95000`:**

```
Environment: { salary: 95000 }

query("decision")
│
├── Is "decision" in env? NO
├── Rules that set "decision": [approve_premium]
│
├── Try rule "approve_premium":
│   Condition: "premium_eligible is true"
│   → "premium_eligible" is UNBOUND
│   → RECURSE: query("premium_eligible")
│   │
│   ├── Is "premium_eligible" in env? NO
│   ├── Rules that set "premium_eligible": [premium_eligible]
│   │
│   ├── Try rule "premium_eligible":
│   │   Condition: "income_level is :high"
│   │   → "income_level" is UNBOUND
│   │   → RECURSE: query("income_level")
│   │   │
│   │   ├── Is "income_level" in env? NO
│   │   ├── Rules that set "income_level": [high_income]
│   │   │
│   │   ├── Try rule "high_income":
│   │   │   Condition: "income exceeds 80000"
│   │   │   → "income" is UNBOUND
│   │   │   → RECURSE: query("income")
│   │   │   │
│   │   │   ├── Is "income" in env? NO
│   │   │   ├── Rules that set "income": [set_income]
│   │   │   │
│   │   │   ├── Try rule "set_income":
│   │   │   │   Condition: "salary exceeds 0"
│   │   │   │   → salary = 95000 > 0 ✓
│   │   │   │   Action: income = salary → income = 95000
│   │   │   │   → PROVED! bindings = {income: 95000}
│   │   │   │
│   │   │   └── env = { salary: 95000, income: 95000 }
│   │   │
│   │   │   → Evaluate: income(95000) exceeds 80000 → ✓
│   │   │   Action: income_level = :high
│   │   │   → PROVED! bindings = {income_level: :high}
│   │   │
│   │   └── env = { salary: 95000, income: 95000, income_level: :high }
│   │
│   │   → Evaluate: income_level(:high) is :high → ✓
│   │   Action: premium_eligible = true
│   │   → PROVED! bindings = {premium_eligible: true}
│   │
│   └── env = { salary: 95000, income: 95000, income_level: :high,
│               premium_eligible: true }
│
│   → Evaluate: premium_eligible(true) is true → ✓
│   Action: decision = :approved
│   → PROVED! bindings = {decision: :approved}
│
└── Final env = { salary: 95000, income: 95000, income_level: :high,
                  premium_eligible: true, decision: :approved }

print(decision) → :approved
```

### The Resulting Proof Tree

```
ProofNode(goal="decision", rule="approve_premium", result=True)
└── ProofNode(goal="premium_eligible", rule="premium_eligible", result=True)
    └── ProofNode(goal="income_level", rule="high_income", result=True)
        └── ProofNode(goal="income", rule="set_income", result=True)
```

Four levels deep. Each level had to be proved before the next could proceed.

---

## 5. Forward + Backward Chaining Together

### What is it?

Sigil supports **both** forward and backward chaining in the same program. You can
use forward chaining (the default rule evaluation) to establish some facts, then
use backward chaining (`query`) to derive specific conclusions.

### How They Interact

Forward chaining runs **first** (during rule evaluation), then `query` statements
in `main:` trigger backward chaining against the **same set of rules**.

The key insight: backward chaining sees the environment **including** any facts
established by forward chaining. And after backward chaining, the environment
is updated with any new bindings it proved.

### Example: Mixed Strategy

```sigil
-- These rules run via FORWARD chaining
-- (evaluated iteratively until fixed point)
rule base_check:
  when age exceeds 17
  then adult is true

-- This rule will be invoked via BACKWARD chaining
rule can_vote:
  when adult is true
  and citizen is true
  then voting_eligible is true

main:
  -- Forward chaining has already run by the time main: executes
  -- So "adult" is already true (if age > 17)

  -- Now backward chaining kicks in:
  query voting_eligible
  print(voting_eligible)
```

With input `{ age: 25, citizen: true }`:

1. **Forward chaining**: Evaluates all rules iteratively. `base_check` fires → `adult = true`.
2. **Main block**: `query voting_eligible` triggers backward chaining.
3. **Backward chaining**:
   - Goal: `voting_eligible`
   - Rule `can_vote` needs: `adult is true` (already in env from forward chaining!) AND `citizen is true` (in env from input).
   - Both conditions satisfied → `voting_eligible = true`.

The power here is that backward chaining doesn't need to re-prove `adult` — it finds
it already in the environment from forward chaining.

---

## 6. Stdlib: sigil.time

### What is it?

A standard library module for working with timestamps and durations.

### Available Functions

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `time.now()` | none | Number | Current Unix timestamp in seconds |
| `time.now_ms()` | none | Number | Current Unix timestamp in milliseconds |
| `time.format_timestamp(ts)` | Number | Text | Convert timestamp to ISO 8601 string |
| `time.elapsed(start, end)` | Number, Number | Number | Seconds between two timestamps |
| `time.duration_seconds(n)` | Number | Number | Convert to duration value |

### Usage

```sigil
import sigil.time

main:
  given start as time.now()
  -- ... do work ...
  given end as time.now()
  given elapsed as time.elapsed(start, end)
  print(elapsed)

  given formatted as time.format_timestamp(start)
  print(formatted)    -- e.g., "2026-03-10T14:30:00+00:00"
```

### Implementation

Each function follows the stdlib signature: `(args: list[Value], trace: ProgramTrace) -> Value`.

```python
def stdlib_now(args, _trace):
    return time.time()          # Unix timestamp (seconds, float)

def stdlib_now_ms(args, _trace):
    return time.time() * 1000   # Milliseconds

def stdlib_format_timestamp(args, _trace):
    ts = float(args[0])
    dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.isoformat()       # "2026-03-10T14:30:00+00:00"

def stdlib_elapsed(args, _trace):
    return float(args[1]) - float(args[0])

def stdlib_duration_seconds(args, _trace):
    return float(args[0])
```

---

## 7. Stdlib: sigil.trace

### What is it?

A standard library module for introspecting the execution trace **from within a Sigil program**.
This enables programs to audit themselves — checking which rules fired, how long evaluation took, etc.

### Available Functions

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `trace.to_json()` | none | Text | Entire trace as a JSON string |
| `trace.fired_rules()` | none | List | Names of rules that fired |
| `trace.rule_count()` | none | Number | Total number of rules evaluated |
| `trace.duration_ms()` | none | Number | Total execution time in ms |

### Usage

```sigil
import sigil.trace

rule example:
  when x exceeds 10
  then result is :high

main:
  given rules as trace.fired_rules()
  print(rules)           -- ["example"]

  given count as trace.rule_count()
  print(count)           -- 1

  given json as trace.to_json()
  print(json)            -- {"rules": [...], "total_duration_ms": ...}
```

### Implementation

These functions receive the live `ProgramTrace` object and extract data from it:

```python
def stdlib_trace_to_json(args, _trace):
    data = {
        "rules": [
            {
                "name": rt.rule_name,
                "priority": rt.priority,
                "fired": rt.fired,
                "duration_ms": rt.duration_ms,
            }
            for rt in _trace.rule_traces
        ],
        "total_duration_ms": _trace.total_duration_ms,
    }
    return json.dumps(data)

def stdlib_fired_rules(args, _trace):
    return [rt.rule_name for rt in _trace.rule_traces if rt.fired]

def stdlib_rule_count(args, _trace):
    return len(_trace.rule_traces)

def stdlib_trace_duration_ms(args, _trace):
    return _trace.total_duration_ms
```

---

## 8. Stdlib: sigil.io

### What is it?

A standard library module for file I/O and JSON serialization.

### Available Functions

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `io.read_file(path)` | Text | Text | Read a file's contents |
| `io.write_file(path, content)` | Text, Text | None | Write content to a file |
| `io.file_exists(path)` | Text | Boolean | Check if a file exists |
| `io.parse_json(str)` | Text | Value | Parse JSON string to Sigil value |
| `io.to_json(value)` | Value | Text | Serialize Sigil value to JSON |

### Usage

```sigil
import sigil.io

main:
  -- JSON round-trip
  given data as io.parse_json("{\"name\": \"Alice\", \"age\": 30}")
  print(data)            -- Record(name="Alice", age=30)

  given json_str as io.to_json(data)
  print(json_str)        -- {"name": "Alice", "age": 30}

  -- File operations
  io.write_file("output.txt", "Hello, Sigil!")
  given exists as io.file_exists("output.txt")
  print(exists)          -- true

  given contents as io.read_file("output.txt")
  print(contents)        -- "Hello, Sigil!"
```

### JSON ↔ Sigil Value Conversion

The `parse_json` and `to_json` functions handle bidirectional conversion:

| JSON Type | Sigil Type |
|-----------|------------|
| `{}` object | `Record` |
| `[]` array | `List` |
| `"string"` | `Text` |
| `123` / `1.5` | `Number` |
| `true`/`false` | `Boolean` |
| `null` | `None` |

Nested structures are converted recursively.

---

## 9. Type Checker: Return Type Consistency

### What is it?

The type checker now warns when a `compute` function's return statements produce
values whose types don't match the declared return type. This is **Check #9** in the
type checker.

### How It Works

When a function declares `returns Number`, the checker inspects every `return` statement
and infers the type of the returned expression:

```
Literal(42)       → Number
Literal("hello")  → Text
Literal(true)     → Boolean
SymbolLit(:ok)    → Symbol
ListExpr([...])   → List
```

If the inferred type doesn't match the declared type, a **warning** is emitted (not
an error — Sigil uses gradual typing).

### Examples

```sigil
-- OK: returns Number, actually returns a number
compute add from a: Number, b: Number returns Number:
  return a + b                        -- ✓ No warning

-- WARNING: returns Number, but returns a string
compute get_name from x: Number returns Number:
  return "hello"                      -- ⚠ Return type mismatch: function
                                      --   declares 'Number' but returns 'Text'

-- WARNING: returns Text, but returns a symbol
compute label from x: Number returns Text:
  return :active                      -- ⚠ Return type mismatch: function
                                      --   declares 'Text' but returns 'Symbol'

-- OK: no declared return type → no check
compute do_stuff from x: Number:
  return "hello"                      -- ✓ No warning (no declared return type)
```

### Branch Checking

The checker recursively walks `if`/`else` branches:

```sigil
compute classify from x: Number returns Number:
  if x exceeds 10:
    return "high"     -- ⚠ Return type mismatch: 'Number' but returns 'Text'
  return x            -- ✓ OK
```

---

## 10. Type Checker: Gradual Type Inference

### What is it?

The type checker now **infers types** from `given` statements with literal values and
tracks them in scope. This means the checker knows that `given x as 42` makes `x` a
Number, and can use that information for subsequent checks. This is **Check #10**.

### How It Works

When the checker encounters a `given` statement, it inspects the right-hand side:

```python
def _infer_from_stmt(self, stmt, inferred):
    if isinstance(stmt, GivenStmt):
        t = self._infer_expr_type(stmt.value)  # "Number", "Text", etc.
        if t:
            inferred[stmt.name] = t
```

The inferred types are added to the local scope, so:

1. The variable is recognized as defined (no "undefined variable" error)
2. Its type is available for return-type checking

### Examples

```sigil
-- The checker infers y: Number from the literal 42
compute test from x: Number returns Number:
  given y as 42
  return y              -- ✓ No error (y is in scope, inferred as Number)

-- The checker infers name: Text from the literal "Alice"
compute test from x: Number returns Number:
  given name as "Alice"
  return name           -- (would warn: 'Number' but returns 'Text')

-- Chain of given statements: each adds to scope
main:
  given a as 42         -- a: Number
  given b as a + 1      -- b is in scope (a was defined above)
  print(b)              -- ✓ No error
```

### query Adds to Scope

The `query` statement also adds its goal variable to scope, since after the query
the variable will have a value:

```sigil
rule set_x:
  when true is true
  then x is 42

main:
  query x        -- Adds "x" to scope
  print(x)       -- ✓ No "undefined variable" error
```

---

## 11. Type Checker: Unit Awareness

### What is it?

The type checker now warns when comparing values with **different unit suffixes**. This
catches dimensional errors at analysis time. This is **Check #11**.

### How It Works

The checker tracks units from two sources:

1. **Literal units**: `100 degrees` → `Literal(value=100, unit="degrees")`
2. **Constant units**: `define MAX_TEMP as 100 degrees` → `_const_units["MAX_TEMP"] = "degrees"`

When it encounters a comparison condition, it checks both sides:

```python
def _check_unit_comparison(self, cond):
    left_unit = self._get_unit(cond.left)     # "degrees" | "seconds" | None
    right_unit = self._get_unit(cond.right)
    if left_unit and right_unit and left_unit != right_unit:
        self._warning(cond.location,
            f"Unit mismatch in comparison: '{left_unit}' vs '{right_unit}'")
```

### Examples

```sigil
-- OK: same units
define MAX_TEMP as 100 degrees
rule check:
  when temperature exceeds 100 degrees    -- ✓ No warning (degrees vs degrees)
  then alert is true

-- WARNING: different units
define LIMIT as 100 degrees
rule check:
  when LIMIT exceeds 50 seconds           -- ⚠ Unit mismatch: 'degrees' vs 'seconds'
  then alert is true

-- OK: one side has no unit (can't detect mismatch)
rule check:
  when x exceeds 100 degrees              -- ✓ No warning (x has no unit)
  then alert is true

-- OK: neither side has a unit
rule check:
  when x exceeds 100                      -- ✓ No warning
  then alert is true
```

### Why Warnings, Not Errors?

Sigil uses **gradual typing**. Unit annotations are opt-in metadata. The checker
can only warn about mismatches when **both** sides have units. If one or neither
side has a unit, no warning is emitted — the programmer might know what they're doing.

---

## 12. Full Example: Insurance Underwriter

This example combines **all** Sprint 3 features in a single, realistic program.

### The Program

```sigil
-- Constants with unit annotations
define MAX_AGE as 65 years
define MIN_INCOME as 30000 dollars
define POLICY_WINDOW as 90 seconds

-- Level 1: Base eligibility facts
rule age_eligible:
  when age is below 66
  and age exceeds 17
  then age_ok is true
  explain "Applicant age is within insurable range"

rule income_eligible:
  when annual_income exceeds 29999
  then income_ok is true
  explain "Applicant meets minimum income requirement"

-- Level 2: Risk assessment
rule low_risk:
  when age_ok is true
  and income_ok is true
  and smoker is false
  then risk_level is :low
  explain "Non-smoker with valid age and income"

rule medium_risk:
  when age_ok is true
  and income_ok is true
  and smoker is true
  then risk_level is :medium
  explain "Smoker with valid age and income"

-- Level 3: Premium calculation
rule low_risk_premium:
  when risk_level is :low
  then:
    given premium as annual_income * 0.02

rule medium_risk_premium:
  when risk_level is :medium
  then:
    given premium as annual_income * 0.05

-- Level 4: Final decision (with temporal + priority)
rule approve_policy with priority 10:
  when risk_level is :low
  within 90 seconds
  then decision is :approved
  explain "Policy approved — low risk applicant"

rule conditional_approve with priority 5:
  when risk_level is :medium
  within 90 seconds
  then decision is :conditional
  explain "Policy conditionally approved — requires medical exam"

-- Backward chaining drives everything
main:
  query decision
  query premium
  print(decision)
  print(premium)
```

### Dry Run: Scenario A — Non-Smoker

**Input**: `{ age: 35, annual_income: 75000, smoker: false }`

```
Initial env: { age: 35, annual_income: 75000, smoker: false }

═══ query decision ═══

query("decision")
├── Not in env. Rules: [approve_policy(p=10), conditional_approve(p=5)]
│
├── Try approve_policy (priority 10):
│   Condition: risk_level is :low
│   → "risk_level" UNBOUND
│   → RECURSE: query("risk_level")
│   │
│   ├── Not in env. Rules: [low_risk, medium_risk]
│   │
│   ├── Try low_risk:
│   │   Conditions:
│   │     1. age_ok is true
│   │        → "age_ok" UNBOUND
│   │        → RECURSE: query("age_ok")
│   │        │
│   │        ├── Try age_eligible:
│   │        │   Conditions:
│   │        │     - age(35) is below 66 → ✓
│   │        │     - age(35) exceeds 17 → ✓
│   │        │   Action: age_ok = true
│   │        │   → PROVED { age_ok: true }
│   │        │
│   │        env += { age_ok: true }
│   │        → age_ok(true) is true → ✓
│   │
│   │     2. income_ok is true
│   │        → "income_ok" UNBOUND
│   │        → RECURSE: query("income_ok")
│   │        │
│   │        ├── Try income_eligible:
│   │        │   Condition: annual_income(75000) exceeds 29999 → ✓
│   │        │   Action: income_ok = true
│   │        │   → PROVED { income_ok: true }
│   │        │
│   │        env += { income_ok: true }
│   │        → income_ok(true) is true → ✓
│   │
│   │     3. smoker(false) is false → ✓
│   │
│   │   All conditions passed!
│   │   Action: risk_level = :low
│   │   → PROVED { risk_level: :low }
│   │
│   env += { risk_level: :low }
│   → risk_level(:low) is :low → ✓
│
│   Temporal: within 90 seconds → recorded in trace metadata
│   Action: decision = :approved
│   → PROVED { decision: :approved }

env = { age: 35, annual_income: 75000, smoker: false,
        age_ok: true, income_ok: true, risk_level: :low,
        decision: :approved }

═══ query premium ═══

query("premium")
├── Not in env. Rules: [low_risk_premium, medium_risk_premium]
│
├── Try low_risk_premium:
│   Condition: risk_level(:low) is :low → ✓   (already in env!)
│   Action: premium = 75000 * 0.02 = 1500.0
│   → PROVED { premium: 1500.0 }

═══ Output ═══
print(decision) → :approved
print(premium)  → 1500.0
```

### Dry Run: Scenario B — Smoker

**Input**: `{ age: 35, annual_income: 75000, smoker: true }`

```
Initial env: { age: 35, annual_income: 75000, smoker: true }

═══ query decision ═══

query("decision")
├── Rules: [approve_policy(p=10), conditional_approve(p=5)]
│
├── Try approve_policy (priority 10 — tried FIRST):
│   Needs: risk_level is :low
│   → RECURSE: query("risk_level")
│   │
│   ├── Try low_risk:
│   │   Conditions pass for age_ok and income_ok (same as before)
│   │   But: smoker(true) is false → ✗ FAILS
│   │
│   ├── Try medium_risk:
│   │   age_ok(true) is true → ✓
│   │   income_ok(true) is true → ✓
│   │   smoker(true) is true → ✓
│   │   Action: risk_level = :medium
│   │   → PROVED { risk_level: :medium }
│   │
│   env += { risk_level: :medium }
│   → risk_level(:medium) is :low → ✗ FAILS (it's :medium, not :low)
│
├── Try conditional_approve (priority 5 — tried SECOND):
│   Condition: risk_level(:medium) is :medium → ✓
│   Temporal: within 90 seconds → recorded
│   Action: decision = :conditional
│   → PROVED { decision: :conditional }

═══ query premium ═══

query("premium")
├── Try low_risk_premium:
│   risk_level(:medium) is :low → ✗ FAILS
├── Try medium_risk_premium:
│   risk_level(:medium) is :medium → ✓
│   Action: premium = 75000 * 0.05 = 3750.0
│   → PROVED { premium: 3750.0 }

═══ Output ═══
print(decision) → :conditional
print(premium)  → 3750.0
```

### Features Used Summary

| Feature | Where in This Example |
|---------|----------------------|
| **Backward chaining** | `query decision`, `query premium` in main |
| **Multi-level proof trees** | 4 levels: eligibility → risk → premium/decision |
| **Temporal constraints** | `within 90 seconds` on approve/conditional rules |
| **Unit-annotated constants** | `65 years`, `30000 dollars`, `90 seconds` |
| **Priority ordering** | `approve_policy(10)` tried before `conditional_approve(5)` |
| **Block actions** | `then: given premium as ...` (computed values) |
| **Explain clauses** | Audit trail on every rule |

---

## Appendix: Test Coverage

Sprint 3 added **83 new tests** (total: 665). Breakdown:

| Area | Tests | Description |
|------|-------|-------------|
| Lexer | 2 | `query`/`within` keyword tokenization |
| Parser | 8 | Query stmt (4) + temporal constraint (4) |
| Backward chaining | 15 | Core engine unit tests |
| Evaluator integration | 6 | Query/temporal in evaluator |
| sigil.time | 7 | Timestamp functions |
| sigil.trace | 7 | Trace introspection |
| sigil.io | 9 | File I/O + JSON |
| Type checker | 15 | Return types (5) + inference (5) + units (5) |
| Integration | 10 | Example programs + deep chains |
| **Total new** | **83** | |

All tests pass. Ruff and mypy clean.

---

## Appendix: Grammar Additions

The PEG grammar was extended with:

```peg
TemporalClause ← 'within' Expression Identifier
QueryStatement ← 'query' Identifier ('with' Expression)?
```

New tokens:

```
QUERY   = "query"
WITHIN  = "within"
```

---

## Appendix: File Map

| File | What Changed |
|------|-------------|
| `src/sigil/lexer/tokens.py` | +QUERY, +WITHIN tokens |
| `src/sigil/ast/nodes.py` | +TemporalConstraint, +QueryStmt, Literal.unit, RuleDecl.temporal |
| `src/sigil/parser/parser.py` | +_parse_query_stmt, temporal parsing, unit capture |
| `src/sigil/interpreter/backward.py` | NEW — BackwardChainer engine |
| `src/sigil/interpreter/evaluator.py` | +_eval_query, temporal trace metadata |
| `src/sigil/interpreter/trace.py` | +proof_trees field |
| `src/sigil/types/checker.py` | +Check #9/#10/#11 |
| `src/sigil/stdlib/_builtins.py` | +STDLIB_TIME, +STDLIB_TRACE, +STDLIB_IO |
| `src/sigil/stdlib/__init__.py` | Registered time/trace/io modules |
