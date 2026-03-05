# Sigil

**A neuro-symbolic programming language bridging human intent and deterministic execution.**

Sigil is a constrained natural language programming language designed as the interface layer between LLM-based neural parsers and deterministic symbolic execution engines. It is not syntax sugar. It is a new programming paradigm for the age of neuro-symbolic AI.

```sigil
rule loan_eligibility:
  when applicant age is between 21 and 65
  and credit_score exceeds 680
  and debt_to_income is below 0.43
  then approve with confidence high
  explain "Applicant meets all federal lending criteria"
```

## Why Sigil?

| Problem | Current State | Sigil Solution |
|---------|--------------|----------------|
| LLMs can't reason deterministically | Agentic AI uses LLMs for decisions (probabilistic) | LLMs only parse; symbolic engine decides (deterministic) |
| JSON/YAML aren't programming languages | No control flow, no types, no composition | Full language features with NL readability |
| Programming languages aren't AI-friendly | Complex syntax, deep nesting, implicit semantics | Flat structure, explicit types, regular grammar |
| DSLs are isolated | Most DSLs can't call general-purpose libraries | FFI to Python (ML ecosystem) and Rust (performance) |

## Architecture

```
Human/LLM Input (natural language)
        |
        v
  [Neural Parser] --- LLM translates NL to Sigil
        |
        v
  [Sigil Program] --- .sigil source file
        |
        v
  [Lexer → Parser → AST] --- PEG-based, deterministic
        |
        v
  [Type Checker] --- static verification of rule well-formedness
        |
        v
  [Interpreter] --- tree-walking, with execution trace
        |
        v
  [Decision + Trace] --- deterministic output + proof of reasoning
        |
        v
  [Python/Rust FFI] --- access to ML models, native performance
```

## Core Design Principles

1. **Constrained Natural Language**: Readable by humans, parseable by machines. Not free-form NL — a formal grammar that *reads* like English.
2. **Deterministic by Default**: Same input always produces same output. Probabilistic operations are explicitly marked.
3. **Trace Everything**: Every rule evaluation produces an auditable execution trace.
4. **Neural for Perception, Symbolic for Reasoning**: LLMs parse; Sigil decides.
5. **Anchor to the Ecosystem**: Python FFI for ML libraries, Rust core for performance.
6. **AI-Native Design**: Flat structure, minimal nesting, regular syntax — optimized for LLM generation.

## Quick Start

```bash
# Install (coming soon)
pip install sigil-lang

# Run a Sigil program
sigil run examples/basics/hello.sigil

# Parse natural language to Sigil (requires LLM backend)
sigil parse "Check if temperature exceeds 100 degrees and alert critical"

# Execute with trace
sigil run --trace examples/rules/temperature_check.sigil
```

## Project Status

**Phase: Foundation (Active)**

This is an ambitious open-source project in early development. See [ROADMAP.md](docs/ROADMAP.md) for the full development plan.

## Repository Structure

```
sigil-lang/
├── README.md
├── docs/
│   ├── VISION.md              # Grand vision and philosophy
│   ├── ARCHITECTURE.md        # Technical architecture
│   ├── design/
│   │   ├── SYNTAX.md          # Language syntax specification
│   │   ├── TYPE_SYSTEM.md     # Type system design
│   │   └── INTEROP.md         # FFI with Python and Rust
│   ├── spec/
│   │   ├── GRAMMAR.peg        # Formal PEG grammar
│   │   └── SEMANTICS.md       # Operational semantics
│   └── research/
│       ├── FOUNDATIONS.md      # Research foundations
│       └── COMPARISONS.md     # Comparison with existing languages
├── src/
│   ├── sigil/                  # Python package (frontend + interpreter)
│   │   ├── lexer/              # Tokenization
│   │   ├── parser/             # PEG parser → AST
│   │   ├── ast/                # AST node definitions
│   │   ├── interpreter/        # Tree-walking interpreter
│   │   ├── types/              # Type system
│   │   ├── stdlib/             # Standard library
│   │   └── ffi/                # Python/Rust interop
│   └── sigil_core/             # Rust core (performance-critical paths)
├── tests/
├── examples/
├── tools/                      # Dev tools, formatters, LSP
└── benchmarks/
```

## Contributing

This project is in its foundational phase. We welcome researchers, language designers, and engineers passionate about neuro-symbolic AI. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE).

## Acknowledgments

Built on research from DARPA's Three Waves of AI, the Kautz Taxonomy of neuro-symbolic systems, and decades of work in symbolic AI, functional programming, and compiler design. See [FOUNDATIONS.md](docs/research/FOUNDATIONS.md) for the full research bibliography.
