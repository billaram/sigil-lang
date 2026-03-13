# Formal Verification for Rule-Based Systems

> A deep dive into what formal verification means for Sigil, why it matters,
> and how BDD-based analysis with threshold discretization provides rule verification
> without heavyweight SMT solvers.

---

## 1. What Is Formal Verification?

Formal verification is the process of using mathematical methods to **prove** that
a system behaves correctly — not by testing specific inputs (which can never cover
all cases), but by reasoning about **all possible inputs** simultaneously.

```
Testing:              Formal Verification:
  input_1 → ✓          ∀ inputs → ✓ or counterexample
  input_2 → ✓          "No input exists that violates property P"
  input_3 → ✓
  input_4 → ✗ (bug!)
  ...
  (infinite inputs remain untested)
```

**Testing proves the presence of bugs. Verification proves their absence.**

In practice, formal verification tools work by:
1. Encoding your program's behavior as mathematical constraints
2. Asking a solver: "Can these constraints ever be violated?"
3. If yes → here's a concrete counterexample (the input that breaks it)
4. If no → the property holds for ALL possible inputs

### Verification vs Testing vs Fuzzing

| Approach | Coverage | Speed | Guarantees |
|----------|----------|-------|-----------|
| Unit testing | Specific cases you thought of | Fast | None — misses edge cases |
| Property-based testing | Random inputs (100s-1000s) | Medium | Statistical confidence |
| Fuzzing | Millions of random/mutated inputs | Slow | Finds crashes, not logic bugs |
| **Formal verification** | **All possible inputs** | Medium | **Mathematical proof** |

### Where It's Used Today

- **Hardware**: Intel, AMD, and ARM formally verify CPU designs (a single bug costs
  billions — see Intel's FDIV bug)
- **Aerospace**: DO-178C requires formal methods for safety-critical avionics software
- **Finance**: Trading systems verify that order matching is fair and complete
- **Compilers**: CompCert (verified C compiler), CakeML (verified ML compiler)
- **Smart contracts**: Solidity verifiers check that funds can't be stolen
- **Rule engines**: Drools, CLIPS verify that rule sets are complete and consistent

Sigil fits naturally here — it's a **rule-based decision engine** where wrong decisions
have real consequences.

---

## 2. Why Sigil Needs Formal Verification

Sigil programs make decisions: approve/deny loans, triage medical alerts, flag fraud,
classify risk. These decisions affect people.

### The Problem With Testing Rules

Consider a simple loan eligibility system:

```sigil
rule young_applicant with priority 1:
  when age is below 25
  and income exceeds 50000
  then eligible is true
  explain "Young applicant with high income"

rule senior_applicant with priority 2:
  when age exceeds 60
  and savings exceeds 100000
  then eligible is true
  explain "Senior applicant with savings"

rule standard with priority 3:
  when income exceeds 30000
  and credit_score exceeds 700
  then eligible is true
  explain "Standard qualification"
```

**Question:** Is every applicant covered? Can someone fall through the cracks?

You might test: age=30, income=40000, credit_score=750 → eligible ✓
And: age=22, income=60000 → eligible ✓

But what about: **age=40, income=25000, credit_score=600, savings=200000**?
No rule fires. The applicant gets no decision — a silent failure.

With 4 variables and realistic ranges, there are **billions** of input combinations.
Testing can't cover them all. Formal verification can.

### Four Properties Every Sigil Program Should Have

#### Property 1: Completeness — "Every input gets a decision"

```
∀ inputs: at least one rule fires
```

If there's a gap in the rules, some inputs produce no output — a silent failure
that's much worse than a crash (at least crashes are visible).

#### Property 2: Consistency — "Rules don't contradict each other"

```
∀ inputs: if multiple rules fire, they don't produce conflicting decisions
```

If rule A says "approve" and rule B says "deny" for the same input, the system's
behavior depends on priority ordering — which may not be what the author intended.

#### Property 3: Reachability — "Every rule can actually fire"

```
∀ rules: ∃ some input that makes this rule fire
```

A dead rule is a maintenance hazard — it exists in the code, developers assume it
works, but it can never trigger. Often caused by conditions that contradict each other.

#### Property 4: Termination — "Forward chaining always halts"

```
The fixed-point loop reaches a stable state in finite steps
```

If rule A sets x=true and rule B sets x=false (and each triggers the other), the
system oscillates forever. Sigil caps this at 100 iterations, but detecting it
statically is better than hitting the cap at runtime.

---

## 3. How Formal Verification Works (Concepts)

### 3.1 Satisfiability (SAT/SMT)

The foundation of formal verification is **satisfiability checking**:

Given a logical formula, is there an assignment of values that makes it true?

```
Formula: (x > 100) AND (x < 50)
Answer:  UNSATISFIABLE — no value of x satisfies both constraints
```

```
Formula: (x > 100) AND (y < 50)
Answer:  SATISFIABLE — e.g., x=200, y=10
```

**SAT** (Boolean Satisfiability) handles propositional logic (true/false variables).
**SMT** (Satisfiability Modulo Theories) extends SAT with arithmetic, strings, arrays,
etc. Z3 is the most famous SMT solver (Microsoft Research, used in thousands of
verification tools).

### 3.2 Counterexample-Guided Verification

The verification pattern for rules:

```
1. Encode all rules as logical formula:
   coverage = rule1_conditions OR rule2_conditions OR ...

2. Ask solver: is NOT(coverage) satisfiable?
   - YES → found a gap (solver returns the concrete input values)
   - NO  → complete (every input is covered by at least one rule)
```

The solver doesn't just say "there's a problem" — it gives you the **exact input**
that triggers it. This is called a **counterexample** and it's the most valuable
output of verification.

### 3.3 Binary Decision Diagrams (BDDs)

A BDD is a compact data structure for representing boolean functions. It's a directed
acyclic graph where each node tests one boolean variable, branching to "true" or
"false" children. Equivalent subtrees are shared (merged), making BDDs canonical —
two BDDs represent the same function if and only if they're structurally identical.

```
Example: (a AND b) OR (a AND c)

  Decision tree (exponential):       BDD (shared, compact):
         a                                  a
        / \                                / \
       b   b                              b   b
      / \ / \                            / \ / \
     c  c c  c                          F  c F  F
    /\ /\ /\ /\                           / \
   T F T F F F T F                        T   F
```

**Why BDDs are perfect for rule verification:**

1. **AND/OR/NOT are native operations** — combining rule conditions is a single
   BDD operation, not a custom algorithm
2. **Satisfiability is O(1)** — a BDD is satisfiable iff it's not the FALSE node
3. **Counterexamples are free** — traverse any path to TRUE to get a witness
4. **Tautology check is O(1)** — a BDD is a tautology iff it's the TRUE node
5. **Canonical form** — two formulas are equivalent iff their BDDs are identical

BDDs have been the standard for rule/circuit verification since Randal Bryant's
seminal 1986 paper. Hardware verification at Intel, AMD, and ARM all use BDDs.

### 3.4 Threshold Discretization

Sigil conditions compare numeric variables against specific values. The key insight:
**between any two consecutive thresholds, all inputs behave identically** (the same
rules fire). So we only need to reason about which threshold regions an input falls in.

```
Given rules that test age at: 18, 25, 50, 65

The number line splits into regions:
  (-∞, 18] | (18, 25] | (25, 50] | (50, 65] | (65, +∞)

Create boolean variables for each threshold:
  age_le_18   →  "age ≤ 18?"
  age_le_25   →  "age ≤ 25?"
  age_le_50   →  "age ≤ 50?"
  age_le_65   →  "age ≤ 65?"

Add ordering constraints (monotonicity):
  age_le_18 → age_le_25 → age_le_50 → age_le_65
  (if age ≤ 18, then certainly age ≤ 25, etc.)

Now encode conditions as boolean formulas:
  "age exceeds 25"          → NOT(age_le_25)
  "age is below 18"         → age_le_17  (or: age_le_18 for ≤ semantics)
  "age is between 18 and 65" → NOT(age_le_17) AND age_le_65
```

This is mathematically **sound** — the discretized boolean analysis captures exactly
the same rule behaviors as the original numeric conditions, because rules only
distinguish inputs at their threshold points.

### 3.5 Multi-Variable Analysis

Real Sigil programs have multiple variables. BDDs handle this naturally — the BDD
has boolean variables for ALL thresholds across ALL input variables:

```sigil
rule complex with priority 5:
  when age exceeds 25
  and income exceeds 50000
  and credit_score is between 600 and 800
```

BDD variables: `age_le_25`, `income_le_50000`, `credit_le_600`, `credit_le_800`
BDD formula: `NOT(age_le_25) AND NOT(income_le_50000) AND NOT(credit_le_600) AND credit_le_800`

The BDD handles AND/OR combinations across variables natively — no need for
"constraint box" products or per-variable analysis. This is strictly more powerful
than per-variable interval analysis because it captures **correlations** between
variables (e.g., "rule fires when age > 25 OR income > 50000").

---

## 4. Sigil's Constraint Space (Why BDDs, Not Z3)

### What Sigil Conditions Map To

Every Sigil condition type maps cleanly to boolean predicates:

```
Sigil condition type        → BDD encoding
──────────────────────────────────────────────────
x exceeds 100               → NOT(x_le_100)              threshold predicate
x is below 50               → x_le_49                     threshold predicate
x is between 10 and 90      → NOT(x_le_9) AND x_le_90    two thresholds
x is at least 18            → NOT(x_le_17)                threshold predicate
x is at most 65             → x_le_65                     threshold predicate
x is :active                → x_eq_active                 enum boolean
x is :high                  → x_eq_high                   enum boolean
x is true                   → x_true                      direct boolean
x is false                  → NOT(x_true)                 negated boolean
x in [1, 2, 3]              → x_eq_1 OR x_eq_2 OR x_eq_3 finite disjunction
not <cond>                  → NOT(cond_bdd)               BDD complement
cond1 and cond2             → cond1_bdd AND cond2_bdd     BDD conjunction
cond1 or cond2              → cond1_bdd OR cond2_bdd      BDD disjunction
x is assigned               → x_assigned                  auxiliary boolean
x is empty                  → x_empty                     auxiliary boolean
x contains elem             → x_contains_elem             auxiliary boolean
any/all/none                → bounded enumeration          expand for small lists
starts_with/ends_with       → SKIP                        not verifiable
```

**Result: 95% of Sigil conditions encode directly as boolean BDD operations.**
The remaining 5% are string operations and unbounded quantification (skipped).

### Why Not Z3?

Z3 is a general-purpose SMT solver handling quantifiers, non-linear arithmetic,
bit-vectors, arrays, strings — far more than Sigil needs. The cost:

1. **200MB C++ binary** — Z3 is massive
2. **Cannot compile to WASM** — the `z3-sys` Rust bindings require native C++ libs
3. **Overkill** — Sigil's conditions are propositional + threshold comparisons
4. **Deployment friction** — users need `pip install z3-solver`

BDDs handle Sigil's exact constraint space with:
- One small pure-Rust dependency (`biodivine-lib-bdd`, 68K downloads)
- Compiles to WASM alongside the bytecode VM
- 40 years of proven use for rule/circuit completeness checking
- AND/OR/NOT/satisfiability/counterexample as native O(1)-to-O(n) operations

### Why Not a Custom Interval Solver?

We also considered building a custom interval arithmetic engine. BDDs are better:

| Aspect | Custom Intervals | BDD |
|--------|-----------------|-----|
| Boolean combinations | Must reinvent union/complement | Native AND/OR/NOT |
| Multi-variable correlations | Per-variable only (lossy) | Full cross-variable analysis |
| Counterexamples | Must implement witness search | `bdd.first_valuation()` (free) |
| Completeness check | Custom gap-finding algorithm | `coverage_bdd == TRUE` (one line) |
| Maintenance | We maintain forever | Community-maintained library |
| Correctness confidence | New code, new bugs | Proven data structure, tested library |

### The Rust Solver Landscape (Research)

| Crate | Type | Pure Rust | WASM | Maturity | Fit for Sigil |
|-------|------|-----------|------|----------|---------------|
| `biodivine-lib-bdd` | BDD | Yes | Yes | High (68K DL) | Excellent |
| `z3` / `z3-sys` | SMT bindings | No (C++ FFI) | No | Very high | Overkill, no WASM |
| `oxiz` | Pure Rust SMT | Yes | Yes | Very low (v0.1.3) | Future option |
| `varisat` | SAT | Yes | Likely | Dormant | Too low-level |
| `rustsat-batsat` | SAT | Yes | Yes | Active | Too low-level |
| `libpcp` | CSP | Yes | Likely | Low | Incomplete analysis |

**Decision:** `biodivine-lib-bdd` for primary analysis, with OxiZ as a future
upgrade path when it matures for coupled multi-variable constraints.

---

## 5. BDD-Based Verification Architecture

### Overview

The verifier lives in Sigil's Rust core (`sigil_core`) using `biodivine-lib-bdd`.
It has three stages:

```
Stage 1: Discretize          Stage 2: Encode           Stage 3: Verify
──────────────────           ───────────────           ────────────────
Scan all rules         →     Build BDD per rule   →   BDD operations for
Extract thresholds           Condition → boolean        completeness, conflicts,
Create boolean vars          formula → BDD              dead rules, termination
Build ordering BDD
```

### Stage 1: Threshold Discretization

Scan all rule conditions and extract numeric comparison points:

```rust
use std::collections::{HashMap, BTreeSet};

/// Extract all numeric thresholds from a rule set, grouped by variable.
pub fn extract_thresholds(rules: &[RuleInfo]) -> HashMap<String, BTreeSet<i64>> {
    let mut thresholds: HashMap<String, BTreeSet<i64>> = HashMap::new();

    for rule in rules {
        for cond in &rule.conditions {
            match cond {
                Comparison { var, op: "exceeds", value } => {
                    thresholds.entry(var.clone())
                        .or_default()
                        .insert(*value);  // threshold at value
                }
                Comparison { var, op: "is below", value } => {
                    thresholds.entry(var.clone())
                        .or_default()
                        .insert(value - 1);  // strict: below value
                }
                Comparison { var, op: "is between", low, high } => {
                    let set = thresholds.entry(var.clone()).or_default();
                    set.insert(low - 1);  // boundary before range
                    set.insert(*high);    // upper bound
                }
                // ... other comparison types
            }
        }
    }
    thresholds
}
```

### Stage 2: Boolean Encoding

Create BDD variables for each threshold and build ordering constraints:

```rust
use biodivine_lib_bdd::{BddVariableSet, BddVariable, Bdd};

pub struct VerifierContext {
    vars: BddVariableSet,
    /// Map: "age_le_25" → BddVariable
    threshold_vars: HashMap<String, BddVariable>,
    /// Map: "status_eq_active" → BddVariable
    symbol_vars: HashMap<String, BddVariable>,
    /// Monotonicity constraints: age_le_18 → age_le_25 → age_le_65
    ordering_bdd: Bdd,
    /// Threshold values for decoding witnesses back to human-readable form
    threshold_values: HashMap<String, Vec<(BddVariable, i64)>>,
}

impl VerifierContext {
    pub fn from_rules(rules: &[RuleInfo]) -> Self {
        let thresholds = extract_thresholds(rules);
        let symbols = extract_symbols(rules);

        // Create BDD variable set
        let mut var_names = Vec::new();
        let mut threshold_vars = HashMap::new();
        let mut threshold_values = HashMap::new();

        for (var_name, points) in &thresholds {
            let sorted: Vec<i64> = points.iter().copied().collect();
            let mut var_thresholds = Vec::new();
            for &point in &sorted {
                let bdd_name = format!("{}_le_{}", var_name, point);
                var_names.push(bdd_name.clone());
                // (will assign BddVariable after building set)
                var_thresholds.push(point);
            }
            threshold_values.insert(var_name.clone(), vec![]); // filled after
        }

        // ... build BddVariableSet from all var_names
        // ... build ordering BDD (monotonicity + mutual exclusion)
        // ... return VerifierContext
    }

    /// Encode a Sigil condition as a BDD formula.
    pub fn encode_condition(&self, cond: &ConditionInfo) -> Bdd {
        match cond {
            Comparison { var, op: "exceeds", value } => {
                // x exceeds 100 → NOT(x_le_100)
                let bdd_var = self.threshold_vars[&format!("{}_le_{}", var, value)];
                self.vars.mk_not_var(bdd_var)
            }
            Comparison { var, op: "is below", value } => {
                // x is below 50 → x_le_49
                let bdd_var = self.threshold_vars[&format!("{}_le_{}", var, value - 1)];
                self.vars.mk_var(bdd_var)
            }
            Comparison { var, op: "is between", low, high } => {
                // x between 10 and 90 → NOT(x_le_9) AND x_le_90
                let lo = self.vars.mk_not_var(
                    self.threshold_vars[&format!("{}_le_{}", var, low - 1)]
                );
                let hi = self.vars.mk_var(
                    self.threshold_vars[&format!("{}_le_{}", var, high)]
                );
                lo.and(&hi)
            }
            SymbolEq { var, symbol } => {
                // x is :active → x_eq_active
                let bdd_var = self.symbol_vars[&format!("{}_eq_{}", var, symbol)];
                self.vars.mk_var(bdd_var)
            }
            BoolCheck { var, value: true } => {
                self.vars.mk_var(self.threshold_vars[&format!("{}_true", var)])
            }
            Compound { op: "and", left, right } => {
                self.encode_condition(left).and(&self.encode_condition(right))
            }
            Compound { op: "or", left, right } => {
                self.encode_condition(left).or(&self.encode_condition(right))
            }
            Not { inner } => {
                self.encode_condition(inner).not()
            }
            // ... other condition types
        }
    }

    /// Encode a full rule: conjunction of all conditions, intersected with ordering.
    pub fn encode_rule(&self, rule: &RuleInfo) -> Bdd {
        let mut bdd = self.ordering_bdd.clone();
        for cond in &rule.conditions {
            bdd = bdd.and(&self.encode_condition(cond));
        }
        bdd
    }
}
```

### Stage 3: Verification Checks

All four checks are simple BDD operations:

```rust
/// Completeness: does the union of all rules cover all valid inputs?
pub fn check_completeness(ctx: &VerifierContext, rule_bdds: &[Bdd]) -> CompletenessResult {
    let mut coverage = ctx.vars.mk_false();
    for bdd in rule_bdds {
        coverage = coverage.or(bdd);
    }

    if coverage.and(&ctx.ordering_bdd) == ctx.ordering_bdd {
        CompletenessResult::Complete
    } else {
        let gap = ctx.ordering_bdd.and_not(&coverage);
        let witness = gap.first_valuation().unwrap();
        CompletenessResult::Incomplete {
            counterexample: ctx.decode_witness(&witness),
        }
    }
}

/// Dead rules: is any rule's BDD unsatisfiable (always FALSE)?
pub fn check_dead_rules(rule_bdds: &[Bdd]) -> Vec<usize> {
    rule_bdds.iter().enumerate()
        .filter(|(_, bdd)| bdd.is_false())
        .map(|(i, _)| i)
        .collect()
}

/// Conflicts: do any two rules with different actions overlap?
pub fn check_conflicts(
    ctx: &VerifierContext,
    rules: &[(Bdd, &RuleInfo)],
) -> Vec<Conflict> {
    let mut conflicts = Vec::new();
    for i in 0..rules.len() {
        for j in (i + 1)..rules.len() {
            let overlap = rules[i].0.and(&rules[j].0);
            if !overlap.is_false() {
                let witness = overlap.first_valuation().unwrap();
                conflicts.push(Conflict {
                    rule_a: i,
                    rule_b: j,
                    witness: ctx.decode_witness(&witness),
                    priority_resolves: rules[i].1.priority != rules[j].1.priority,
                    action_conflict: rules[i].1.action != rules[j].1.action,
                });
            }
        }
    }
    conflicts
}

/// Termination: detect cycles in the rule dependency graph (no BDD needed).
pub fn check_termination(rules: &[RuleInfo]) -> Vec<Cycle> {
    let mut graph: HashMap<String, Vec<String>> = HashMap::new();
    for rule in rules {
        let reads = extract_read_vars(rule);
        let writes = extract_write_vars(rule);
        for w in &writes {
            for r in &reads {
                graph.entry(w.clone()).or_default().push(r.clone());
            }
        }
    }
    find_cycles(&graph)
}
```

### Witness Decoding

BDD gives a satisfying assignment as a map of boolean variable → true/false.
We decode this back to human-readable input values:

```rust
impl VerifierContext {
    /// Decode BDD valuation → human-readable input description
    pub fn decode_witness(&self, valuation: &BddValuation) -> Counterexample {
        let mut inputs = HashMap::new();

        for (var_name, thresholds) in &self.threshold_values {
            // Find which region the variable falls in
            // e.g., age_le_18=true, age_le_25=true, age_le_65=true → age ≤ 18
            // e.g., age_le_18=false, age_le_25=true → 18 < age ≤ 25
            let mut lower = None;
            let mut upper = None;
            for (bdd_var, threshold_value) in thresholds {
                if valuation[*bdd_var] {
                    upper = Some(*threshold_value);
                    break;
                } else {
                    lower = Some(*threshold_value);
                }
            }
            // Pick a concrete value in the region
            let value = match (lower, upper) {
                (None, Some(u)) => u,           // age ≤ 18 → pick 18
                (Some(l), Some(u)) => l + 1,    // 18 < age ≤ 25 → pick 19
                (Some(l), None) => l + 1,       // age > 65 → pick 66
                (None, None) => 0,              // unconstrained → pick 0
            };
            inputs.insert(var_name.clone(), Value::Number(value as f64));
        }

        // ... decode symbol and boolean variables similarly
        Counterexample { inputs }
    }
}
```

---

## 6. Worked Examples

### Example 1: Finding a Completeness Gap

```sigil
define MIN_AGE as 18
define MAX_AGE as 65

rule young_adult with priority 1:
  when age is between MIN_AGE and 30
  then category is :young
  explain "Young adult bracket"

rule middle_age with priority 2:
  when age exceeds 30
  and age is below 50
  then category is :middle
  explain "Middle age bracket"

rule senior with priority 3:
  when age exceeds 50
  and age is below MAX_AGE
  then category is :senior
  explain "Senior bracket"
```

**Verification runs (BDD-based):**

```
Step 1: Extract thresholds
  age thresholds: {17, 18, 30, 50, 65}
  BDD variables: age_le_17, age_le_18, age_le_30, age_le_50, age_le_65
  Ordering: age_le_17 → age_le_18 → age_le_30 → age_le_50 → age_le_65

Step 2: Encode each rule as BDD
  young_adult: NOT(age_le_17) AND age_le_30       (age ∈ [18, 30])
  middle_age:  NOT(age_le_30) AND age_le_50       (age ∈ (30, 50])
               BUT: "exceeds 30" is strict, so NOT(age_le_30)
               AND "below 50" is strict, so age_le_49...
               → actually: NOT(age_le_30) AND age_le_49
  senior:      NOT(age_le_50) AND age_le_64       (age ∈ (50, 65))

Step 3: Build coverage BDD
  coverage = young_adult OR middle_age OR senior

Step 4: Check completeness
  gap = ordering_bdd AND NOT(coverage)
  gap != FALSE → INCOMPLETE

Step 5: Extract counterexamples from gap BDD
  Witness 1: age_le_17=true → age = 10 (minors not handled)
  Witness 2: age_le_49=false, age_le_50=true → age = 50 (boundary miss)
  Witness 3: age_le_65=false → age = 70 (elderly not handled)

Report:
  Completeness: 3 gaps found
    Gap 1: age < 18 (example: age = 10) — minors not handled
    Gap 2: age = 50 — boundary between middle and senior
    Gap 3: age ≥ 65 (example: age = 70) — elderly not handled
  Suggestion: Add boundary rules or use inclusive comparisons
```

### Example 2: Detecting a Dead Rule

```sigil
rule impossible with priority 5:
  when temperature exceeds 100
  and temperature is below 50
  then alert is :paradox
  explain "This should never happen"
```

**Verification (BDD-based):**

```
Step 1: Extract thresholds
  temperature thresholds: {50, 100}
  BDD variables: temp_le_50, temp_le_100
  Ordering: temp_le_50 → temp_le_100

Step 2: Encode rule as BDD
  "exceeds 100"  → NOT(temp_le_100)
  "is below 50"  → temp_le_49 (strict less)
  Rule BDD = NOT(temp_le_100) AND temp_le_49
  After AND with ordering: temp_le_49 implies temp_le_100
    so NOT(temp_le_100) AND temp_le_49 → FALSE

Step 3: BDD is FALSE → DEAD RULE

Report:
  Dead Rules: 1
    "impossible" — conditions are unsatisfiable
      temperature must simultaneously exceed 100 AND be below 50
      No input can ever trigger this rule
```

### Example 3: Detecting an Oscillation

```sigil
rule turn_on with priority 1:
  when system_active is false
  then system_active is true
  explain "Activate system"

rule turn_off with priority 2:
  when system_active is true
  then system_active is false
  explain "Deactivate system"
```

**Verification (graph-based, no constraint solving):**

```
Step 1: Build dependency graph
  turn_on:  reads system_active, writes system_active
  turn_off: reads system_active, writes system_active

Step 2: Detect cycles
  turn_on writes system_active → turn_off reads system_active
  turn_off writes system_active → turn_on reads system_active
  CYCLE DETECTED

Step 3: Check for oscillation
  turn_on sets system_active = true
  turn_off sets system_active = false
  Values toggle → OSCILLATION

Report:
  Termination: 1 potential infinite loop
    "turn_on" ↔ "turn_off" oscillate system_active between true/false
    Forward chaining will hit the 100-iteration cap
  Suggestion: Add a guard condition (e.g., check a counter or external state)
```

---

## 7. Limitations and Boundaries

### What We CAN Verify

- Numeric conditions (exceeds, below, between, at least, at most)
- Symbol equality (is :active, is :high)
- Boolean conditions (is true, is false)
- List membership (in [1, 2, 3])
- Logical combinations (and, or, not)
- Rule completeness, conflicts, dead rules, termination cycles

### What We CANNOT Verify

| Limitation | Why | Mitigation |
|-----------|-----|-----------|
| String conditions | Infinite domain, regex undecidability | Skip; report as "unverifiable" |
| Neural outputs | Non-deterministic by definition | Skip neural-dependent rules |
| Runtime expressions | `given x as a + b * c` — symbolic execution needed | Approximate or skip |
| External data | `given x from input` — unbounded domain | Assume full domain unless type-annotated |
| Quantified conditions | `any item in list where item exceeds 10` — depends on list contents | Bounded enumeration for small lists |
| Coupled constraints | `when x + y exceeds 100` — multi-variable intervals | Conservative (warn, don't verify) |

### The Verification Guarantee

Sigil's verifier provides:
- **If "PASS":** No counterexample exists within the verifiable constraint space.
  Your rules are complete and consistent for all numeric, boolean, and symbol inputs.
- **If "FAIL":** Here are concrete input values that break the property. Fix them.
- **If "PARTIAL":** Some conditions couldn't be verified (strings, neural, coupled).
  The verified portion is sound; the unverified portion is flagged.

This is **not** "your program is 100% correct." It's "your rule conditions are
mathematically consistent and complete within the verifiable domain."

---

## 8. Comparison: Z3 vs BDD vs Custom Interval Solver

### Why We Chose BDDs

| Factor | Z3 (C++ SMT) | Custom Intervals | BDD (biodivine) |
|--------|--------------|-----------------|------------------|
| **Installation** | 200MB C++ binary | Built-in | 1 small Rust crate |
| **WASM** | Impossible | Yes | Yes (pure Rust) |
| **Boolean ops** | Built-in | Must reinvent | Native (free) |
| **Multi-variable** | Full cross-variable | Per-variable only | Full cross-variable |
| **Counterexamples** | Built-in | Must implement | `first_valuation()` (free) |
| **Completeness** | Query-based | Custom algorithm | `bdd == TRUE` (one line) |
| **Solver power** | Full SMT | Intervals + enums | Propositional + discretized |
| **Maintenance** | External (Microsoft) | Us forever | External (active community) |
| **Maturity** | 15+ years | Brand new | 40+ years (BDD theory) |
| **Sigil fit** | Overkill | Good | Excellent |

### When Z3 / Full SMT Would Be Better

If Sigil grew to support:
- Non-linear arithmetic constraints (x^2 + y^2 < 100)
- Regular expression matching in conditions
- Complex quantified reasoning (∀ x ∈ list: P(x))
- Array theory (indexed access with symbolic indices)
- Coupled multi-variable constraints (x + y > 100)

The encoder interface is designed with a backend abstraction — when OxiZ (pure Rust
SMT solver) matures, it can be added as an optional backend for cases where BDD
discretization is insufficient. The BDD approach handles the common case; SMT
handles the exceptional case.

### BDD Scalability

BDD size depends on **variable count** and **variable ordering**. For Sigil:

| Rule set | BDD variables | Expected BDD nodes | Verification time |
|----------|---------------|--------------------|--------------------|
| 5 rules, 3 vars | ~10 | ~50 | < 1ms |
| 20 rules, 8 vars | ~40 | ~500 | < 10ms |
| 50 rules, 15 vars | ~80 | ~5,000 | < 100ms |
| 100 rules, 25 vars | ~120 | ~50,000 | < 1s |
| 200+ rules, 40+ vars | ~200+ | ~500,000+ | 1-5s |

The exponential worst case (2^n BDD nodes) is avoided by Sigil's typical patterns:
rules group conditions by variable (good for BDD sharing), and threshold predicates
are monotone (ordering constraints provide structure).

---

## 9. Research and Prior Art

### Rule Verification in Industry

- **Drools (Red Hat)**: Business rule management system with built-in conflict detection
  and completeness analysis. Uses decision tables for static analysis.
- **CLIPS (NASA)**: Expert system shell with agenda-based conflict resolution. Formal
  verification via SCADE integration for safety-critical applications.
- **OPA (Open Policy Agent)**: Policy engine with Rego language. Verification via
  `opa check` command — similar to what `sigil verify` will provide.
- **Alloy (MIT)**: Relational logic analyzer. Uses SAT solving for bounded model
  checking of structural properties. Inspired our counterexample-guided approach.

### BDD History and Applications

- **Bryant (1986)**: "Graph-Based Algorithms for Boolean Function Manipulation" —
  the foundational paper that made BDDs practical. Showed that with fixed variable
  ordering, BDDs are canonical (unique representation for each function).
- **Hardware verification**: Intel, AMD, and ARM use BDD-based model checking for
  CPU design verification. The entire field of symbolic model checking (McMillan, 1993)
  is built on BDDs.
- **Network verification**: Tools like Hassel (Header Space Library) use BDD-like
  structures to verify that network forwarding rules are complete and consistent —
  the same class of problem as Sigil rule verification.

### Abstract Interpretation

- **Abstract interpretation** (Cousot & Cousot, 1977): Foundation of interval analysis.
  Used in ASTRÉE (Airbus A380 flight control verification) and Polyspace (MATLAB).
  Threshold discretization is a form of abstract interpretation over interval domains.

### Relevant Papers

- Bryant, "Graph-Based Algorithms for Boolean Function Manipulation" (1986)
  — The BDD paper. Foundation of our verification approach.
- McMillan, "Symbolic Model Checking" (1993)
  — Using BDDs for exhaustive verification of finite-state systems
- De Moura & Bjørner, "Z3: An Efficient SMT Solver" (2008)
  — Z3's architecture; OxiZ is building a pure Rust equivalent
- Clarke, Grumberg & Peled, "Model Checking" (2000)
  — Comprehensive textbook on formal verification techniques
- Jackson, "Software Abstractions" (2012)
  — Alloy's approach to lightweight formal methods (counterexample-guided)
- Cousot & Cousot, "Abstract Interpretation: A Unified Lattice Model" (1977)
  — Theoretical foundation for threshold discretization

---

## 10. Summary

Formal verification for Sigil answers four critical questions about rule-based
programs:

1. **Completeness** — Does every input get a decision?
2. **Consistency** — Do rules ever contradict?
3. **Reachability** — Can every rule actually fire?
4. **Termination** — Does forward chaining always halt?

We use **BDD-based analysis** with `biodivine-lib-bdd` (pure Rust) instead of Z3
or a custom interval solver because:
- BDDs are the proven standard for rule completeness/conflict checking (40+ years)
- AND/OR/NOT/satisfiability/counterexample are native BDD operations (free)
- Pure Rust — compiles to WASM, ships built-in, one small dependency
- Threshold discretization is sound for Sigil's finite comparison points
- Handles multi-variable correlations that per-variable interval analysis cannot
- Future upgrade path to OxiZ (pure Rust SMT) for coupled constraints

The verifier:
1. Extracts numeric thresholds from all rule conditions
2. Creates boolean predicates with monotonicity constraints
3. Encodes each rule as a BDD
4. Uses BDD operations to check all four properties
5. Produces **concrete counterexamples** from BDD satisfying assignments

```
$ sigil verify loan_rules.sigil

Completeness ✓  All inputs covered
Conflicts    ⚠  2 overlaps (resolved by priority)
Dead Rules   ✓  All rules reachable
Termination  ✓  No cycles detected

Result: PASS (0 errors, 2 warnings)
```
