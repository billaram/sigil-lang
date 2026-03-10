<p align="center">
  <h1 align="center">Sigil</h1>
  <p align="center"><strong>The programming language where LLMs parse and symbolic engines decide.</strong></p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> &bull;
    <a href="#why-sigil">Why Sigil</a> &bull;
    <a href="#see-it-in-action">Examples</a> &bull;
    <a href="#architecture">Architecture</a> &bull;
    <a href="docs/VISION.md">Vision</a> &bull;
    <a href="docs/ROADMAP.md">Roadmap</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/tests-582%20passing-brightgreen" alt="Tests">
    <img src="https://img.shields.io/badge/phase-2%20of%205-blue" alt="Phase">
    <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python">
    <img src="https://img.shields.io/badge/rust-core-orange" alt="Rust">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</p>

---

> **Neural for perception. Symbolic for reasoning. Traces as proof.**
>
> Sigil is a neuro-symbolic programming language — constrained natural language that compiles to deterministic symbolic execution with auditable traces. LLMs never make decisions. The symbolic engine does. Every time.

```sigil
rule loan_eligibility with priority 10:
  when applicant credit_score exceeds 680
  and applicant debt_to_income is below 43
  and applicant age is between 21 and 65
  then approve_loan is true
  explain "Applicant meets all federal lending criteria (CFPB/ECOA/FCRA)"
```

This is not YAML. Not a prompt template. Not an agent framework.
This is a **programming language** — with a lexer, parser, AST, type system, interpreter, module system, standard library, and REPL. Built from scratch.

---

## Why Sigil?

The AI industry has a reasoning problem:

| The Problem | Today's Hack | Sigil's Answer |
|---|---|---|
| LLMs hallucinate decisions | "Just add guardrails" | LLMs **only parse** — Sigil's symbolic engine decides |
| AI decisions aren't auditable | Log prompts and pray | Every rule produces an **execution trace** — the trace IS the output |
| Rules live in JSON/YAML | No types, no composition, no control flow | Full language: types, rules, compute, modules, FFI |
| Programming languages aren't AI-friendly | LLMs struggle with deep nesting | Flat structure, ~30 keywords, explicit types, PEG grammar |
| DSLs are islands | Can't call real libraries | **Python FFI** for ML ecosystem, **Rust core** for performance |

### The Neuro-Symbolic Split

```
                  THE BOUNDARY
                       |
    Neural Side        |        Symbolic Side
    ───────────        |        ───────────────
    LLMs               |        Sigil Engine
    Parse text         |        Evaluate rules
    Extract intent     |        Produce decisions
    Handle ambiguity   |        Guarantee determinism
    Probabilistic      |        Auditable traces
                       |
    "Patient reports   |   rule triage with priority 100:
     chest pain and    |     when any symptom in CRITICAL_SET
     shortness of      |     then escalate to emergency
     breath"           |     explain "Critical symptom detected"
                       |     trace: compliance [:hipaa, :emtala]
```

LLMs are extraordinary at perception. They should never make decisions. **Sigil enforces this boundary at the language level.**

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/billaram/sigil-lang.git
cd sigil-lang
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run your first program
sigil run examples/basics/hello.sigil

# Run with execution trace
sigil run examples/basics/temperature.sigil --trace --input '{"reading": {"sensor_id": "S1", "temperature": 142, "status": "active"}}'

# Type-check a program
sigil check examples/rules/loan_eligibility.sigil

# Start the REPL
sigil repl
```

---

## See It in Action

### Rules That Read Like English, Execute Like Code

```sigil
-- Temperature monitoring with prioritized rules
define CRITICAL_THRESHOLD as 150
define SAFE_THRESHOLD as 100

rule emergency_shutdown with priority 100:
  when reading temperature exceeds CRITICAL_THRESHOLD
  then shutdown_system
  explain "Temperature {reading.temperature} exceeds critical limit of {CRITICAL_THRESHOLD}"

rule temperature_alert with priority 10:
  when reading temperature exceeds SAFE_THRESHOLD
  and reading status is :active
  then trigger alert with severity :high
  explain "Active sensor {reading.sensor_id} exceeded safe threshold"
```

### Pattern Matching

```sigil
compute severity_label from level: Symbol returns Text:
  return match level:
    :critical -> "CRITICAL - Immediate action required"
    :high     -> "HIGH - Action required within 1 hour"
    :medium   -> "MEDIUM - Action required within 24 hours"
    :low      -> "LOW - No immediate action"
    _         -> "UNKNOWN"
```

### Functional Pipelines

```sigil
define scores as [85, 92, 78, 95, 88, 73, 91]

main:
  given top_3 as scores
    |> filter where it exceeds 80
    |> sort by it descending
    |> take first 3
  print(top_3)  -- [95, 92, 91]
```

### Types and Records

```sigil
type Applicant is record:
  name: Text
  age: Number
  credit_score: Number
  debt_to_income: Number

type Decision is one of:
  approved with rate: Number
  denied with reasons: list of Text
  review with notes: Text
```

### Neural Bridge — The Explicit Boundary

```sigil
-- The 'neural' keyword is the ONLY way to introduce non-determinism
neural extract_symptoms from clinical_text: Text:
  model "medical-ner-v3"
  returns list of Text
  confidence_threshold 0.75
  fallback to empty list

-- Neural output feeds deterministic rules
rule triage_assessment:
  given symptoms from extract_symptoms(patient.text)
  when any symptom in symptoms is in CRITICAL_SYMPTOMS
  then escalate to emergency
  explain "Critical symptom detected via NER model"
  trace:
    compliance [:hipaa, :emtala]
```

### Module System and Standard Library

```sigil
import sigil.math
import sigil.text
import sigil.list

main:
  given root as sqrt(144)           -- 12.0
  given name as uppercase("sigil")  -- "SIGIL"
  given nums as range(1, 5)         -- [1, 2, 3, 4]
```

---

## Execution Traces — Not Debugging, Fundamental Output

Every rule evaluation produces a trace. In regulated domains (finance, healthcare, compliance), **the trace is the product**. The decision is just a side effect.

```
sigil run loan.sigil --trace --input '{"applicant": {"age": 35, "credit_score": 720, "debt_to_income": 38, "income": 85000}}'
```

```
TRACE [age_check]:
  EVAL applicant.age between 21 and 65 → true  [age = 35]
  RULE age_check → FIRED
  ACTION age_eligible = true

TRACE [credit_check]:
  EVAL applicant.credit_score >= 680 → true  [credit_score = 720]
  RULE credit_check → FIRED
  ACTION credit_eligible = true

TRACE [full_eligibility]:
  EVAL age_eligible is true → true
  EVAL income_eligible is true → true
  EVAL credit_eligible is true → true
  RULE full_eligibility → FIRED
  ACTION loan_approved = true

Decision: approved | Rate: 3.8% | Time: 0.4ms
Trace: 5 rules evaluated, 5 fired, 0 skipped
```

---

## Architecture

```
Natural Language ──► Neural Parser ──► .sigil source ──► Compiler Pipeline ──► Decision + Trace
 (human or LLM)       (LLM)            (code)            (deterministic)       (auditable)
```

```
┌─────────────────────────────────────────────────────┐
│                  SIGIL PIPELINE                      │
│                                                     │
│   Source (.sigil)                                    │
│       │                                             │
│       ▼                                             │
│   [Lexer] ─── tokens (80+ token types)              │
│       │                                             │
│       ▼                                             │
│   [Parser] ─── AST (hand-written recursive descent) │
│       │                                             │
│       ▼                                             │
│   [Type Checker] ─── static verification            │
│       │                                             │
│       ▼                                             │
│   [Interpreter] ─── tree-walking evaluator          │
│       │                                             │
│       ├──► Rule Engine (forward chaining)           │
│       ├──► Trace Logger (always on)                 │
│       ├──► Python FFI (ML ecosystem)         │
│       └──► Rust Core (PyO3, performance)            │
│                                                     │
│   Output: Decision + Trace + Explanation            │
└─────────────────────────────────────────────────────┘
```

**Key implementation choices:**

| Component | Choice | Why |
|---|---|---|
| Parser | Hand-written recursive descent (PEG) | Unambiguous, linear-time, maximum control |
| Interpreter | Tree-walking (Python) | Proven path — bytecode VM planned for Phase 4 |
| Performance core | Rust via PyO3/maturin | <1ms rule evaluation at scale |
| Type system | Gradual (optional, required at boundaries) | Low barrier + safety where it matters |
| Rule engine | Forward chaining, priority-based | Iterative until fixed point, auditable |

---

## What's Built (582 Tests Passing)

| Component | Status | Details |
|---|---|---|
| Lexer | **Complete** | 80+ token types, indentation engine, 91 tests |
| Parser | **Complete** | Recursive descent, 40+ AST nodes, 87 tests |
| Type Checker | **Complete** | 5 error categories, match exhaustiveness, 51 tests |
| Interpreter | **Complete** | Rules, compute, match, pipeline, closures, 187 tests |
| Module System | **Complete** | Imports, exports, cycle detection, 53 tests |
| Standard Library | **Complete** | math, text, list, logic — 76 tests |
| REPL | **Complete** | Interactive with `:env`, `:rules`, `:trace` commands |
| CLI | **Complete** | `run`, `lex`, `parse-ast`, `check`, `repl` |
| Neural Bridge | **Stubs** | Returns fallback values — real model loading in Phase 3 |
| Rust Core | **Scaffold** | PyO3 module loads, performance paths planned |

### Development Phases

```
Phase 1 ████████████████████ COMPLETE   Lexer + Parser + Interpreter + Types + REPL
Phase 2 ████████████████░░░░ Sprint 3   Module System + Stdlib + Advanced Rules
Phase 3 ░░░░░░░░░░░░░░░░░░░░            Neural Bridge + Python FFI + Real Models
Phase 4 ░░░░░░░░░░░░░░░░░░░░            Bytecode VM + LSP + Performance
Phase 5 ░░░░░░░░░░░░░░░░░░░░            Production Hardening + WASM + Distribution
```

---

## The Sigil Language — Quick Reference

```sigil
-- Comments
-- This is a comment

-- Constants
define MAX_TEMP as 100 degrees
define THRESHOLD as 0.85

-- Types
type Person is record:
  name: Text
  age: Number

type Result is one of:
  success with value: Number
  failure with reason: Text

-- Rules (the core construct)
rule check_temperature with priority 10:
  when sensor temperature exceeds MAX_TEMP
  and sensor status is :active
  then trigger alert with severity :critical
  explain "Temperature exceeded on active sensor"

-- Compute (pure functions)
compute calculate_rate from score: Number returns Number:
  given base as 5.5
  given adjustment as (score - 680) * 0.01
  return base - adjustment

-- Match expressions
compute classify from value: Number returns Symbol:
  return match value:
    x when x exceeds 90 -> :excellent
    x when x exceeds 70 -> :good
    _ -> :needs_review

-- Pipelines
main:
  given result as data
    |> filter where it exceeds 50
    |> map to it * 2
    |> sort by it descending

-- Neural (explicit non-determinism)
neural classify from text: Text:
  model "classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  fallback to :unknown

-- Modules
import sigil.math
import sigil.text
from sigil.list import reverse, unique

-- Keywords (~30 total):
-- rule, when, then, and, or, not, if, else, given, define,
-- as, is, exceeds, below, between, any, all, none, in,
-- import, export, module, type, neural, explain, with,
-- true, false, compute, return, match, for, each, main
```

---

## Development

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
maturin develop                    # Build Rust core

# Run
sigil run file.sigil               # Execute a program
sigil run file.sigil --trace       # Execute with trace output
sigil run file.sigil --input '{}'  # Execute with JSON input
sigil repl                         # Interactive REPL
sigil lex file.sigil               # Dump token stream
sigil parse-ast file.sigil         # Dump AST
sigil check file.sigil             # Type-check only

# Test
pytest tests/ -v                   # All 582 tests
pytest tests/lexer/ -v             # Lexer tests
pytest tests/parser/ -v            # Parser tests
pytest tests/interpreter/ -v       # Interpreter tests
ruff check src/                    # Lint
mypy src/sigil/                    # Type check
```

---

## Research Foundations

Sigil builds on decades of work in symbolic AI, compiler design, and neuro-symbolic integration:

- **LISP (1958)** — Code as data. Programs that reason about themselves.
- **Prolog (1972)** — Logic as programming. Declarative rule evaluation.
- **Inform 7 (2006)** — Constrained natural language as a real programming language.
- **AlphaGeometry/AlphaProof (2024)** — Neural intuition feeding symbolic verification achieves superhuman reasoning.
- **Kautz Taxonomy** — Framework for classifying neuro-symbolic architectures.

Sigil is the **missing integration layer** — a general-purpose language for building neuro-symbolic systems, not another bespoke solution.

See [docs/research/](docs/research/) for the full bibliography (65 references).

---

## Contributing

We welcome researchers, language designers, and engineers passionate about neuro-symbolic AI.

**Good first contributions:**
- Write a new `.sigil` example program
- Add tests for edge cases
- Improve error messages
- Try breaking the parser and file issues

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <strong>Use neural where you must, symbolic where you can.</strong><br>
  <em>The trace is the proof.</em>
</p>
