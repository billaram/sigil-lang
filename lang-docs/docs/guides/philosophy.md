# Philosophy

## The problem

Two worlds exist in tension:

**The Neural World**: LLMs can understand natural language, extract intent, handle ambiguity, and generalize from examples. But they cannot reason deterministically, produce reproducible outputs, or explain their decisions with verifiable traces.

**The Symbolic World**: Rule engines, constraint solvers, and formal systems can reason deterministically, produce auditable traces, and guarantee correctness. But they cannot understand natural language, handle ambiguity, or learn from examples.

Every serious AI system today awkwardly bridges these worlds with JSON configs, YAML files, prompt templates, and ad-hoc glue code. There is no *lingua franca* — no shared language that both worlds speak natively.

**Sigil is that language.**

---

## What Sigil IS

- **A programming language** — with a lexer, parser, AST, type checker, interpreter, and standard library.
- **A neuro-symbolic interface** — the formal boundary between neural perception and symbolic reasoning.
- **An AI-native language** — designed from day one for LLM generation and human reading.
- **An ecosystem participant** — anchored to Python (for ML libraries) and Rust (for performance). Sigil is not an island.
- **An open standard** — MIT licensed, community-driven, specification-first.

## What Sigil is NOT

- **Not a prompt template language.** Sigil programs execute deterministically. They are not prompts.
- **Not JSON/YAML with keywords.** Sigil has control flow, types, composition, modules, and traces.
- **Not an "English programming language."** The grammar is formal and constrained. It reads like English but parses like a PEG.
- **Not agentic AI.** LLMs do not make decisions. They parse. Sigil decides.
- **Not purely academic.** Designed for production use in regulated domains.

---

## Core principles

### 1. Neural for perception, symbolic for reasoning

LLMs parse natural language into Sigil. The symbolic engine decides. LLMs never make decisions — they translate. The `neural` keyword is the only bridge, and it requires explicit types, confidence thresholds, and fallbacks.

### 2. Deterministic by default

Same input produces the same output, always. The only way to introduce non-determinism is the `neural` keyword. Everything else is pure symbolic computation.

### 3. Traces are fundamental output, not debugging

Every rule evaluation produces an auditable execution trace. In regulated domains (finance, healthcare, compliance), the trace IS the output. The decision is just a side effect.

### 4. Constrained natural language, not free-form

Sigil reads like English but parses as a PEG grammar. This is not "code that looks like English" — it's a formal language with a natural-language-like surface syntax. The grammar is unambiguous and linear-time parseable.

### 5. Anchor to ecosystem

Python FFI for ML libraries. Rust core for performance. Sigil is designed to work with existing tools, not replace them.

---

## The end state

When Sigil reaches maturity:

1. A domain expert describes a decision process in natural language
2. An LLM translates that description into a Sigil program
3. The Sigil program is type-checked, validated, and reviewed by humans
4. The program executes deterministically, producing decisions with traces
5. When the rules are insufficient, explicitly-marked neural fallbacks engage
6. Every decision is auditable, reproducible, and explainable

---

## Historical context

Sigil builds on a lineage of ideas:

- **LISP** (1958) — Code as data. Programs that can reason about themselves.
- **Prolog** (1972) — Logic as programming. Declarative rules over imperative steps.
- **Inform 7** (2006) — Natural language as code. Proof that constrained NL can be a real programming language.
- **AlphaGeometry / AlphaProof** (2024) — Neuro-symbolic reasoning. Neural intuition feeding symbolic verification.

Sigil is the missing integration layer — a general-purpose language for building neuro-symbolic systems.
