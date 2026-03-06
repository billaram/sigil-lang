# CLAUDE.md — Sigil Language Project Context

## What Is Sigil?

Sigil is a **neuro-symbolic programming language** — the interface between LLM neural parsers and deterministic symbolic execution engines. It uses constrained natural language syntax with a Python + Rust core.

```
Human/LLM text → Neural Parser → .sigil source → Lexer → Parser → AST → Type Checker → Interpreter → Decision + Trace
```

This is NOT syntax sugar. This is a new programming language with lexer, parser, AST, type system, interpreter, module system, and FFI.

## Core Philosophy (Never Violate These)

1. **Neural for perception, symbolic for reasoning.** LLMs parse natural language into Sigil. The symbolic engine decides. LLMs never make decisions.
2. **Deterministic by default.** Same input → same output, always. The `neural` keyword is the only way to introduce non-determinism.
3. **Traces are fundamental output, not debugging.** Every rule evaluation produces an auditable execution trace.
4. **Constrained NL, not free-form NL.** Sigil reads like English but parses as a PEG. Formal grammar underneath, readable surface on top.
5. **Anchor to ecosystem.** Python FFI for ML libraries, Rust core for performance. Sigil is not an island.
6. **AI-native grammar.** Flat structure, minimal nesting, ~30 keywords, explicit types at boundaries — designed for LLM generation.

## Architecture Decisions (Already Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language name | Sigil | Symbolic mark with inherent power/meaning |
| Host language | Python + Rust core | Python for ML ecosystem; Rust (via PyO3/maturin) for performance |
| Syntax style | Constrained natural language | Human readable + LLM generable |
| Parser approach | PEG-based (hand-written recursive descent) | Unambiguous, linear-time, maximum control |
| Implementation | Tree-walking interpreter first | Proven path: tree-walk → bytecode VM → native |
| Indentation | Significant whitespace (Python-style, spaces only) | Natural for NL-style syntax |
| Type system | Gradual (optional annotations, required at boundaries) | Low barrier + safety where it matters |
| Build system | maturin (Rust+Python) | Industry standard for PyO3 projects |
| Testing | pytest + hypothesis | Property-based testing for parser/type checker |

## Project Structure

```
sigil-lang/
├── CLAUDE.md                       ← YOU ARE HERE
├── ai_docs/                        ← Deep context for Claude Code sessions
│   ├── CONVENTIONS.md              ← Code style, naming, patterns
│   ├── ARCHITECTURE_DECISIONS.md   ← Why we chose what we chose
│   └── STATUS.md                   ← Current state, what works, what doesn't
├── PRP/                            ← Sprint plans and retrospectives
│   └── mar1-mar15.md               ← Current sprint
├── docs/
│   ├── VISION.md                   ← Grand vision (read for philosophy)
│   ├── ARCHITECTURE.md             ← Technical architecture (read for structure)
│   ├── ROADMAP.md                  ← Full 5-phase plan
│   ├── design/
│   │   ├── SYNTAX.md               ← Language syntax spec (THE reference for syntax)
│   │   ├── TYPE_SYSTEM.md          ← Type system design
│   │   └── INTEROP.md              ← Python/Rust FFI design
│   ├── spec/
│   │   ├── GRAMMAR.peg             ← Formal PEG grammar (THE reference for parsing)
│   │   └── SEMANTICS.md            ← Operational semantics
│   └── research/                   ← 8 research documents + bibliography
├── src/sigil/                      ← Python package (interpreter frontend)
│   ├── lexer/                      ← Tokenization
│   ├── parser/                     ← PEG parser → AST
│   ├── ast/                        ← AST node definitions
│   ├── interpreter/                ← Tree-walking evaluator
│   ├── types/                      ← Type checker
│   ├── stdlib/                     ← Standard library
│   ├── ffi/                        ← Python/Rust interop
│   └── cli.py                      ← CLI entry point
├── src/sigil_core/                 ← Rust crate (performance core, via PyO3)
├── tests/                          ← pytest test suite
├── examples/                       ← .sigil example programs (5 currently)
├── tools/                          ← Dev tools, formatters, LSP (future)
└── benchmarks/                     ← Performance benchmarks (future)
```

## Key Files to Read Before Working

**Before ANY work**, read these in order:
1. `ai_docs/STATUS.md` — What is currently implemented, what's next
2. `ai_docs/CONVENTIONS.md` — Code style and patterns to follow
3. `PRP/mar1-mar15.md` (or latest sprint plan) — Current tasks
4. `docs/design/SYNTAX.md` — Language syntax specification
5. `docs/spec/GRAMMAR.peg` — Formal grammar (if working on lexer/parser)

**For deeper context** (read as needed):
- `docs/VISION.md` — Philosophy and design principles
- `docs/ARCHITECTURE.md` — Full system architecture
- `docs/spec/SEMANTICS.md` — What programs mean (if working on interpreter)
- `docs/design/TYPE_SYSTEM.md` — Types (if working on type checker)
- `docs/design/INTEROP.md` — FFI design (if working on Python/Rust bridge)

## Development Commands

```bash
# Setup
pip install -e ".[dev]"           # Install in dev mode
maturin develop                    # Build Rust core (when it exists)

# Run
sigil run file.sigil               # Execute a program
sigil repl                         # Interactive REPL
sigil lex file.sigil               # Dump token stream (debugging)
sigil parse-ast file.sigil         # Dump AST (debugging)

# Test
pytest tests/ -v                   # Run all tests
pytest tests/lexer/ -v             # Lexer tests only
pytest tests/parser/ -v            # Parser tests only
ruff check src/                    # Lint
mypy src/sigil/                    # Type check Python code

# Format
ruff format src/ tests/            # Auto-format
```

## Code Conventions (Summary — see ai_docs/CONVENTIONS.md for full)

- **Python 3.11+**, use dataclasses, type hints everywhere
- **Immutable by default** — `@dataclass(frozen=True)` for AST nodes
- **No classes where functions suffice** — the lexer is a function, not a class with state
- **Tests alongside implementation** — never ship code without tests
- **Error messages matter** — include source location, context, and suggestions
- **Examples are the spec** — the 5 .sigil files in examples/ are acceptance criteria

## Sigil Language Quick Reference

```sigil
-- Comments start with --
-- Keywords: rule, when, then, and, or, not, if, else, given, define,
--           as, is, exceeds, below, between, any, all, none, in,
--           import, export, module, type, neural, explain, with,
--           true, false, using, from, compute, return, trace, match,
--           for, each, evaluate, main

rule example_rule with priority 10:
  when x exceeds 100
  and y is between 10 and 50
  and status is :active
  then trigger alert with severity :critical
  explain "X exceeded threshold"

compute add from a: Number, b: Number returns Number:
  return a + b

neural classify from text: Text:
  model "classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  fallback to :unknown

type Person is record:
  name: Text
  age: Number

define MAX_TEMP as 100 degrees
```

## What NOT To Do

- **Do not change the syntax philosophy.** Sigil is constrained NL. Do not make it look like Python/Rust/JS.
- **Do not add features not in the current sprint.** Check PRP/ for what's in scope.
- **Do not skip tests.** Every function gets tested. Property-based tests for parser.
- **Do not create abstractions prematurely.** Three similar lines > one premature abstraction.
- **Do not modify examples/ unless the grammar changes.** Examples are the acceptance criteria.
- **Do not use external parser libraries without discussion.** We chose hand-written recursive descent deliberately.
- **Do not implement neural features before symbolic works.** Neural bridge is Phase 3.
