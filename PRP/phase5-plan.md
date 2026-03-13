# Phase 5 Plan: Formal Verification + Bytecode VM + WASM Target

> **Date**: 2026-03-13 (revised v2)
> **Scope**: Phase 5.5 (Verification) → 5.1 (Bytecode VM) → 5.3 (WASM)
> **Prerequisite**: Phase 4 complete (1000 tests, `sigil code` agent shipped)
> **Solver**: BDD-based via `biodivine-lib-bdd` (NOT Z3 — see Decision Record)

---

## Overview

Three features in dependency order — each one makes the next easier:

```
Phase 5.5: Formal Verification  → Prove rules are correct (Rust-native constraint solver)
Phase 5.1: Bytecode VM          → 10-100x perf (Rust compiler + VM)
Phase 5.3: WASM Target          → Run Sigil anywhere (VM already in Rust — just add wasm-bindgen)
```

### Why This Order?

The Bytecode VM is the linchpin. Without it, WASM requires porting the 1500-line
tree-walking evaluator to Rust — a painful, throwaway effort since you'd want a VM
later anyway. With the VM built first:

```
Without VM (old plan):
  Python evaluator.py  →  port line-by-line to Rust  →  compile to WASM
  Result: tree-walking in WASM (slow, large binary, thrown away later)

With VM (revised plan):
  Python evaluator.py  →  Rust bytecode compiler + VM  →  compile to WASM
  Result: bytecode VM in WASM (fast, tiny dispatch loop, permanent)
```

| Aspect | Port tree-walker | VM first, then WASM |
|--------|-----------------|---------------------|
| WASM binary size | Large (recursive AST walking) | Small (tight dispatch loop) |
| Runtime performance | ~5-10x over Python | ~50-100x over Python |
| Code reuse | Throwaway | VM serves PyO3 AND WASM |
| Evaluator port effort | ~1800 lines of branching | ~800 line VM + ~500 line compiler |
| Architecture | Dead end | Foundation for JIT later |

---

## Part A: Formal Verification (Phase 5.5) — BDD-Based, Rust-Native

### Problem

Sigil programs make decisions. Wrong decisions have real consequences (loans denied
incorrectly, medical triage errors, compliance failures). Users need confidence that:
1. Every possible input produces a decision (no gaps)
2. Rules don't contradict each other
3. Rules that should fire actually can fire
4. Forward chaining terminates

### Why BDD-Based (Not Z3, Not Custom Interval Solver)

We evaluated three approaches:

| Aspect | Z3 (C++ SMT) | Custom Interval Solver | BDD (`biodivine-lib-bdd`) |
|--------|--------------|----------------------|---------------------------|
| Dependencies | 200MB C++ binary | Zero | 1 Rust crate (~small) |
| WASM | Cannot compile | Yes | Yes (pure Rust) |
| Maturity | 15+ years, battle-tested | Brand new (us) | Mature (68K downloads, active) |
| Boolean logic | Excellent | Must reinvent | Native — AND/OR/NOT are free |
| Numeric intervals | Excellent | Good | Via threshold discretization |
| Enum equality | Excellent | Must implement | Native (boolean variables) |
| Counterexamples | Built-in | Must implement | Built-in (satisfying assignment) |
| Completeness check | Query-based | Custom formula | `BDD == TRUE` check (one line) |
| Maintenance | External team | Us forever | External team |
| Future upgrade | N/A | Hard to extend | Add OxiZ for SMT when it matures |

**Why BDD wins:**

1. **40 years of proven use** — BDDs have been the standard for rule/circuit
   completeness and conflict checking since Bryant (1986). Hardware verification,
   model checking, and rule engines all use BDDs for exactly this class of problems.

2. **Boolean operations are free** — AND, OR, NOT, complement, equivalence, and
   satisfiability are native BDD operations. A custom interval solver must reinvent
   all of these; a BDD library gives them for free with optimal caching.

3. **Counterexamples are free** — Finding a satisfying assignment (witness) is a
   single BDD traversal. No custom witness-finding algorithm needed.

4. **biodivine-lib-bdd is production-ready** — Pure Rust, 68K crates.io downloads,
   actively maintained (last update Feb 2026), thread-safe, well-documented.

5. **Threshold discretization is sound** — Sigil rules test a finite number of
   comparison points. Converting these to boolean predicates is a standard technique
   that's mathematically equivalent to interval analysis.

### Strategy

Encode Sigil rule conditions as Binary Decision Diagrams (BDDs) using threshold
discretization for numeric comparisons. Use BDD operations for all four verification
checks.

```
RuleDecl AST → Threshold Extraction → Boolean Encoding → BDD → Verification
```

### How Threshold Discretization Works

Sigil rules compare variables against specific numeric values. We extract all these
thresholds and create boolean predicates:

```
Given rules:
  rule r1: when age exceeds 25 and income exceeds 50000
  rule r2: when age is below 18
  rule r3: when age is between 18 and 65

Step 1: Extract thresholds per variable
  age:    {18, 25, 65}
  income: {50000}

Step 2: Create ordered boolean predicates
  age_le_18   (age ≤ 18)
  age_le_25   (age ≤ 25)
  age_le_65   (age ≤ 65)
  income_le_50000 (income ≤ 50000)

Step 3: Add ordering constraints (monotonicity)
  age_le_18 → age_le_25       (if age ≤ 18 then age ≤ 25)
  age_le_25 → age_le_65       (if age ≤ 25 then age ≤ 65)

Step 4: Encode conditions as boolean formulas
  "age exceeds 25"         → NOT(age_le_25)
  "age is below 18"        → age_le_18   (note: below = strictly less)
  "age is between 18 and 65" → NOT(age_le_18) AND age_le_65
  "income exceeds 50000"   → NOT(income_le_50000)

Step 5: Build BDD for each rule
  r1_bdd = NOT(age_le_25) AND NOT(income_le_50000)
  r2_bdd = age_le_18
  r3_bdd = NOT(age_le_18) AND age_le_65

Step 6: Verification checks (BDD operations)
  coverage_bdd = r1_bdd OR r2_bdd OR r3_bdd
  completeness: coverage_bdd AND ordering_constraints == ordering_constraints?
  dead_rule:    ri_bdd AND ordering_constraints == FALSE?
  conflict:     ri_bdd AND rj_bdd AND ordering_constraints != FALSE?
```

**Why this is sound:** The rules only distinguish inputs at the extracted threshold
values. Between any two consecutive thresholds, all inputs behave identically
(same rules fire). So discretizing at thresholds captures all distinct behaviors.

### Condition → Boolean Encoding Table

| Sigil Condition | Boolean Encoding | BDD Variables Used |
|----------------|------------------|--------------------|
| `x exceeds 100` | `NOT(x_le_100)` | `x_le_100` |
| `x is below 50` | `x_le_49` (strict) | `x_le_49` |
| `x is between 10 and 90` | `NOT(x_le_9) AND x_le_90` | `x_le_9`, `x_le_90` |
| `x is at least 18` | `NOT(x_le_17)` | `x_le_17` |
| `x is at most 65` | `x_le_65` | `x_le_65` |
| `x is :active` | `x_eq_active` | `x_eq_active` |
| `x is :high` | `x_eq_high` | `x_eq_high` |
| `x is true` | `x_true` | `x_true` |
| `x is false` | `NOT(x_true)` | `x_true` |
| `x in [1, 2, 3]` | `x_eq_1 OR x_eq_2 OR x_eq_3` | `x_eq_1`, `x_eq_2`, `x_eq_3` |
| `not <cond>` | `NOT(cond_bdd)` | (same as inner) |
| `cond1 and cond2` | `cond1_bdd AND cond2_bdd` | (union) |
| `cond1 or cond2` | `cond1_bdd OR cond2_bdd` | (union) |
| `x is assigned` | `x_assigned` (auxiliary bool) | `x_assigned` |
| `x is empty` | `x_empty` (auxiliary bool) | `x_empty` |

**Symbol encoding:** Each symbol type gets one boolean variable per variant. For
`type Status is one of: low, medium, high`, we create `status_eq_low`,
`status_eq_medium`, `status_eq_high` with a mutual-exclusion constraint
(exactly one is true).

### Architecture

```
src/sigil_core/src/verifier/       ← Rust module in sigil_core
├── mod.rs                          ← verify_program(), VerificationReport (~100 lines)
├── discretize.rs                   ← Threshold extraction from AST conditions (~200 lines)
├── encoder.rs                      ← AST Condition → BDD encoding (~300 lines)
├── ordering.rs                     ← Monotonicity + mutual-exclusion constraints (~150 lines)
├── completeness.rs                 ← Coverage BDD check + gap witness (~150 lines)
├── conflicts.rs                    ← Pairwise BDD intersection + action analysis (~200 lines)
├── dead_rules.rs                   ← Per-rule satisfiability BDD check (~100 lines)
├── termination.rs                  ← Dependency graph cycle detection (~100 lines)
├── witness.rs                      ← BDD satisfying assignment → human-readable input (~150 lines)
└── report.rs                       ← VerificationReport struct + formatters (~150 lines)

src/sigil/verifier/                 ← Python wrapper via PyO3
├── __init__.py                     ← export verify_program(), VerificationReport
└── wrapper.py                      ← Thin wrapper calling sigil_core.verify() (~100 lines)

tests/verifier/                     ← Rust tests + Python integration tests
├── Rust: ~80 unit tests            ← discretize, encoder, ordering, checkers, witness
└── Python: ~45 integration tests   ← full programs, CLI, example validation
```

### Core Implementation

```rust
use biodivine_lib_bdd::{Bdd, BddVariableSet, BddVariable};

/// Context for encoding a rule set into BDDs.
pub struct VerifierContext {
    /// BDD variable set (all boolean predicates)
    vars: BddVariableSet,
    /// Mapping: variable name → list of threshold predicates
    thresholds: HashMap<String, Vec<(BddVariable, f64)>>,
    /// Mapping: variable name → symbol enum predicates
    symbols: HashMap<String, Vec<(BddVariable, String)>>,
    /// Monotonicity + mutual-exclusion constraints
    ordering_bdd: Bdd,
}

impl VerifierContext {
    /// Build context by scanning all rule conditions for thresholds.
    pub fn from_rules(rules: &[RuleInfo]) -> Self { ... }

    /// Encode a single Sigil condition as a BDD.
    pub fn encode_condition(&self, cond: &ConditionInfo) -> Bdd { ... }

    /// Encode an entire rule (conjunction of all conditions).
    pub fn encode_rule(&self, rule: &RuleInfo) -> Bdd {
        let mut bdd = self.vars.mk_true();
        for cond in &rule.conditions {
            bdd = bdd.and(&self.encode_condition(cond));
        }
        // Intersect with ordering constraints for soundness
        bdd.and(&self.ordering_bdd)
    }
}

/// Check completeness: does the union of all rules cover all valid inputs?
pub fn check_completeness(ctx: &VerifierContext, rules: &[Bdd]) -> CompletenessResult {
    let mut coverage = ctx.vars.mk_false();
    for rule_bdd in rules {
        coverage = coverage.or(rule_bdd);
    }
    // Complete iff coverage ≡ ordering_constraints (all valid inputs are covered)
    if coverage == ctx.ordering_bdd {
        CompletenessResult::Complete
    } else {
        // Find a valid input NOT in coverage
        let gap = ctx.ordering_bdd.and_not(&coverage);
        let witness = gap.first_valuation();  // BDD gives this for free
        CompletenessResult::Incomplete {
            counterexample: ctx.decode_witness(witness),
        }
    }
}

/// Check for dead rules: is any rule's BDD unsatisfiable?
pub fn check_dead_rules(ctx: &VerifierContext, rules: &[Bdd]) -> Vec<DeadRule> {
    rules.iter().enumerate()
        .filter(|(_, bdd)| bdd.is_false())
        .map(|(i, _)| DeadRule { rule_index: i })
        .collect()
}

/// Check for conflicts: do any two rules with different actions overlap?
pub fn check_conflicts(ctx: &VerifierContext, rules: &[RuleBdd]) -> Vec<Conflict> {
    let mut conflicts = Vec::new();
    for i in 0..rules.len() {
        for j in (i+1)..rules.len() {
            let overlap = rules[i].bdd.and(&rules[j].bdd);
            if !overlap.is_false() {
                let witness = overlap.first_valuation();
                conflicts.push(Conflict {
                    rule_a: i, rule_b: j,
                    witness: ctx.decode_witness(witness),
                    priority_resolves: rules[i].priority != rules[j].priority,
                    action_conflict: rules[i].action != rules[j].action,
                });
            }
        }
    }
    conflicts
}
```

### The Four Checkers

#### Checker 1: Completeness — "All inputs covered?"

```
coverage_bdd = rule1_bdd OR rule2_bdd OR ... OR ruleN_bdd
complete iff coverage_bdd ⊇ ordering_constraints
gap = ordering_constraints AND NOT(coverage_bdd)
counterexample = gap.first_valuation()
```

One BDD union, one comparison, one traversal. Done.

#### Checker 2: Conflicts — "Rules contradict?"

```
for each pair (ri, rj) where ri.action != rj.action:
    overlap = ri_bdd AND rj_bdd
    if overlap != FALSE:
        witness = overlap.first_valuation()
        report conflict with counterexample
```

Pairwise BDD intersection. O(n^2) rule pairs, but BDD operations are fast.

#### Checker 3: Dead Rules — "Rule can ever fire?"

```
for each rule ri:
    if ri_bdd == FALSE:
        report dead rule
```

Single check per rule. The BDD construction already intersects with ordering
constraints, so unsatisfiable conditions (x > 100 AND x < 50) produce FALSE.

#### Checker 4: Termination — "Forward chaining halts?"

Graph-based analysis (no BDD needed):
1. Build dependency graph: rule → variables it reads, variables it writes
2. Detect cycles in the write→read graph
3. Flag oscillating assignments (rule A sets x=true, rule B sets x=false)

### CLI Integration

```bash
# Verify a program
sigil verify program.sigil

# Verify with specific checks
sigil verify program.sigil --check completeness
sigil verify program.sigil --check conflicts
sigil verify program.sigil --check dead-rules
sigil verify program.sigil --check termination

# Output as JSON (for CI integration)
sigil verify program.sigil --format json

# Verify all .sigil files in a directory
sigil verify examples/rules/
```

**Example output:**
```
$ sigil verify examples/rules/loan_eligibility.sigil

Sigil Verification Report
═════════════════════════

Completeness ✓
  All input combinations covered by at least one rule.

Conflicts ✓
  No contradictory rules found.
  2 overlapping pairs (resolved by priority):
    • age_check (p=0) ∩ full_eligibility (p=10)
    • credit_check (p=0) ∩ full_eligibility (p=10)

Dead Rules ✓
  No unreachable rules found.

Termination ✓
  No cyclic dependencies detected.
  Max chain depth: 2 (age_check → full_eligibility → approve_decision)

Result: PASS (0 errors, 2 info)
```

### Verification Sprints

**Sprint 5.5.1: BDD Engine + Threshold Discretization** (Week 1)
- [ ] `discretize.rs` — extract thresholds from AST conditions per variable
- [ ] `ordering.rs` — build monotonicity + mutual-exclusion BDD constraints
- [ ] `encoder.rs` — translate all 12 AST condition types to BDD formulas
- [ ] Symbol → boolean variable mapping with mutual exclusion
- [ ] `witness.rs` — BDD satisfying assignment → human-readable input values
- [ ] 40+ Rust unit tests (discretization, encoding, ordering, witness decoding)

**Sprint 5.5.2: Completeness + Dead Rules** (Week 2)
- [ ] `completeness.rs` — coverage BDD union, gap detection, counterexample gen
- [ ] `dead_rules.rs` — per-rule satisfiability check against ordering BDD
- [ ] `report.rs` — VerificationReport struct + text/JSON formatters
- [ ] 35+ tests (20 completeness, 15 dead rules)

**Sprint 5.5.3: Conflicts + Termination** (Week 3)
- [ ] `conflicts.rs` — pairwise BDD intersection, subsumption, action conflict
- [ ] `termination.rs` — write/read dependency graph, cycle detection
- [ ] PyO3 wrapper: `verify_program()` Python function
- [ ] 35+ tests (25 conflicts, 10 termination)

**Sprint 5.5.4: Integration + CLI** (Week 4)
- [ ] `sigil verify` CLI command with --check, --format flags
- [ ] Python integration tests against example .sigil files
- [ ] JSON output format for CI
- [ ] Documentation
- [ ] 15+ integration tests

### Dependencies

```toml
# Cargo.toml addition
[dependencies]
biodivine-lib-bdd = "0.6"    # Pure Rust BDD library (WASM-compatible)
```

One small, pure-Rust dependency. Ships with `sigil_core`, compiles to WASM.

```bash
# Just works — no extra install needed
sigil verify program.sigil
```

### Verification Performance Targets

BDDs are fast for typical rule sets. Variable ordering heuristics keep BDD size small.

| Metric | Target | Notes |
|--------|--------|-------|
| 10 rules, all checks | < 50ms | Small BDDs, fast operations |
| 50 rules, all checks | < 200ms | BDD caching helps repeated subexpressions |
| 100 rules, all checks | < 1 second | Pairwise conflict check dominates |
| 200+ rules | < 5 seconds | BDD variable ordering becomes critical |
| Counterexample generation | < 1ms per case | Single BDD traversal |
| WASM verification | Same performance | Same Rust code, same BDD library |

### BDD Variable Ordering Strategy

BDD size is exponentially sensitive to variable ordering. For Sigil's typical
patterns (rules group conditions by the same variables), we use:

1. **Group by variable** — all thresholds for `age` adjacent, then `income`, etc.
2. **Within a variable, order by threshold value** — `age_le_18` before `age_le_25`
3. **Heuristic: most-constrained variable first** — variables appearing in the most
   rules get lower BDD indices (closer to root = more sharing)

This ordering keeps BDD sizes small for rule sets with independent variable groups
(the common case in Sigil).

### Verification Risks

| Risk | Mitigation |
|------|-----------|
| BDD blowup on many variables (>50 thresholds) | Variable ordering heuristics; partition into independent variable groups |
| Coupled constraints (x + y > 100) | Cannot encode directly; warn as "partially verified" |
| Quantified conditions (any/all over lists) | Bounded enumeration for small lists; mark as "approximate" |
| String conditions (starts_with, contains) | Cannot verify; mark as "unverifiable, skipped" |
| Neural declarations | Skip neural-dependent rules; report as "unverifiable" |
| Users expect soundness guarantees | Sound within discretized domain; document limitations |

### Future: SMT Upgrade Path (OxiZ)

OxiZ (v0.1.3, pure Rust SMT solver) is tracking toward Z3 compatibility. When it
matures (target: v1.0+), we can add it as an optional backend for:
- Coupled multi-variable constraints (x + y > 100)
- Complex arithmetic in compute functions
- Deeper verification of expression evaluation

The encoder interface is designed to support this: `encode_rule()` produces a
representation that can target either BDD or SMT backends.

---

## Part B: Bytecode VM (Phase 5.1)

### Problem

The tree-walking interpreter evaluates the AST directly — every node traversal
involves Python `isinstance()` checks, dict lookups, and function call overhead.
This is ~100-1000x slower than native execution. The Rust core helps for pattern
matching and constraint solving, but the evaluator loop itself is the bottleneck.

### Strategy

Build a two-stage execution pipeline:

```
                    Compile Time                    Runtime
                    ──────────                      ───────
AST (from parser) → Bytecode Compiler (Rust) → Instruction Stream
                                                       │
                                                       ▼
                                               Bytecode VM (Rust)
                                                       │
                                                       ▼
                                               Result + Trace
```

The compiler runs once per program. The VM executes the instruction stream
repeatedly (for different inputs) at near-native speed.

### Why a Stack Machine?

Stack-based VMs are simpler to implement, compile to, and port to WASM than
register-based VMs. Production languages that use stack VMs: Python (CPython),
Java (JVM), WebAssembly itself, Lua 4, .NET CLR.

```
Sigil source:          Bytecode:              Stack trace:
  given x as 3 + 4      PUSH_INT 3             []
                         PUSH_INT 4             [3]
                         ADD                    [3, 4]
                         STORE "x"              [7]
                                                []
```

### Instruction Set

~40 instructions, designed for Sigil's semantics:

```rust
#[derive(Debug, Clone, serde::Serialize)]
pub enum Opcode {
    // --- Stack Operations ---
    PushInt(i64),              // Push integer literal
    PushFloat(f64),            // Push float literal
    PushString(StringIdx),     // Push string (index into string pool)
    PushSymbol(StringIdx),     // Push :symbol
    PushBool(bool),            // Push true/false
    PushNone,                  // Push none
    PushList(u16),             // Pop N items, push as list
    PushRecord(u16),           // Pop N key-value pairs, push as record
    Pop,                       // Discard top of stack
    Dup,                       // Duplicate top of stack

    // --- Arithmetic ---
    Add,                       // a + b
    Sub,                       // a - b
    Mul,                       // a * b
    Div,                       // a / b
    Neg,                       // -a
    Mod,                       // a % b

    // --- Comparison ---
    Eq,                        // a == b
    Neq,                       // a != b
    Gt,                        // a > b    (used in compute bodies)
    Lt,                        // a < b
    Gte,                       // a >= b
    Lte,                       // a <= b

    // --- Logic ---
    Not,                       // !a
    And,                       // a && b  (short-circuit via Jump)
    Or,                        // a || b  (short-circuit via Jump)

    // --- Variables ---
    Load(StringIdx),           // Push variable value onto stack
    Store(StringIdx),          // Pop stack, bind to variable
    LoadField(StringIdx),      // Pop record, push field value
    LoadInput(StringIdx),      // Load from input data

    // --- Control Flow ---
    Jump(u32),                 // Unconditional jump to instruction offset
    JumpIfFalse(u32),          // Pop condition, jump if false
    JumpIfTrue(u32),           // Pop condition, jump if true

    // --- Functions ---
    Call(StringIdx, u8),       // Call function by name with N args
    Return,                    // Return from function (pop frame)
    CallBuiltin(BuiltinId, u8),// Call stdlib function directly

    // --- Rule Engine ---
    EvalCondition(CondOp),     // Evaluate a Sigil condition (exceeds, below, between, etc.)
    FireRule(RuleIdx),         // Mark rule as fired, execute action block
    CheckFired(RuleIdx),       // Push true if rule already fired

    // --- Trace ---
    TraceBegin(StringIdx),     // Start trace for rule/compute
    TraceEnd,                  // End trace, record duration
    TracePrint,                // Pop value, add to output_lines

    // --- Special ---
    Halt,                      // Stop execution
}

/// Sigil-specific condition operators (used by EvalCondition)
#[derive(Debug, Clone)]
pub enum CondOp {
    Exceeds,                   // a exceeds b
    Below,                     // a is below b
    Between,                   // a is between b and c  (pops 3 values)
    IsSymbol,                  // a is :symbol
    IsAssigned,                // a is assigned (not _UNBOUND)
    IsEmpty,                   // collection is empty
    Contains,                  // collection contains element
    InList,                    // element in [list]
    HasCount,                  // collection has count N
}
```

### Architecture

```
src/sigil_core/src/
├── lib.rs                     ← existing (add vm module)
├── values.rs                  ← existing (extend for bytecode values)
├── matcher.rs                 ← existing (pattern matcher)
├── solver.rs                  ← existing (constraint solver)
├── trace.rs                   ← existing (trace serialization)
│
├── compiler/                  ← NEW: AST → bytecode
│   ├── mod.rs                 ← Compiler entry point
│   ├── opcodes.rs             ← Opcode enum (~40 instructions)
│   ├── chunk.rs               ← Chunk (instruction stream + constants pool)
│   ├── emit.rs                ← Expression/statement/rule compilation
│   └── string_pool.rs         ← Interned string table
│
└── vm/                        ← NEW: bytecode executor
    ├── mod.rs                 ← VM entry point
    ├── engine.rs              ← Main dispatch loop
    ├── stack.rs               ← Value stack
    ├── frames.rs              ← Call frames (compute function calls)
    ├── rules.rs               ← Forward chaining loop (bytecode-level)
    ├── backward.rs            ← Backward chaining (query)
    └── stdlib.rs              ← Built-in function dispatch table
```

**Python-side (thin wrapper):**

```
src/sigil/vm/
├── __init__.py                ← export compile_and_run()
└── runner.py                  ← Python wrapper for Rust VM via PyO3
```

### Compilation Examples

**Constants + Rules:**
```sigil
define THRESHOLD as 100

rule check with priority 5:
  when value exceeds THRESHOLD
  then trigger alert
  explain "Value exceeded"
```

Compiles to:
```
; Constants
0000  PUSH_INT     100
0001  STORE        "THRESHOLD"

; Rule "check" (priority 5)
; --- condition: value exceeds THRESHOLD ---
0002  TRACE_BEGIN   "check"
0003  LOAD          "value"
0004  LOAD          "THRESHOLD"
0005  EVAL_COND     Exceeds
0006  JUMP_IF_FALSE 0011        ; skip to trace_end if condition false

; --- action: trigger alert ---
0007  PUSH_SYMBOL   "trigger"
0008  PUSH_SYMBOL   "alert"
0009  FIRE_RULE      0          ; mark rule 0 as fired

; --- explain ---
0010  PUSH_STRING   "Value exceeded"

0011  TRACE_END
0012  HALT
```

**Compute functions:**
```sigil
compute add from a: Number, b: Number returns Number:
  return a + b
```

Compiles to:
```
; Function "add" (2 params)
add:
  0000  LOAD   "a"
  0001  LOAD   "b"
  0002  ADD
  0003  RETURN
```

**Forward chaining loop:**

The compiler emits the forward chaining loop as a bytecode sequence:

```
; Forward chaining (max 100 iterations)
LOOP_START:
  ; For each rule (sorted by priority, highest first):
  CHECK_FIRED  rule_0          ; skip if already fired
  JUMP_IF_TRUE NEXT_RULE_0
  <rule_0 condition bytecode>
  JUMP_IF_FALSE NEXT_RULE_0
  <rule_0 action bytecode>
  FIRE_RULE rule_0
  JUMP LOOP_START              ; restart — new fact may trigger other rules

  NEXT_RULE_0:
  CHECK_FIRED rule_1
  ...

  ; If no rule fired this iteration → fixed point reached
  HALT
```

### Dual-Target Build

The VM crate compiles to both PyO3 (Python extension) and WASM:

```toml
# Cargo.toml
[lib]
crate-type = ["cdylib", "rlib"]  # cdylib for PyO3/WASM, rlib for Rust tests

[features]
default = ["pyo3"]
pyo3 = ["dep:pyo3"]
wasm = ["dep:wasm-bindgen"]

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[dependencies.pyo3]
version = "0.25"
optional = true

[dependencies.wasm-bindgen]
version = "0.2"
optional = true
```

```rust
// lib.rs — conditional compilation
#[cfg(feature = "pyo3")]
mod python_bindings {
    use pyo3::prelude::*;

    #[pyfunction]
    fn compile_and_run(source: &str, input_json: &str) -> PyResult<String> {
        // lexer → parser → compiler → VM → result JSON
    }
}

#[cfg(feature = "wasm")]
mod wasm_bindings {
    use wasm_bindgen::prelude::*;

    #[wasm_bindgen]
    pub fn run(source: &str, input_json: &str) -> String {
        // Same pipeline — lexer → parser → compiler → VM → result JSON
    }
}
```

Build commands:
```bash
maturin develop                          # PyO3 build (Python extension)
wasm-pack build --features wasm          # WASM build (browser/edge)
```

### Integration with Existing Python Interpreter

The VM is opt-in. The tree-walking interpreter remains the default for development
and debugging. The VM is used for production execution.

```python
# cli.py
def _cmd_run(file, *, trace=False, use_vm=False):
    if use_vm:
        from sigil.vm import compile_and_run
        result = compile_and_run(source, input_json)
    else:
        # existing tree-walking path
        evaluator = Evaluator()
        result, trace = evaluator.eval_program(program, input_data)
```

```bash
sigil run program.sigil              # tree-walking (default, debuggable)
sigil run program.sigil --vm         # bytecode VM (fast, production)
```

### VM Sprints

**Sprint 5.1.1: Instruction Set + Compiler Foundation** (Week 5)
- [ ] `opcodes.rs` — Opcode enum with ~40 instructions
- [ ] `chunk.rs` — Chunk struct (instructions + constant pool + string pool)
- [ ] `string_pool.rs` — Interned string table
- [ ] `emit.rs` — Compile expressions: literals, binary ops, unary ops, identifiers
- [ ] `emit.rs` — Compile statements: given, return, if/else, for
- [ ] 40+ compiler unit tests

**Sprint 5.1.2: VM Engine** (Week 6)
- [ ] `stack.rs` — Value stack with fixed capacity (1024)
- [ ] `frames.rs` — Call frames for compute function calls
- [ ] `engine.rs` — Main dispatch loop (`match opcode { ... }`)
- [ ] `stdlib.rs` — Built-in function dispatch (math, text, list, logic)
- [ ] Expression evaluation end-to-end (compile → execute → result)
- [ ] 50+ VM execution tests

**Sprint 5.1.3: Rule Engine in Bytecode** (Week 7)
- [ ] Compile rules: conditions → bytecode, actions → bytecode
- [ ] `rules.rs` — Forward chaining loop in bytecode
- [ ] `backward.rs` — Backward chaining (query) via bytecode
- [ ] `fired_rules` tracking, priority sorting
- [ ] Trace generation from bytecode execution
- [ ] 40+ rule engine tests

**Sprint 5.1.4: Integration + Benchmarks** (Week 8)
- [ ] PyO3 wrapper (`compile_and_run()` Python function)
- [ ] `sigil run --vm` CLI flag
- [ ] Port existing interpreter test suite to VM execution
- [ ] Benchmarks: tree-walking vs bytecode VM
- [ ] Dual-target build verification (PyO3 + WASM feature flags)
- [ ] 30+ integration tests + benchmark suite

### VM Performance Targets

| Metric | Tree-Walking | Bytecode VM | Speedup |
|--------|-------------|-------------|---------|
| Simple rule (1 condition) | ~0.5ms | ~0.005ms | ~100x |
| 10 rules, forward chaining | ~5ms | ~0.05ms | ~100x |
| 100 rules, forward chaining | ~80ms | ~1ms | ~80x |
| Compute function (fibonacci) | ~50ms | ~0.5ms | ~100x |
| Full loan eligibility | ~20ms | ~0.2ms | ~100x |

### VM Risks

| Risk | Mitigation |
|------|-----------|
| Instruction set design wrong | Start minimal (~30 opcodes), extend as needed. Tree-walker remains fallback |
| Debugging bytecode is hard | Emit source maps (instruction → source line). Keep tree-walker for dev |
| Forward chaining semantics change | Test suite must pass identically on both tree-walker and VM |
| Backward chaining complexity | Can defer backward chaining to sprint 5.1.4 if needed |
| String interpolation | Pre-resolve at compile time into concatenation instructions |

---

## Part C: WASM Target (Phase 5.3)

### Problem

Sigil currently requires Python to run. This blocks:
- Browser-based rule editors / dashboards
- Edge deployment (Cloudflare Workers, Deno Deploy)
- Embedding Sigil in Node.js / TypeScript applications
- Lightweight serverless functions without Python runtime

### Why WASM Is Now Easy

With the Bytecode VM already in Rust, the WASM target needs only:

1. **Port lexer + parser to Rust** — The compiler and VM are already Rust
2. **Add `wasm-bindgen` exports** — Same Rust code, different bindings
3. **Embed stdlib** — Already done for the VM

```
What's already Rust (from Phase 5.1):        What still needs porting:
  ✓ Bytecode compiler                          ✗ Lexer (lexer.py → Rust)
  ✓ VM engine                                  ✗ Parser (parser.py → Rust)
  ✓ Stdlib dispatch                            ✗ Type checker (checker.py → Rust)
  ✓ Forward + backward chaining
  ✓ Trace serialization
  ✓ Pattern matcher
  ✓ Constraint solver
  ✓ Value types
```

The evaluator.py port — the hardest part — is replaced by the VM.

### Architecture

```
sigil_core/src/                    ← Extended (NOT a new crate)
├── lib.rs                         ← Add wasm-bindgen exports
├── lexer/                         ← NEW: Port from Python
│   ├── mod.rs
│   ├── tokens.rs                  ← TokenType enum, Token struct
│   └── scanner.rs                 ← tokenize() with indentation engine
├── parser/                        ← NEW: Port from Python
│   ├── mod.rs
│   ├── ast.rs                     ← AST nodes as Rust enums
│   └── parser.rs                  ← Recursive descent parser
├── checker/                       ← NEW: Port from Python
│   └── mod.rs                     ← Type checker (11 checks)
├── compiler/                      ← FROM PHASE 5.1 (already done)
│   └── ...
├── vm/                            ← FROM PHASE 5.1 (already done)
│   └── ...
├── matcher.rs                     ← EXISTING
├── solver.rs                      ← EXISTING
├── trace.rs                       ← EXISTING
└── values.rs                      ← EXISTING
```

### JavaScript/TypeScript API

```typescript
// npm install @sigil-lang/wasm
import init, { SigilRuntime } from '@sigil-lang/wasm';

await init();
const runtime = new SigilRuntime();

// Full pipeline: lex → parse → compile → VM execute
const result = runtime.run(`
  define THRESHOLD as 100
  rule check:
    when value exceeds THRESHOLD
    then trigger alert
  main:
    given value as 150
    print(value)
`, '{"value": 150}');

console.log(result.output);    // ["150"]
console.log(result.trace);     // { rule_traces: [...], duration_ms: 0.2 }

// Precompile for repeated execution with different inputs
const program = runtime.compile(sourceCode);
const r1 = runtime.execute(program, '{"value": 50}');
const r2 = runtime.execute(program, '{"value": 200}');

// Validate only
const diagnostics = runtime.check(sourceCode);

// Format
const formatted = runtime.format(sourceCode);
```

Key difference from the old plan: `compile()` + `execute()` separation enables
precompilation — compile once, run many times with different inputs. This is the
killer feature for edge deployment.

### Deployment Targets

**Browser (ES Module):**
```bash
wasm-pack build --features wasm --target bundler
```
```html
<script type="module">
  import init, { SigilRuntime } from './sigil_wasm.js';
  const runtime = await init().then(() => new SigilRuntime());
  const result = runtime.run(source, inputJson);
  document.getElementById('output').textContent = result.output.join('\n');
</script>
```

**Cloudflare Workers:**
```typescript
import { SigilRuntime } from '@sigil-lang/wasm';

// Precompile at startup (cold start optimization)
const runtime = new SigilRuntime();
const program = runtime.compile(RULES_SOURCE);

export default {
  async fetch(request: Request): Promise<Response> {
    const input = await request.json();
    const result = runtime.execute(program, JSON.stringify(input));
    return Response.json({ output: result.output, trace: result.trace });
  }
};
```

**Deno / Node.js:**
```bash
wasm-pack build --features wasm --target nodejs
```

### What Gets Ported vs What Gets Dropped

| Component | Status After VM | WASM Action | Notes |
|-----------|----------------|-------------|-------|
| Lexer | Python | **Port to Rust** | ~500 lines Rust |
| Parser | Python | **Port to Rust** | ~2000 lines Rust |
| Compiler | Rust (Phase 5.1) | Already done | Zero work |
| VM | Rust (Phase 5.1) | Already done | Zero work |
| Type Checker | Python | **Port to Rust** | ~600 lines Rust |
| Stdlib | Rust (Phase 5.1) | Already done | Embedded in VM |
| Trace | Rust (existing) | Already done | `sigil_core::trace` |
| Matcher | Rust (existing) | Already done | `sigil_core::matcher` |
| Solver | Rust (existing) | Already done | `sigil_core::solver` |
| Python FFI | Python | **Drop** | No Python in WASM; JS callbacks |
| Neural Bridge | Python | **Stub** | JS callback API for model calls |
| Module System | Python | Simplified | Embed stdlib; HTTP for user modules |
| Formatter | Python | **Port to Rust** | ~500 lines Rust |
| Agent | Python | **Drop** | Agent stays Python-side |

### WASM Sprints

**Sprint 5.3.1: Rust Lexer** (Week 9)
- [ ] `lexer/tokens.rs` — TokenType enum, Token struct, UNIT_SUFFIXES
- [ ] `lexer/scanner.rs` — tokenize() with indentation engine (INDENT/DEDENT)
- [ ] Keyword recognition, string interpolation, comment handling
- [ ] Unit suffix consumption (`100 degrees` → NUMBER with unit)
- [ ] 91 tests (port from Python lexer tests)

**Sprint 5.3.2: Rust Parser** (Week 10)
- [ ] `parser/ast.rs` — AST nodes as Rust enums with serde derive
- [ ] `parser/parser.rs` — Recursive descent parser (all `parse_*` methods)
- [ ] Error recovery (panic-mode synchronization)
- [ ] 75+ tests (port from Python parser tests)

**Sprint 5.3.3: WASM Integration** (Week 11)
- [ ] `checker/mod.rs` — Type checker port (11 checks)
- [ ] wasm-bindgen exports: `run()`, `compile()`, `execute()`, `check()`, `format()`
- [ ] JSON marshaling for Values (input → Sigil, result → JSON)
- [ ] Error reporting (structured JSON errors)
- [ ] Full pipeline integration tests (source → lex → parse → compile → VM → result)
- [ ] 50+ integration tests

**Sprint 5.3.4: Packaging + Deployment** (Week 12)
- [ ] `wasm-pack build` for bundler, nodejs, web targets
- [ ] npm package: `@sigil-lang/wasm`
- [ ] Browser example: interactive Sigil playground
- [ ] Cloudflare Workers example with precompilation
- [ ] Deno example
- [ ] Documentation + README
- [ ] CI: build WASM in GitHub Actions
- [ ] 20+ deployment tests

### Size + Performance Targets

| Metric | Target |
|--------|--------|
| WASM binary (gzipped) | < 150KB (VM is tiny) |
| Full pipeline (100 rules) | < 10ms (vs 50ms tree-walker) |
| Precompiled execution (100 rules) | < 1ms |
| Lexer (1000 lines) | < 3ms |
| Parser (1000 lines) | < 5ms |
| Startup (init WASM) | < 30ms |
| Cold start (Cloudflare Workers) | < 50ms |

### WASM Risks

| Risk | Mitigation |
|------|-----------|
| Lexer indentation engine complexity | Port test-by-test; Python tests are the spec |
| Parser is 1500 lines Python | Mechanical port; recursive descent maps cleanly to Rust |
| String interpolation in Rust | Resolve at compile time into concat instructions |
| Module system without filesystem | Embed stdlib; provide JS callback for module loading |
| Neural bridge in WASM | Stub to JS Promise; call external APIs via WASM boundary |
| Binary size | VM dispatch loop is small; lexer/parser are the main contributors. Use wasm-opt |

---

## Implementation Schedule

```
Weeks 1-4:   Phase 5.5 — Formal Verification (BDD-based, biodivine-lib-bdd)
             ├── Week 1: BDD engine + threshold discretization + encoder
             ├── Week 2: Completeness + dead rules
             ├── Week 3: Conflicts + termination + PyO3 wrapper
             └── Week 4: CLI integration + polish

Weeks 5-8:   Phase 5.1 — Bytecode VM (Rust, extends sigil_core)
             ├── Week 5: Instruction set + compiler
             ├── Week 6: VM engine + stdlib dispatch
             ├── Week 7: Rule engine in bytecode
             └── Week 8: PyO3 integration + benchmarks

Weeks 9-12:  Phase 5.3 — WASM Target (Rust lexer/parser + wasm-bindgen)
             ├── Week 9:  Rust lexer
             ├── Week 10: Rust parser
             ├── Week 11: WASM integration + type checker
             └── Week 12: npm packaging + deployment examples
```

### Dependency Graph

```
Phase 5.5 (Verification)     Phase 5.1 (VM)          Phase 5.3 (WASM)
─────────────────────────     ──────────────          ────────────────
BDD engine (biodivine) ───────► (shared sigil_core)
Threshold discretizer          Compiler ──────────────► Rust lexer
Condition encoder              VM engine ─────────────► Rust parser
Completeness/conflicts         Rule engine bytecode ──► WASM integration
Termination checker            PyO3 wrapper ──────────► npm packaging
sigil verify CLI               sigil run --vm          @sigil-lang/wasm
```

Verification is independent of VM but shares the `sigil_core` crate — so verifier
compiles to WASM for free when WASM target ships (browser-side rule verification).
BDD library (biodivine-lib-bdd) is pure Rust, so no WASM issues.
VM must complete before WASM starts (WASM uses the VM for execution).

### Test Count Projections

| Feature | New Tests | Running Total |
|---------|-----------|---------------|
| Current | — | 1000 |
| Formal Verification | ~125 | ~1125 |
| Bytecode VM | ~160 | ~1285 |
| WASM Target | ~236 (ported + new) | ~1521 |

---

## Exit Criteria

### Formal Verification Done When:
- [ ] `sigil verify program.sigil` runs 4 checks and produces a report
- [ ] All 25 existing example .sigil files pass verification (or have documented exceptions)
- [ ] Counterexamples are actionable (show exact input values)
- [ ] 125+ verification tests passing
- [ ] Documentation with 3 worked examples

### Bytecode VM Done When:
- [ ] `sigil run program.sigil --vm` produces identical output to tree-walking
- [ ] All existing interpreter tests pass under VM execution
- [ ] Benchmarks show 50-100x speedup over tree-walking
- [ ] Dual-target Cargo.toml (PyO3 + WASM feature flags) builds cleanly
- [ ] 160+ VM tests passing

### WASM Target Done When:
- [ ] `wasm-pack build` produces working .wasm + .js bindings
- [ ] npm package `@sigil-lang/wasm` installable
- [ ] Precompile + execute API works (compile once, run many)
- [ ] Browser playground demo runs in Chrome/Firefox/Safari
- [ ] Cloudflare Workers example deploys and handles requests
- [ ] WASM binary < 150KB gzipped
- [ ] 236+ Rust tests passing (ported + new)

---

## Decision Record

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| VM before WASM | VM is the execution engine for WASM; porting tree-walker is throwaway work | Port tree-walker to Rust (thrown away), WASM without VM (slow) |
| Stack-based VM | Simpler than register VM; matches WASM model; proven in CPython/JVM/Lua | Register VM (more complex, marginally faster), direct WASM compilation |
| ~40 opcodes | Covers all Sigil semantics; `EvalCondition` keeps Sigil condition ops as first-class | Fewer opcodes (lose NL condition semantics), more opcodes (over-engineered) |
| Single crate, feature flags | One codebase serves Python (PyO3) and WASM (wasm-bindgen) | Separate crates (code duplication), WASM-only crate (no Python benefit) |
| Verification first | Simpler than VM, immediate user value, verifier gets WASM for free | VM first (delays immediate user value), all three in parallel (too complex) |
| BDD via biodivine-lib-bdd | 40 years proven for rule verification, pure Rust, WASM-safe, AND/OR/NOT/witness free, threshold discretization is sound for Sigil's finite comparison points | Z3 (200MB C++, no WASM), custom interval solver (reinvents boolean ops BDDs give free, maintenance burden), OxiZ (too immature at v0.1.3) |
| Precompile API in WASM | Compile once + execute many = edge performance; key differentiator | Run-only API (recompiles every request, 10x slower at edge) |
