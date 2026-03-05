# Sigil: Operational Semantics

## Overview

This document defines the operational semantics of Sigil — what programs *mean* and how they execute. Sigil has two execution domains:

1. **Symbolic domain**: Deterministic, traced, CPU-native
2. **Neural domain**: Probabilistic, confidence-tagged, explicitly bounded

## Execution Model

### Environments

An environment `E` maps identifiers to values:

```
E = { x₁ → v₁, x₂ → v₂, ..., xₙ → vₙ }
```

Environments are **immutable** — new bindings create new environments:

```
E' = E ∪ { x → v }     -- extend E with new binding
```

### Values

The value domain:

```
v ::= n                 -- numbers (integer or float)
    | s                 -- strings (text)
    | b                 -- booleans (true, false)
    | :k                -- symbols (keywords)
    | none              -- absence
    | [v₁, ..., vₙ]    -- lists
    | {k₁: v₁, ..., kₙ: vₙ}  -- records
    | <rule>            -- rule values
    | <trace>           -- trace records
    | <confidence v c>  -- neural result with confidence
```

### Traces

Every evaluation produces a trace `T`:

```
T = [t₁, t₂, ..., tₙ]

tᵢ = TraceEntry {
  expression: AST,        -- what was evaluated
  result: Value,          -- what it produced
  bindings: Environment,  -- variable values at this point
  duration: Duration,     -- wall-clock time
  source: :symbolic | :neural  -- which domain
}
```

## Rule Semantics

### Rule Evaluation

A rule `R` has the form:

```
rule name [priority p]:
  when C₁ and C₂ and ... and Cₙ
  then A
  explain S
```

**Evaluation**: `eval_rule(R, E) → (fires: bool, trace: T)`

```
eval_rule(R, E) =
  let (b₁, t₁) = eval_condition(C₁, E)
  let (b₂, t₂) = eval_condition(C₂, E)
  ...
  let (bₙ, tₙ) = eval_condition(Cₙ, E)
  let fires = b₁ ∧ b₂ ∧ ... ∧ bₙ
  let trace = [t₁, t₂, ..., tₙ]
  if fires:
    let (v, tₐ) = eval_action(A, E)
    return (true, trace ++ [tₐ])
  else:
    return (false, trace)
```

**Key property**: Short-circuit evaluation for AND conditions. If C₁ is false, C₂...Cₙ are not evaluated (but are recorded in the trace as "skipped").

### Rule Set Evaluation

Given a rule set `RS = {R₁, R₂, ..., Rₘ}` and facts `E`:

```
eval_rules(RS, E) =
  let candidates = [(Rᵢ, eval_rule(Rᵢ, E)) | Rᵢ ∈ RS]
  let matching = [Rᵢ | (Rᵢ, (true, _)) ∈ candidates]
  let winner = select_by_priority(matching)
  return (winner.action_result, merge_traces(candidates))
```

**Conflict resolution** (when multiple rules match):
1. Highest priority wins
2. If equal priority: most specific rule wins (more conditions)
3. If still equal: declaration order (first declared wins)

### Forward Chaining

Rules can assert new facts, triggering other rules:

```
eval_forward_chain(RS, E) =
  let E' = E
  loop:
    let (fired, new_facts, trace) = eval_rules(RS, E')
    if no rules fired:
      return (E', trace)
    E' = E' ∪ new_facts
    continue loop  -- with new facts, re-evaluate
```

**Termination guarantee**: Forward chaining terminates when:
- No new facts are produced in an iteration
- A maximum iteration count is reached (configurable, default 100)
- A cycle is detected (same facts produce same new facts)

## Condition Semantics

### Comparison Operators

```
eval_condition(x exceeds y, E) =
  let vx = eval_expr(x, E)
  let vy = eval_expr(y, E)
  assert type(vx) = type(vy) = Number
  return (vx > vy, trace_entry(x > y, vx > vy, {x: vx, y: vy}))

eval_condition(x is between a and b, E) =
  let vx = eval_expr(x, E)
  let va = eval_expr(a, E)
  let vb = eval_expr(b, E)
  return (va ≤ vx ≤ vb, trace_entry(...))

eval_condition(x is y, E) =
  let vx = eval_expr(x, E)
  let vy = eval_expr(y, E)
  return (vx = vy, trace_entry(...))  -- structural equality
```

### Logical Combinators

```
eval_condition(C₁ and C₂, E) =
  let (b₁, t₁) = eval_condition(C₁, E)
  if not b₁:
    return (false, [t₁, skip(C₂)])  -- short-circuit
  let (b₂, t₂) = eval_condition(C₂, E)
  return (b₁ ∧ b₂, [t₁, t₂])

eval_condition(C₁ or C₂, E) =
  let (b₁, t₁) = eval_condition(C₁, E)
  if b₁:
    return (true, [t₁, skip(C₂)])   -- short-circuit
  let (b₂, t₂) = eval_condition(C₂, E)
  return (b₁ ∨ b₂, [t₁, t₂])

eval_condition(not C, E) =
  let (b, t) = eval_condition(C, E)
  return (¬b, [negate(t)])
```

### Quantifiers

```
eval_condition(any x in xs has C, E) =
  let vs = eval_expr(xs, E)
  for each v in vs:
    let E' = E ∪ {x → v}
    let (b, t) = eval_condition(C, E')
    if b:
      return (true, t)
  return (false, all_traces)

eval_condition(all x in xs have C, E) =
  -- similar, but requires ALL to be true

eval_condition(none x in xs has C, E) =
  -- equivalent to: not (any x in xs has C)
```

## Expression Semantics

### Arithmetic

```
eval_expr(a + b, E) = eval_expr(a, E) + eval_expr(b, E)
eval_expr(a - b, E) = eval_expr(a, E) - eval_expr(b, E)
eval_expr(a * b, E) = eval_expr(a, E) * eval_expr(b, E)
eval_expr(a / b, E) = eval_expr(a, E) / eval_expr(b, E)  -- error if b = 0
```

### Field Access

```
eval_expr(r.f, E) =
  let v = eval_expr(r, E)
  assert v is Record
  assert f ∈ fields(v)
  return v[f]
```

### Function Call

```
eval_expr(f(a₁, ..., aₙ), E) =
  let func = lookup(f, E)
  let v₁ = eval_expr(a₁, E)
  ...
  let vₙ = eval_expr(aₙ, E)
  let E' = bind_params(func.params, [v₁, ..., vₙ])
  return eval_body(func.body, E')
```

### Pipeline

```
eval_expr(xs |> filter where C |> map to f |> take first n, E) =
  let v₀ = eval_expr(xs, E)
  let v₁ = [x | x ∈ v₀, eval_condition(C, E ∪ {it → x})]
  let v₂ = [eval_expr(f, E ∪ {it → x}) | x ∈ v₁]
  let v₃ = v₂[0:n]
  return v₃
```

## Neural Semantics

### Neural Declaration Evaluation

```
eval_neural(neural f from x: T, E) =
  let model = load_model(f.model)
  let input = eval_expr(x, E)
  let (result, confidence) = model.predict(input)

  if confidence < f.threshold:
    let fallback_value = eval_expr(f.fallback, E)
    return (<confidence fallback_value 0.0>,
            trace_entry(f, fallback_value, :neural, :fallback))

  assert type(result) = f.return_type
  return (<confidence result confidence>,
          trace_entry(f, result, :neural, :prediction))
```

**Neural guarantees:**
1. Always returns a value (fallback ensures this)
2. Always has a confidence score
3. Trace marks the result as `:neural` (vs `:symbolic`)
4. Type of result matches declaration

### Confidence Propagation

When neural results enter symbolic rules:

```
rule handle:
  given intent from classify(text)       -- intent has confidence
  when intent is :purchase               -- comparison uses value, ignores confidence
  and intent confidence above 0.9        -- explicit confidence check
  then process_purchase
```

Confidence is **not** implicitly propagated through symbolic rules. The symbolic engine produces deterministic outputs. Confidence is only accessible via explicit `confidence` access.

## Determinism Guarantee

**Theorem**: For any Sigil program P with no `neural` declarations, and any input I:

```
∀ runs r₁, r₂ of P on I:
  result(r₁) = result(r₂)
  trace(r₁) = trace(r₂)  -- modulo timestamps
```

**Proof sketch**: All operations in the symbolic domain are pure functions over immutable environments. Rule evaluation order is deterministic (priority + declaration order). No randomness, no side effects, no mutable state.

The only source of non-determinism is the `neural` keyword, which is explicitly marked and bounded by confidence thresholds and fallbacks.

## Memory Model

- **Immutable by default**: All bindings are immutable
- **`mutable` keyword**: Opt-in mutability for specific use cases
- **No shared mutable state**: Parallel rule evaluation is safe
- **Garbage collected**: Python's GC manages Sigil values
- **Rust core uses arena allocation**: For performance-critical paths
