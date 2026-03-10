# Sigil — Neuro-Symbolic AI Positioning & Gap Analysis

> **Date**: 2026-03-10
> **Scope**: Where Sigil stands in the neuro-symbolic AI landscape, what's already aligned, what's missing, and what to build next.

---

## 1. The Core of Neuro-Symbolic Systems

Every serious neuro-symbolic system — whether academic, enterprise, or open-source — converges on the same foundational architecture:

```
Raw Input → [Neural Perception] → Structured Representation → [Symbolic Reasoning] → Decision + Trace
                                        ↕
                                   State / Memory
                                        ↕
                                   Tools / APIs
```

Eight principles define the field:

| # | Principle | What It Means |
|---|-----------|---------------|
| 1 | **Dual Representation** | Neural handles perception/learning; symbolic handles reasoning/logic. Neither replaces the other. |
| 2 | **Integration Layer** | A formal bridge converts neural outputs into symbolic representations and symbolic decisions back into natural language. |
| 3 | **Deterministic Reasoning** | Given the same symbolic state, always produce the same decision. Non-determinism is explicit and bounded. |
| 4 | **Explainability & Traceability** | Every decision has an auditable reasoning chain. White-box, not black-box. |
| 5 | **Grounded Knowledge** | Rules, ontologies, or knowledge graphs anchor reasoning to verified domain knowledge. |
| 6 | **State Management** | Symbolic state persists and evolves across reasoning steps (and optionally across interactions). |
| 7 | **Tool & API Orchestration** | The symbolic layer can deterministically invoke external systems (databases, APIs, models). |
| 8 | **Ontology / Schema** | A structured representation of domain entities, relationships, and constraints governs the reasoning space. |

---

## 2. Sigil Alignment Scorecard

### What Sigil Already Has

| Principle | Sigil Implementation | Alignment |
|-----------|---------------------|-----------|
| **Dual Representation** | `neural` keyword = perception, `rule`/`compute` = reasoning. The language **enforces** the boundary — LLMs never decide. | STRONG |
| **Integration Layer** | `neural` declarations with `confidence_threshold`, `fallback`, and typed returns feed into deterministic `rule` conditions. Phase 4 adds NL-to-Sigil generation (the reverse bridge). | STRONG (design), PARTIAL (implementation) |
| **Deterministic Reasoning** | Forward chaining engine with priority-based conflict resolution, iterative until fixed point. 582 tests prove determinism. Same input always produces the same decision. | STRONG |
| **Explainability & Traceability** | `ProgramTrace`, `RuleTrace`, `ConditionTrace` — every condition evaluation, every rule firing, every action recorded. `explain` clauses provide human-readable justifications. Traces are **fundamental output**, not debugging. | STRONG — this is Sigil's defining advantage |
| **Grounded Knowledge** | `define` constants, `type` records, explicit fact space. Domain knowledge is source code, not configuration. | STRONG |
| **State Management** | Immutable `Environment` with scope chain. Rule fact space evolves during forward chaining. | MODERATE — single evaluation, not multi-turn |
| **Tool & API Orchestration** | Python FFI design exists. Module system with import/export works. | PARTIAL — real FFI in Phase 3 |
| **Ontology / Schema** | `type Person is record:`, `type Decision is one of:`, gradual type system with boundary enforcement. | MODERATE — types exist, no auto-generation |

### Alignment Summary

```
Dual Representation      ████████████████████  STRONG
Deterministic Reasoning  ████████████████████  STRONG
Traceability             ████████████████████  STRONG (defining feature)
Grounded Knowledge       ████████████████████  STRONG
Integration Layer        ████████████████░░░░  STRONG design, needs real neural
State Management         ████████████░░░░░░░░  Single-shot, not multi-turn
Tool Orchestration       ████████░░░░░░░░░░░░  Design exists, needs real FFI
Ontology / Schema        ████████████░░░░░░░░  Types exist, no auto-generation
```

**Bottom line**: Sigil is strongly aligned on the reasoning/tracing/knowledge side. The gaps are on the perception/integration/stateful-agent side.

---

## 3. What Sigil Gets Right

These are properties that make Sigil uniquely positioned in the neuro-symbolic space:

### 3.1 Traces as Fundamental Output

Most systems treat execution traces as debugging artifacts. Sigil treats them as **the primary output**. In regulated domains (finance, healthcare, compliance), the trace IS the deliverable. The decision is a side effect.

```
TRACE [credit_check]:
  EVAL applicant.credit_score >= 680 → true  [credit_score = 720]
  RULE credit_check → FIRED
  ACTION credit_eligible = true
  EXPLAIN "Applicant meets minimum credit threshold (FCRA compliant)"
```

This is not a log. This is the product.

### 3.2 AI-Native Grammar

Sigil was designed from day one for LLM generation:
- **Flat structure**: Minimal nesting. Rules are top-level declarations.
- **~30 keywords**: Every keyword is a common English word.
- **Explicit types at boundaries**: No inference across modules.
- **PEG grammar**: Unambiguous. LLMs can generate valid Sigil reliably.

Research (MoonBit, SimPy) shows flat, regular, explicitly-typed languages reduce LLM token usage by 10-15% and improve generation accuracy.

### 3.3 Constrained NL That Actually Parses

Sigil is not "write in English" (unreliable). Not "write in code" (unreadable). It is a formal PEG grammar that reads like English:

```sigil
rule temperature_alert with priority 10:
  when sensor temperature exceeds 100 degrees
  and sensor status is :active
  then trigger alert with severity :critical
  explain "Active sensor exceeded safe threshold"
```

This is parseable by a hand-written recursive descent parser. It is also readable by a domain expert who has never seen code before.

### 3.4 Open Specification

Sigil's PEG grammar, operational semantics, and type system spec are all published. Anyone can build a Sigil implementation. This is the "open standard" play — Sigil as the lingua franca for neuro-symbolic systems, not a proprietary engine.

### 3.5 Ecosystem Anchor

Python FFI for the ML ecosystem. Rust core for performance. Sigil is not an island — it connects to the tools and libraries that matter.

---

## 4. What's Missing — Gap Analysis

### Gap 1: Real Neural Integration (CRITICAL)

**Current state**: `neural` declarations return hardcoded fallback values.
**Required**: Actual model loading, inference, confidence scoring, and fallback enforcement.
**Impact**: Without this, Sigil is a symbolic-only language claiming neuro-symbolic identity.
**Phase**: 3 — Neural Bridge (planned)

```sigil
-- This parses and evaluates today, but the model isn't actually called
neural classify_intent from text: Text:
  model "intent-classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  fallback to :unknown
```

**What needs to happen**:
- Model registry and loading (HuggingFace, local, API-based)
- Confidence type as first-class value
- Threshold enforcement at runtime
- Neural vs symbolic trace distinction
- Latency tracking in traces

### Gap 2: Multi-Turn Stateful Evaluation (HIGH)

**Current state**: Sigil evaluates programs as single-shot — input in, decision out.
**Required**: Stateful sessions where symbolic state persists across interactions.
**Impact**: Cannot build conversational agents, multi-step workflows, or interactive decision systems.
**Phase**: Not currently planned — should be added to Phase 3 or Phase 4.

**Proposed construct** — `agent` or `session`:

```sigil
agent loan_advisor:
  state:
    step: :greeting
    applicant: none
    decision: none

  rule greet with priority 100:
    when step is :greeting
    then respond "I can help you check loan eligibility. What's your name?"
    transition step to :collecting_info

  rule collect_info with priority 50:
    when step is :collecting_info
    and applicant is none
    then request applicant_data
    transition step to :evaluating

  rule evaluate with priority 30:
    when step is :evaluating
    and applicant is not none
    then evaluate loan_rules with applicant
    transition step to :complete
```

This would enable:
- Conversational AI with deterministic state management
- Multi-step approval workflows
- Interactive decision systems
- Agent-style applications with symbolic guarantees

### Gap 3: Backward Chaining (MEDIUM)

**Current state**: Forward chaining only (data-driven: "given facts, what rules fire?").
**Required**: Goal-driven evaluation ("to prove X, what facts do I need?").
**Impact**: Cannot answer "why" questions or prove goals from incomplete data.
**Phase**: Phase 2 Sprint 3 (planned, next sprint)

```sigil
-- Forward: evaluate all rules, see what fires
evaluate all rules with applicant

-- Backward: prove a specific goal
query loan_approved with applicant
-- "To prove loan_approved, I need eligible_base AND credit_ok..."
```

### Gap 4: Tool & API Orchestration (HIGH)

**Current state**: Module system works for Sigil-to-Sigil imports. Python FFI is design-only.
**Required**: Real Python library calls from Sigil, API invocation, database queries.
**Impact**: Cannot connect to external systems (CRMs, databases, APIs).
**Phase**: Phase 3 — Python FFI (planned)

```sigil
-- Should actually call the Python function
import python requests

compute fetch_credit_score from ssn: Text returns Number:
  given response as requests.get("https://api.credit.com/score", params: {ssn: ssn})
  return response.json().score
```

### Gap 5: Auto-Ontology Generation (MEDIUM)

**Current state**: Types and records are hand-written by developers.
**Required**: Automatic generation of domain ontologies from natural language descriptions or existing data schemas.
**Impact**: Slower onboarding for new domains.
**Phase**: Phase 4+ (not currently planned)

```sigil
-- Future: generate types from schema
ontology from "airline_booking":
  -- Auto-generates: Passenger, Flight, Booking, Seat, FareClass, etc.
  -- With relationships and constraints
```

### Gap 6: Continuous Learning / Feedback Loop (LOW for now)

**Current state**: Rules are static. Changes require editing source code.
**Required**: Mechanism to incorporate feedback into rule refinement.
**Impact**: Rules don't improve from production experience.
**Phase**: Phase 5+ (future)

### Gap 7: Temporal / Event Stream Processing (MEDIUM)

**Current state**: Phase 2 Sprint 3 adds `within` constraint parsing (stored, not enforced).
**Required**: Real event streams, time windows, temporal pattern matching.
**Impact**: Cannot build monitoring, alerting, or time-sensitive decision systems.
**Phase**: Phase 2 Sprint 3 (foundations), Phase 3+ (real implementation)

---

## 5. Sigil's Strategic Position

### The SQL Analogy

Sigil should be to neuro-symbolic AI what SQL is to databases:

| SQL | Sigil |
|-----|-------|
| Declarative language for data | Declarative language for decisions |
| Any database engine can execute it | Any symbolic engine can execute it |
| Human-readable, machine-parseable | Human-readable, LLM-generable |
| Open standard, many implementations | Open spec (PEG grammar, semantics published) |
| The interface, not the engine | The interface between neural and symbolic |

### Target Domains (where Sigil wins)

| Domain | Why Sigil Fits |
|--------|---------------|
| **Regulated Finance** | Traces satisfy audit requirements (CFPB, ECOA, FCRA). Determinism is legally required. |
| **Healthcare** | HIPAA/EMTALA compliance needs explainable decisions. Neural triage + symbolic protocols. |
| **Insurance** | Claims processing rules are naturally expressed as Sigil rules. Trace = compliance proof. |
| **Legal/Compliance** | Policy rules, regulatory checks, sanctions screening — all rule-based with audit needs. |
| **Supply Chain** | Multi-criteria decision making with explainable trade-offs. |
| **Safety-Critical Systems** | Deterministic fallbacks for neural perception failures. |

### What Makes Sigil Different

```
Proprietary NS engines:    Closed model, API-based, vendor lock-in
Python frameworks:          No formal grammar, no type system, no traces
Logic languages (Prolog):   Not LLM-generable, not readable by domain experts
JSON/YAML configs:          No control flow, no types, no composition
Prompt engineering:          Non-deterministic, no audit trail, no guarantees

Sigil:                      Open language + formal grammar + LLM-generable +
                            deterministic + traced + typed + ecosystem-connected
```

---

## 6. Revised Phase Plan — Incorporating Gaps

### Phase 2 Sprint 3 (Current — Advanced Rules + Polish)
- Backward chaining engine (`query` keyword)
- Temporal rule foundations (`within` constraints, stored not enforced)
- Stdlib: `sigil.time`, `sigil.trace`, `sigil.io`
- Enhanced type inference
- Performance benchmarks
- Target: 660+ tests

### Phase 3 (Ecosystem Integration — **Critical Phase**)
- **Real neural bridge**: Model loading, inference, confidence types
- **Python FFI**: Real library calls from Sigil
- **Rust core**: Performance-critical symbolic execution via PyO3
- **Multi-turn state management**: `agent`/`session` construct (NEW)
- Target: 800+ tests

### Phase 4 (Production Readiness)
- NL-to-Sigil generator (LLM-powered)
- Bytecode VM (10-100x performance)
- LSP server + VS Code extension
- Rich error experience
- PyPI package (`pip install sigil-lang`)
- Target: 1000+ tests

### Phase 5 (Advanced Features + Benchmarking)
- WASM target (browser-based execution)
- Distributed execution
- Formal verification (Z3 integration)
- Visual rule builder
- Auto-ontology generation from schemas
- **Benchmark: [t-bench](https://github.com/sierra-research/tau-bench) airline & retail scenarios** — validate Sigil's neuro-symbolic pipeline against industry-standard task completion benchmarks
- Continuous learning / feedback loops
- Target: production-grade

---

## 7. Immediate Action Items

| Priority | Action | Why |
|----------|--------|-----|
| **P0** | Complete Phase 2 Sprint 3 | Backward chaining + temporal foundations close important symbolic gaps |
| **P1** | Design `agent`/`session` construct | Multi-turn state is the #1 missing capability for real-world applications |
| **P1** | Begin Phase 3 neural bridge | Without real model integration, the "neuro" in neuro-symbolic is theoretical |
| **P2** | Build NL-to-Sigil proof-of-concept | Demonstrate that LLMs can reliably generate valid Sigil programs |
| **P2** | Publish Sigil's PEG grammar as a standalone spec | Reinforce the "open standard" positioning |
| **P3** | Run t-bench scenarios end-to-end | Validate neuro-symbolic pipeline on industry benchmarks (Phase 5) |
| **P3** | Target one regulated industry vertical | Build a complete domain example (e.g., loan processing end-to-end with real data) |

---

## 8. The Moat

Sigil's defensibility comes from three interlocking properties:

1. **Open specification** — The PEG grammar, operational semantics, and type system are published. This invites adoption, not competition. Network effects compound.

2. **Traces as product** — In regulated industries, the decision is a side effect. The trace is the deliverable. Sigil's trace architecture is baked into the language, not bolted on. This is extremely hard to retrofit.

3. **AI-native grammar** — Designed for LLM generation from day one. ~30 keywords, flat structure, explicit types. As LLMs become the primary authors of rule systems, the language that LLMs generate most reliably wins.

The combination — open, traced, and AI-native — is unique. No other system offers all three.

---

*Neural for perception. Symbolic for reasoning. Traces as proof.*
*The trace is the product. The decision is a side effect.*
