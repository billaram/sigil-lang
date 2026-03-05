# Sigil: Comparative Analysis

## How Sigil Differs from Existing Approaches

This document positions Sigil against existing languages, tools, and paradigms.

---

## Comparison Matrix

| Feature | Sigil | JSON/YAML | Prolog | Scallop | Python | LMQL | Inform 7 |
|---------|-------|-----------|--------|---------|--------|------|----------|
| **Human readable** | High | Medium | Low | Low | Medium | Medium | Very High |
| **LLM generable** | High | High | Low | Low | Medium | Medium | Low |
| **Deterministic execution** | Yes | N/A | Yes | Partial | No | No | Yes |
| **Execution traces** | Built-in | N/A | Via cut | Provenance | Manual | No | No |
| **Neural integration** | First-class | N/A | No | First-class | Manual | First-class | No |
| **Type system** | Gradual | Schema | Untyped | Typed | Dynamic | Untyped | Weak |
| **FFI** | Python+Rust | N/A | C | Python | C/Rust | Python | N/A |
| **Rule engine** | Built-in | N/A | Core | Core | Libraries | N/A | Built-in |
| **Control flow** | Yes | No | Backtrack | Datalog | Yes | Partial | Limited |
| **Module system** | Yes | No | Modules | Files | Yes | No | Chapters |
| **Production ready** | Planned | Yes | Yes | Research | Yes | Research | Niche |

---

## Detailed Comparisons

### Sigil vs JSON/YAML

**The problem Sigil solves**: JSON and YAML are data formats, not programming languages. When AI systems need to express logic, they encode it in JSON:

```json
{
  "rule": "temperature_check",
  "conditions": [
    {"field": "temperature", "operator": ">", "value": 100},
    {"field": "status", "operator": "==", "value": "active"}
  ],
  "action": {"type": "alert", "severity": "critical"}
}
```

```sigil
rule temperature_check:
  when temperature exceeds 100
  and status is :active
  then alert with severity :critical
```

| Dimension | JSON/YAML | Sigil |
|-----------|-----------|-------|
| Readability | Structural but verbose | Natural language |
| Control flow | None (data only) | Full (if/else, loops, match) |
| Type safety | Schema validation (external) | Built-in type checker |
| Composition | Manual merging | Module system, imports |
| Execution | Requires separate engine | Self-executing |
| Traces | Not applicable | Built-in |
| Error messages | Parse errors only | Semantic errors with suggestions |

**Sigil is what JSON/YAML would be if they were programming languages designed for AI.**

### Sigil vs Prolog

**Prolog** is the classic logic programming language. Sigil draws from its declarative philosophy but diverges in critical ways:

```prolog
% Prolog
eligible(X) :-
    age(X, Age), Age >= 21, Age =< 65,
    credit_score(X, Score), Score >= 680,
    dti(X, DTI), DTI =< 0.43.
```

```sigil
-- Sigil
rule eligible:
  when applicant age is between 21 and 65
  and applicant credit_score is at least 680
  and applicant dti is at most 43 percent
  then approved
```

| Dimension | Prolog | Sigil |
|-----------|--------|-------|
| Syntax | Formal logic notation | Constrained natural language |
| Reasoning | Unification + backtracking | Forward/backward chaining |
| Neural integration | None | First-class (`neural` keyword) |
| Typing | Untyped | Gradual typing with units |
| Traces | Via trace/cut | Built-in, always-on |
| Ecosystem | Limited libraries | Python + Rust FFI |
| Learning curve | Steep (logic programming) | Gentle (reads like English) |
| LLM generation | Difficult | Designed for it |

### Sigil vs Scallop

**Scallop** (PLDI 2023) is the closest existing work to Sigil. Both are neuro-symbolic DSLs. Key differences:

```scallop
// Scallop (Datalog-based)
rel classify(x, label) = neural_net(x, label)
rel result(x) = classify(x, "positive"), sentiment_score(x, s), s > 0.5
```

```sigil
-- Sigil (constrained NL)
neural classify from text:
  model "sentiment-v2"
  returns Symbol
  threshold 0.5
  fallback to :neutral

rule positive_result:
  given label from classify(input)
  when label is :positive
  then flag_positive
```

| Dimension | Scallop | Sigil |
|-----------|---------|-------|
| Foundation | Datalog (relational) | Rule-based (forward/backward chaining) |
| Syntax | Logic programming | Constrained natural language |
| Differentiable | Yes (provenance semirings) | No (symbolic is deterministic) |
| Target user | ML researchers | Domain experts + engineers |
| Readability | Requires PL/Datalog knowledge | Reads like English |
| FFI | Python/PyTorch | Python + Rust |
| Traces | Provenance annotations | Full execution traces |
| Scope | Research framework | General-purpose NeSy language |

**Key distinction**: Scallop enables *differentiable* symbolic reasoning (training through symbolic layers). Sigil separates neural and symbolic: neural for perception, symbolic for deterministic execution. Different goals, complementary approaches.

### Sigil vs Python (for rule systems)

Python with libraries (e.g., `durable-rules`, `pyke`, custom if/else):

```python
# Python
def check_eligibility(applicant):
    if (21 <= applicant['age'] <= 65 and
        applicant['credit_score'] >= 680 and
        applicant['dti'] <= 0.43):
        return {'decision': 'approved', 'reasons': [...]}
    return {'decision': 'denied', 'reasons': [...]}
```

```sigil
-- Sigil
rule check_eligibility:
  when applicant age is between 21 and 65
  and applicant credit_score is at least 680
  and applicant dti is at most 43 percent
  then approved
  explain "All eligibility criteria met"
```

| Dimension | Python | Sigil |
|-----------|--------|-------|
| Readability | Code (requires programming) | Natural language |
| Traces | Manual logging | Automatic, always-on |
| Determinism | Possible but not enforced | Default behavior |
| Neural boundary | Implicit (any code can call models) | Explicit (`neural` keyword) |
| Domain expert access | Requires coding | Readable by non-programmers |
| Rule composition | Manual wiring | Built-in forward chaining |
| Error messages | Generic Python errors | Domain-specific Sigil errors |
| Performance | Interpreted | Rust-backed hot paths |

**Sigil is not replacing Python.** Sigil *uses* Python (via FFI) for ML/data operations. Sigil replaces the *rule logic* that is currently written as Python if/else chains or JSON configs.

### Sigil vs LMQL / DSPy / Guidance

These are LLM-interaction languages — they orchestrate LLM calls:

```lmql
# LMQL
"Classify {text} as [LABEL]" where LABEL in ["positive", "negative"]
```

```python
# DSPy
class Classifier(dspy.Module):
    def forward(self, text):
        return dspy.ChainOfThought("text -> label")(text=text)
```

| Dimension | LMQL/DSPy | Sigil |
|-----------|-----------|-------|
| Purpose | Orchestrate LLM calls | Bridge neural parsing + symbolic execution |
| Decision maker | LLM | Symbolic rule engine |
| Determinism | No (LLM output varies) | Yes (symbolic execution) |
| Traces | LLM-generated explanations | Actual computation proofs |
| Core paradigm | Prompt engineering | Rule-based programming |
| Where LLM is used | Central (for decisions) | Peripheral (for parsing only) |

**Fundamental difference**: LMQL/DSPy make LLMs smarter at deciding. Sigil makes LLMs unnecessary for deciding — they only parse.

### Sigil vs Inform 7

Inform 7 is the closest language in *syntax philosophy*:

```inform7
-- Inform 7
The temperature threshold is a number that varies.
The temperature threshold is 100.
Every turn when the current temperature is greater than the temperature threshold:
    say "ALERT: Temperature exceeded safe threshold!"
```

```sigil
-- Sigil
define temperature_threshold as 100 degrees

rule temperature_alert:
  when current_temperature exceeds temperature_threshold
  then alert "Temperature exceeded safe threshold"
```

| Dimension | Inform 7 | Sigil |
|-----------|----------|-------|
| Domain | Interactive fiction | Neuro-symbolic AI / decision systems |
| NL approach | Very free-form NL | Constrained NL with formal grammar |
| Typing | Weak | Gradual with units |
| Neural integration | None | First-class |
| FFI | Z-machine / Glulx | Python + Rust |
| Scale | Single games | Production decision systems |
| LLM generation | Difficult (too free-form) | Designed for it |

**Lesson from Inform 7**: Constrained NL programming works brilliantly in the right domain. Sigil applies this lesson to neuro-symbolic AI.

---

## Unique Sigil Properties

Properties that no existing language combines:

1. **Constrained NL syntax + formal PEG grammar**: Reads like English, parses deterministically
2. **Explicit neural/symbolic boundary**: `neural` keyword marks every non-deterministic operation
3. **Always-on execution traces**: Not debugging — fundamental output
4. **Dual FFI (Python + Rust)**: ML ecosystem + native performance
5. **AI-native grammar design**: Flat, regular, explicit — optimized for LLM generation
6. **Two-layer representation**: NL surface ↔ S-expression core
7. **Unit types**: `100 degrees`, `50 percent` — dimensional analysis built in
8. **Domain expert accessibility**: Non-programmers can read and understand Sigil rules

---

## When to Use Sigil (vs Alternatives)

| Use Case | Best Choice | Why |
|----------|-------------|-----|
| Decision logic in regulated domains | **Sigil** | Deterministic, auditable, traceable |
| ML model training | Python | Sigil is not for training |
| General application development | Python/Rust/etc. | Sigil is for decision logic, not apps |
| Formal theorem proving | Lean 4 | Sigil is less formal, more accessible |
| Database queries | SQL/Datalog | Sigil is for rules, not data retrieval |
| LLM prompt engineering | LMQL/DSPy | Sigil doesn't orchestrate LLMs |
| Differentiable symbolic reasoning | Scallop | Sigil's symbolic path is not differentiable |
| NL→Decision with audit trail | **Sigil** | This is exactly what Sigil is built for |
| AI-generated rule systems | **Sigil** | Designed for LLM generation |
| Config that needs logic | **Sigil** | JSON/YAML can't express logic |
