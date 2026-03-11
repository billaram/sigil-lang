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

## Architecture Decisions

@ai_docs/ARCHITECTURE_DECISIONS.md

## Project Structure

```
sigil-lang/
├── CLAUDE.md                       ← YOU ARE HERE
├── .claude/
│   ├── rules/                      ← Path-scoped context (auto-loaded per subsystem)
│   ├── skills/                     ← Reusable workflows (/run-tests, /fix-issue, etc.)
│   └── agents/                     ← Specialist subagents (compiler, neuro-symbolic, etc.)
├── ai_docs/                        ← Deep context for Claude Code sessions
│   ├── CONVENTIONS.md              ← Code style, naming, patterns
│   ├── ARCHITECTURE_DECISIONS.md   ← Why we chose what we chose
│   └── STATUS.md                   ← Current state, what works, what doesn't
├── PRP/                            ← Sprint plans and retrospectives
├── docs/
│   ├── VISION.md                   ← Grand vision
│   ├── ARCHITECTURE.md             ← Technical architecture
│   ├── ROADMAP.md                  ← Full 5-phase plan
│   ├── design/                     ← SYNTAX.md, TYPE_SYSTEM.md, INTEROP.md
│   ├── spec/                       ← GRAMMAR.peg, SEMANTICS.md
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
├── tests/                          ← pytest test suite (665 tests)
└── examples/                       ← .sigil example programs (18 files)
```

## Development Commands

```bash
# Setup
pip install -e ".[dev]"           # Install in dev mode
maturin develop                    # Build Rust core

# Run
sigil run file.sigil               # Execute a program
sigil repl                         # Interactive REPL
sigil lex file.sigil               # Dump token stream
sigil parse-ast file.sigil         # Dump AST

# Test
pytest tests/ -v                   # Run all tests
pytest tests/<subsystem>/ -v       # Subsystem tests only
ruff check src/                    # Lint
mypy src/sigil/                    # Type check

# Format
ruff format src/ tests/            # Auto-format
```

## Context Loading

Context is loaded automatically via `.claude/rules/` based on which files you're editing:
- **Lexer/parser work** → `sigil-syntax.md`, `lexer.md`, `parser.md` auto-load
- **Interpreter work** → `interpreter.md` auto-loads
- **Type checker work** → `typechecker.md` auto-loads
- **Module/stdlib work** → `modules.md`, `stdlib.md` auto-load
- **Test work** → `testing.md` auto-loads
- **All work** → `code-conventions.md`, `known-issues.md` always loaded

For deeper context, read: `ai_docs/STATUS.md`, `docs/design/SYNTAX.md`, `docs/spec/GRAMMAR.peg`

## Skills (Reusable Workflows)

- `/run-tests [subsystem]` — Run pytest with right flags
- `/validate-examples` — Run all .sigil examples
- `/fix-issue` — Structured reproduce→diagnose→test→fix→verify workflow
- `/update-status` — Update ai_docs/STATUS.md after completing work
- `/add-syntax` — 10-step workflow for adding new language syntax
- `/new-sprint` — Create sprint plan from template

## Specialist Agents

- **compiler-expert** — Lexer, parser, AST, grammar
- **neuro-symbolic-expert** — Rule engines, chaining, neural bridge, semantics
- **testing-qa** — Test writing, coverage, property-based testing
- **code-reviewer** — Read-only code review (uses haiku for speed)

## What NOT To Do

- **Do not change the syntax philosophy.** Sigil is constrained NL. Do not make it look like Python/Rust/JS.
- **Do not add features not in the current sprint.** Check PRP/ for what's in scope.
- **Do not skip tests.** Every function gets tested. Property-based tests for parser.
- **Do not create abstractions prematurely.** Three similar lines > one premature abstraction.
- **Do not modify examples/ unless the grammar changes.** Examples are the acceptance criteria.
- **Do not use external parser libraries without discussion.** We chose hand-written recursive descent deliberately.
- **Do not implement neural features before symbolic works.** Neural bridge is Phase 3.
