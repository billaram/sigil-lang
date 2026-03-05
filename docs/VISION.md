# Sigil: Vision & Philosophy

## The Problem

We are at an inflection point in computing. Two worlds exist in tension:

**The Neural World**: LLMs can understand natural language, extract intent, handle ambiguity, and generalize from examples. But they cannot reason deterministically, produce reproducible outputs, or explain their decisions with verifiable traces.

**The Symbolic World**: Rule engines, constraint solvers, and formal systems can reason deterministically, produce auditable traces, and guarantee correctness. But they cannot understand natural language, handle ambiguity, or learn from examples.

Every serious AI system today awkwardly bridges these worlds with JSON configs, YAML files, prompt templates, and ad-hoc glue code. There is no *lingua franca* — no shared language that both worlds speak natively.

**Sigil is that language.**

## The Thesis

> A constrained natural language programming language, designed for AI-native generation and human-native reading, can serve as the universal interface between neural perception and symbolic execution — creating a new programming paradigm for neuro-symbolic AI.

## Historical Arc

### LISP (1958): Code as Data
John McCarthy created LISP with a radical insight: programs and data should share the same representation. S-expressions made programs inspectable, transformable, and composable. This enabled the first AI revolution — expert systems, symbolic reasoning, and the dream of machine intelligence through logic.

LISP's homoiconicity was ahead of its time. Programs that could reason about themselves. Code that could be generated, analyzed, and transformed by other code. This is exactly what we need today — but for a world where the "other code" is an LLM.

### Prolog (1972): Logic as Programming
Alain Colmerauer showed that formal logic could *be* the programming language. You declare what is true; the system figures out how to compute it. Unification, backtracking, and resolution — programming as theorem proving.

Prolog's declarative nature maps directly to rule systems. But its syntax was designed for logicians, not humans or LLMs.

### Inform 7 (2006): Natural Language as Code
Graham Nelson proved that constrained natural language could be a real programming language. Inform 7 compiles English sentences into executable interactive fiction. It demonstrated that the gap between human language and formal computation is bridgeable — within a well-defined domain.

### The Missing Piece (2024→): Neural + Symbolic + Natural Language

AlphaGeometry and AlphaProof proved that neuro-symbolic systems can achieve superhuman reasoning when neural intuition feeds symbolic verification. But both are bespoke systems. There is no general-purpose language for building such systems.

**Sigil fills this gap.**

## Design Philosophy

### 1. The Two-Layer Principle

Sigil has two layers, both first-class:

**Surface Layer** — Constrained natural language that humans read and LLMs generate:
```sigil
rule temperature_alert:
  when sensor temperature exceeds 100 degrees
  and sensor status is active
  then trigger alert with severity critical
  explain "Temperature exceeded safe threshold on active sensor"
```

**Core Layer** — Symbolic representation that the interpreter executes:
```
(rule temperature_alert
  (when (and (> (. sensor temperature) 100)
             (= (. sensor status) :active)))
  (then (trigger alert {:severity :critical}))
  (explain "Temperature exceeded safe threshold on active sensor"))
```

The surface layer *desugars* to the core layer. Both are valid Sigil. The surface is for humans and LLMs; the core is for the interpreter and tooling.

### 2. Determinism as Default

Every Sigil expression is deterministic unless explicitly marked otherwise:

```sigil
-- This is deterministic: same input → same output, always
rule check_eligibility:
  when score exceeds 700 then approve

-- This is explicitly probabilistic (requires neural backend)
neural classify_intent from input:
  model "intent-classifier-v2"
  confidence_threshold 0.85
  fallback to unknown
```

The `neural` keyword is the only way to introduce non-determinism. It is visually distinct, requires a confidence threshold, and mandates a fallback. You always know where the boundary is.

### 3. Traces Are Not Optional

Every rule evaluation produces a trace — not as a debugging feature, but as a fundamental output:

```
TRACE [temperature_alert]:
  EVAL (> sensor.temperature 100) → true  [sensor.temperature = 142]
  EVAL (= sensor.status :active)  → true  [sensor.status = :active]
  MATCH rule temperature_alert    → fires
  ACTION trigger alert {severity: critical}
  EXPLAIN "Temperature exceeded safe threshold on active sensor"
  RESULT: alert triggered in 0.3ms
```

In regulated domains (finance, healthcare, compliance), the trace IS the output. The decision is just a side effect.

### 4. AI-Native Grammar

Sigil's grammar is designed for LLM generation:

- **Flat structure**: Minimal nesting. Rules are top-level declarations.
- **Regular syntax**: Consistent patterns (`when...then`, `define...as`, `given...compute`).
- **Explicit boundaries**: Type annotations at module boundaries. No inference across modules.
- **Small keyword vocabulary**: ~30 keywords. Every keyword is a common English word.
- **Unambiguous grammar**: PEG-based. No parsing ambiguity. LLMs can generate valid Sigil reliably.

Research shows (MoonBit, SimPy) that flat, regular, explicitly-typed languages reduce LLM token usage by 10-15% and improve generation accuracy.

### 5. Ecosystem Anchor

Sigil does not exist in a vacuum:

```sigil
-- Use Python ML libraries
import python torch
import python transformers

-- Use Rust for performance-critical symbolic execution
import rust sigil_core::solver

-- The bridge: neural parsing feeds symbolic execution
neural parse_claim from patient_text:
  model "medical-ner-v3"
  extract symptoms, severity, duration

rule triage_assessment:
  given parsed_claim from parse_claim
  when any symptom in ["chest_pain", "difficulty_breathing"]
  and severity is high
  then escalate to emergency
  using rust sigil_core::triage_engine  -- Rust for <1ms execution
```

Python gives us the entire ML/AI ecosystem. Rust gives us the performance for symbolic execution at scale. Sigil is the bridge.

## What Sigil Is NOT

- **Not a prompt template language**: Sigil programs execute deterministically. They are not prompts.
- **Not JSON/YAML with keywords**: Sigil has control flow, types, composition, modules, and traces.
- **Not an "English programming language"**: The grammar is formal and constrained. It reads like English but parses like a PEG.
- **Not agentic AI**: LLMs do not make decisions. They parse. Sigil decides.
- **Not purely academic**: Designed for production use in regulated domains.

## What Sigil IS

- **A programming language**: With lexer, parser, AST, type checker, interpreter, and standard library.
- **A neuro-symbolic interface**: The formal boundary between neural perception and symbolic reasoning.
- **An AI-native language**: Designed from day one for LLM generation and human reading.
- **An ecosystem participant**: Anchored to Python and Rust, not isolated.
- **An open standard**: MIT licensed, community-driven, specification-first.

## The End State

When Sigil reaches maturity:

1. A domain expert describes a decision process in natural language.
2. An LLM translates that description into a Sigil program.
3. The Sigil program is type-checked, validated, and reviewed by humans.
4. The program executes deterministically on CPU, producing decisions with traces.
5. When the rules are insufficient, explicitly-marked neural fallbacks engage.
6. Every decision is auditable, reproducible, and explainable.

This is not a dream. Each component exists today. Sigil is the missing integration layer.

## Guiding Quotes

> "The real problem is not whether machines think but whether men do." — B.F. Skinner

> "A language that doesn't affect the way you think about programming is not worth knowing." — Alan Perlis

> "Use neural where you must, symbolic where you can." — Neuro-Symbolic Design Principle

> "The trace is the proof." — Sigil Design Principle
