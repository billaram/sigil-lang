# Project Status — KEEP THIS UPDATED

> **Last updated**: 2026-03-06
> **Current phase**: Phase 1 (Minimal Language) — COMPLETE
> **Current sprint**: PRP/mar-phase1-sprint2.md (Type Checker + REPL) — DONE
> **Next milestone**: Phase 2 (Core Language)

---

## What Exists and Works

### Documentation (Complete)
- Full vision, architecture, syntax spec, type system spec, interop design
- Formal PEG grammar (validated against 5 examples — 8 gaps found and fixed in parser)
- Operational semantics
- 8 research documents + 65-reference bibliography
- Sprint plans: `PRP/mar-phase1-sprint1.md` (done), `PRP/mar-phase1-sprint2.md` (active)

### Project Infrastructure (Working)
- [x] Git repo initialized on `main` branch
- [x] `pyproject.toml` with maturin build (Rust 1.94.0 + PyO3 0.25)
- [x] `.gitignore`, `LICENSE` (MIT)
- [x] Python package skeleton (`src/sigil/` with all subpackages)
- [x] CLI: `sigil --help`, `sigil lex`, `sigil parse-ast` all working
- [x] `maturin develop` — builds Rust core + installs Python package
- [x] Virtual environment at `.venv` (Python 3.14.3)
- [x] Rust crate (`src/sigil_core/`) — PyO3 module loading, `__version__` exposed
- [x] Linting passes — `ruff check src/ tests/` clean
- [ ] CI pipeline — NOT YET CREATED

### Example Programs (5 Complete)
All serve as acceptance criteria — all 5 lex and parse successfully:
1. `examples/basics/hello.sigil` (9 lines) — minimal rule
2. `examples/basics/temperature.sigil` (35 lines) — multi-rule with priority
3. `examples/rules/loan_eligibility.sigil` (109 lines) — types, rules, compute, neural
4. `examples/neuro_symbolic/medical_triage.sigil` (91 lines) — neural + quantifiers
5. `examples/neuro_symbolic/compliance_checker.sigil` (95 lines) — complex conditions

### Lexer (Complete — Sprint 1)
- `src/sigil/errors.py` — Error hierarchy + SourceLocation
- `src/sigil/lexer/tokens.py` — TokenType enum (80+ keywords), Token dataclass, UNIT_SUFFIXES
- `src/sigil/lexer/lexer.py` — Full tokenizer with indentation engine
- 91 tests, all passing

### Parser (Complete — Sprint 1)
- `src/sigil/ast/nodes.py` — Full AST node definitions (40+ frozen dataclasses)
- `src/sigil/parser/parser.py` — Recursive descent parser
- 75 tests, all passing, all 5 examples parse correctly

### Interpreter (Complete — Sprint 2)
- `src/sigil/interpreter/values.py` — Symbol, Record, Variant, Value union, format_value, values_equal
- `src/sigil/interpreter/environment.py` — Immutable environment with scope chain
- `src/sigil/interpreter/trace.py` — ConditionTrace, RuleTrace, ProgramTrace, TraceTimer, format_trace
- `src/sigil/interpreter/builtins.py` — print, max, min, len builtins
- `src/sigil/interpreter/evaluator.py` — Full tree-walking evaluator (~930 lines):
  - Expression evaluator (12+ types: literals, field access, binary ops, function calls, etc.)
  - Condition evaluator (12 condition types with short-circuit AND/OR)
  - Rule evaluator (priority-based forward chaining, max 100 iterations)
  - Action evaluator (simple, set, block)
  - Statement evaluator (given, return, if, for, becomes, evaluate)
  - Compute function evaluator with return signal
  - String interpolation in explain clauses
  - Neural stubs (return fallback values)
  - All 5 example programs execute correctly
- `src/sigil/cli.py` — `sigil run` with --input (JSON) and --trace flags
- All 5 example programs execute correctly

### Type Checker (Complete — Sprint 2)
- `src/sigil/types/checker.py` — Two-phase type checker (~300 lines):
  - Phase 1: Scan declarations, build symbol table, collect settable names
  - Phase 2: Walk bodies checking for 5 error types
  - Check #1: Undefined variables (with conservative scope: builtins, declarations, settable names, field-access bases)
  - Check #2: Undefined fields (on typed compute params with record type annotations)
  - Check #3: Comparison type mismatches (non-numeric operands in numeric comparisons)
  - Check #4: Function arity (compute, neural, builtin)
  - Check #5: Duplicate declarations
  - All 5 example programs pass with zero errors
- `src/sigil/cli.py` — `sigil check` command with diagnostics output

### REPL (Complete — Sprint 2)
- `src/sigil/interpreter/repl.py` — Interactive REPL (~200 lines):
  - `ReplSession` class with persistent state (env, rules, compute funcs, types)
  - Input classification: declarations parse as-is, statements/expressions wrapped in main block
  - Multi-line detection (colon continuation, unbalanced brackets)
  - Special commands: `:env`, `:rules`, `:funcs`, `:types`, `:trace`, `:reset`, `:help`
  - Error recovery: lex/parse/runtime errors caught and printed, REPL continues
- `src/sigil/interpreter/evaluator.py` — `eval_program_repl()` method for persistent evaluation
- `src/sigil/cli.py` — `sigil repl` command

### Test Suite
- **373 tests total**, all passing:
  - 91 lexer tests
  - 75 parser tests
  - 137 interpreter tests (values, environment, evaluator, integration)
  - 31 REPL tests (session, declarations, commands, errors, multi-line)
  - 39 type checker tests (5 checks + integration with all 5 examples)

---

## Grammar Gaps Found and Fixed (Sprint 1)

8 gaps between GRAMMAR.peg and the 5 example programs, all handled in the parser:

1. **Space-based field access**: `reading temperature` → `reading.temperature`
2. **Parameterless compute**: `compute NAME returns TYPE:` without `from` clause
3. **`becomes` keyword**: Assignment operator (`y becomes y + [...]`)
4. **`empty list` / `empty`**: Expression for empty collections
5. **`is not assigned`**: Special condition for null/unset checks
6. **Nested inline records**: `vital_signs: record:` inside another record
7. **Actions as variable setting**: `then age_eligible is true` → SetAction
8. **Multi-word actions + positional args**: `trigger alert with severity :high`

---

## What's After Phase 1

### Phase 2: Core Language (est. 6 weeks):
- Advanced compute: pattern matching, closures, pipeline operator
- Module system: imports, exports, circular dependency detection
- Advanced rules: backward chaining, temporal rules
- Standard library: math, text, logic, time, trace, io, types

### Phase 3+: See `docs/ROADMAP.md`

---

## Known Issues / Open Questions

1. ~~Rust not installed~~: **Resolved** — Rust 1.94.0 installed, maturin build working with PyO3 0.25
2. **Grammar doc needs updating**: `docs/spec/GRAMMAR.peg` should reflect the 8 gaps found
3. **Pipeline parsing**: Partially implemented but not exercised by current examples
4. **CI pipeline**: Not yet set up (GitHub Actions)
5. **mypy**: Not yet run on the codebase
6. **Neural stubs**: Phase 1 interpreter will use fallback values, real model loading in Phase 3

---

## Decision Log

| Date | Decision | Rationale | Alternatives Rejected |
|------|----------|-----------|----------------------|
| 2026-03-06 | Name: Sigil | Symbolic mark with power; short; .sigil extension | Synap, Rune, Loom |
| 2026-03-06 | Host: Python + Rust core | Python for ML ecosystem; Rust via PyO3 for perf | Pure Rust, JVM, Zig |
| 2026-03-06 | Syntax: Constrained NL | Readable + parseable + LLM-generable | S-expressions, ML-style, hybrid |
| 2026-03-06 | Impl: Tree-walking first | Proven path; fast iteration | Bytecode VM, transpiler |
| 2026-03-06 | Parser: Hand-written RD | Maximum control; educational; debuggable | PEG library, parser combinators |
| 2026-03-06 | Build: maturin + PyO3 0.25 | Rust 1.94.0 installed; Python 3.14 support | setuptools (used temporarily) |
| 2026-03-06 | Grammar: Examples drive spec | 8 grammar gaps found; examples are ground truth | Strict grammar-first |
| 2026-03-06 | Type checker: Light for Phase 1 | Catch obvious errors, defer full inference to Phase 2 | Full gradual types upfront |

---

## How to Update This File

After completing a task or making a decision:
1. Move items from "Being Built" to "What Exists"
2. Add new issues/questions to "Known Issues"
3. Log decisions in "Decision Log"
4. Update the "Last updated" date at top
5. Bump "Current phase" and "Current sprint" as needed
