# Project Status — KEEP THIS UPDATED

> **Last updated**: 2026-03-07
> **Current phase**: Phase 2 (Core Language) — Sprints 1 & 2 COMPLETE
> **Completed sprints**: phase2-sprint1.md (Pattern Matching + Pipeline + Closures), phase2-sprint2.md (Module System + Stdlib)
> **Next sprint**: PRP/phase2-sprint3.md (Advanced Rules + Polish)
> **Previous phase**: Phase 1 (Minimal Language) — COMPLETE

---

## What Exists and Works

### Documentation (Complete)
- Full vision, architecture, syntax spec, type system spec, interop design
- Formal PEG grammar (validated against 5 examples — 8 gaps found and fixed in parser)
- Operational semantics
- 8 research documents + 65-reference bibliography
- Sprint plans: `PRP/mar-phase1-sprint1.md` (done), `PRP/mar-phase1-sprint2.md` (done)
- Phase 2 plans: `PRP/phase2-sprint1.md` (done), `PRP/phase2-sprint2.md` (done), `PRP/phase2-sprint3.md`

### Project Infrastructure (Working)
- [x] Git repo initialized on `main` branch
- [x] `pyproject.toml` with maturin build (Rust 1.94.0 + PyO3 0.25)
- [x] `.gitignore`, `LICENSE` (MIT)
- [x] Python package skeleton (`src/sigil/` with all subpackages)
- [x] CLI: `sigil --help`, `sigil lex`, `sigil parse-ast`, `sigil run`, `sigil check`, `sigil repl` all working
- [x] `maturin develop` — builds Rust core + installs Python package
- [x] Virtual environment at `.venv` (Python 3.14.3)
- [x] Rust crate (`src/sigil_core/`) — PyO3 module loading, `__version__` exposed
- [x] Linting passes — `ruff check src/ tests/` clean
- [x] mypy passes — `mypy src/sigil/` clean (0 errors, 25 files)
- [ ] CI pipeline — NOT YET CREATED

### Example Programs (15 Complete)
**Phase 1 examples** (acceptance criteria — all 5 lex, parse, and execute):
1. `examples/basics/hello.sigil` — minimal rule
2. `examples/basics/temperature.sigil` — multi-rule with priority
3. `examples/rules/loan_eligibility.sigil` — types, rules, compute, neural
4. `examples/neuro_symbolic/medical_triage.sigil` — neural + quantifiers
5. `examples/neuro_symbolic/compliance_checker.sigil` — complex conditions

**Phase 2 Sprint 1 examples** (6 new):
6. `examples/features/pattern_matching.sigil` — match expressions
7. `examples/features/pipeline.sigil` — pipeline operator
8. `examples/features/higher_order.sigil` — closures and higher-order functions
9. `examples/features/data_processing.sigil` — data processing with pipelines
10. `examples/features/match_rules.sigil` — match in rule actions
11. `examples/features/functional_pipeline.sigil` — functional pipeline patterns

**Phase 2 Sprint 2 examples** (4 new):
12. `examples/modules/math_demo.sigil` — sigil.math stdlib
13. `examples/modules/text_demo.sigil` — sigil.text stdlib
14. `examples/modules/multi_import.sigil` — multiple stdlib imports
15. `examples/modules/selective_import.sigil` — selective imports (from X import a, b)

### Lexer (Complete — Phase 1)
- `src/sigil/errors.py` — Error hierarchy + SourceLocation
- `src/sigil/lexer/tokens.py` — TokenType enum (80+ keywords), Token dataclass, UNIT_SUFFIXES
- `src/sigil/lexer/lexer.py` — Full tokenizer with indentation engine
- 91 tests, all passing

### Parser (Complete — Phase 1 + Phase 2 enhancements)
- `src/sigil/ast/nodes.py` — Full AST node definitions (40+ frozen dataclasses)
- `src/sigil/parser/parser.py` — Recursive descent parser
- **Phase 2 additions**: Pipeline expression parsing (`|>`), lambda expression parsing, export declaration parsing, keyword-safe dotted name parsing for import paths
- 75+ tests, all passing

### Interpreter (Complete — Phase 1 + Phase 2 enhancements)
- `src/sigil/interpreter/values.py` — Symbol, Record, Variant, Closure, Value union, format_value, values_equal
- `src/sigil/interpreter/environment.py` — Immutable environment with scope chain
- `src/sigil/interpreter/trace.py` — ConditionTrace, RuleTrace, ProgramTrace, TraceTimer, format_trace
- `src/sigil/interpreter/builtins.py` — print, max, min, len builtins
- `src/sigil/interpreter/evaluator.py` — Full tree-walking evaluator (~1230 lines):
  - Expression evaluator (15+ types: literals, field access, binary ops, function calls, match, pipeline, lambda, etc.)
  - Condition evaluator (12 condition types with short-circuit AND/OR)
  - Rule evaluator (priority-based forward chaining, max 100 iterations)
  - Action evaluator (simple, set, block)
  - Statement evaluator (given, return, if, for, becomes, evaluate)
  - Compute function evaluator with return signal
  - Closure/lambda support with lexical scoping
  - Import evaluation with selective, aliased, and full import modes
  - String interpolation in explain clauses
  - Neural stubs (return fallback values)
- `src/sigil/cli.py` — `sigil run` with --input (JSON) and --trace flags, module loader integration

### Module System (Complete — Phase 2 Sprint 2)
- `src/sigil/modules/resolver.py` — Module path resolution (stdlib, python, relative, project-relative)
- `src/sigil/modules/loader.py` — Module loading, caching, circular dependency detection
- `src/sigil/ast/nodes.py` — `ExportDecl` AST node
- Import evaluation in `evaluator.py` — selective (`from X import a, b`), aliased (`import X as Y`), full import
- Export declarations control module visibility
- Circular dependency detection via loading set

### Standard Library (Complete — Phase 2 Sprint 2)
- `src/sigil/stdlib/_builtins.py` — Python-backed stdlib functions:
  - **sigil.math**: sqrt, abs, floor, ceil, round, pow, log, sin, cos, PI, E
  - **sigil.text**: length, substring, split, join, lowercase, uppercase, trim, replace, starts_with, ends_with
  - **sigil.list**: range, reverse, flatten, unique, zip, sum, count, length
  - **sigil.logic**: xor, implies, nand, type_of, is_number, is_text, is_list
- `src/sigil/stdlib/__init__.py` — Registry with `get_stdlib_module()`

### Type Checker (Complete — Phase 1 + Phase 2 enhancements)
- `src/sigil/types/checker.py` — Two-phase type checker (~350 lines):
  - Phase 1: Scan declarations, build symbol table, collect settable names
  - Phase 2: Walk bodies checking for 5+ error types
  - Check #1: Undefined variables
  - Check #2: Undefined fields (on typed compute params)
  - Check #3: Comparison type mismatches
  - Check #4: Function arity
  - Check #5: Duplicate declarations
  - **Phase 2**: Match exhaustiveness check, pipeline validation, lambda type checking

### REPL (Complete — Phase 1)
- `src/sigil/interpreter/repl.py` — Interactive REPL (~200 lines)
- Special commands: `:env`, `:rules`, `:funcs`, `:types`, `:trace`, `:reset`, `:help`

### Test Suite
- **582 tests total**, all passing:
  - 91 lexer tests
  - 75 parser tests (+ 12 pipeline parsing tests)
  - 137 interpreter tests (Phase 1)
  - 15 match expression tests
  - 17 pipeline evaluation tests
  - 18 closure/higher-order function tests
  - 31 REPL tests
  - 39 type checker tests (Phase 1)
  - 12 enhanced type checker tests (Phase 2)
  - 8 Phase 2 Sprint 1 integration tests
  - 27 stdlib unit tests (math)
  - 16 stdlib unit tests (text)
  - 14 stdlib unit tests (list)
  - 19 stdlib unit tests (logic)
  - 16 module resolver tests
  - 17 module loader tests
  - 16 module import integration tests
  - 4 module example integration tests
  - 8 Sprint 1 example integration tests

---

## Grammar Gaps Found and Fixed (Phase 1)

8 gaps between GRAMMAR.peg and the 5 example programs, all handled in the parser:

1. **Space-based field access**: `reading temperature` → `reading.temperature`
2. **Parameterless compute**: `compute NAME returns TYPE:` without `from` clause
3. **`becomes` keyword**: Assignment operator (`y becomes y + [...]`)
4. **`empty list` / `empty`**: Expression for empty collections
5. **`is not assigned`**: Special condition for null/unset checks
6. **Nested inline records**: `vital_signs: record:` inside another record
7. **Actions as variable setting**: `then age_eligible is true` → SetAction
8. **Multi-word actions + positional args**: `trigger alert with severity :high`

## Parser Fixes (Phase 2)

1. **Pipeline vs condition conflict**: Condition parser consuming `|>` tokens. Fixed by using `_parse_additive()` instead of `_parse_expression()` in condition parsing.
2. **Keyword module names**: `list` is a keyword, so `sigil.list` failed dotted name parsing. Fixed with `_expect_identifier_or_keyword()` method.

---

## Phase 2 Plan (3 Sprints)

### Sprint 1: Language Features — COMPLETE
- [x] Match expression evaluation
- [x] Pipeline operator `|>` end-to-end (parser + evaluator)
- [x] Closures and higher-order functions (function values, lambdas)
- [x] Enhanced type checker (match, pipeline, closure checks)
- [x] 6 new examples, 82 new tests → 455 total

### Sprint 2: Module System + Stdlib — COMPLETE
- [x] Module resolver (file system), loader (caching), cycle detection
- [x] Import/export evaluation, visibility
- [x] Standard library: sigil.math, sigil.text, sigil.list, sigil.logic
- [x] Python FFI stubs
- [x] 4 multi-file examples, 127 new tests → 582 total

### Sprint 3: Advanced Rules + Polish (PRP/phase2-sprint3.md)
- Backward chaining engine (goal-driven evaluation)
- Temporal rule foundations (within constraints, stored not enforced)
- Standard library: sigil.time, sigil.trace, sigil.io
- Enhanced type inference (return types, gradual, unit awareness)
- Performance benchmarks
- 80+ new tests → 660+ total

### Phase 3+: See `docs/ROADMAP.md`

---

## Known Issues / Open Questions

1. ~~Rust not installed~~: **Resolved** — Rust 1.94.0 installed, maturin build working with PyO3 0.25
2. ~~Grammar doc needs updating~~: **Resolved** — GRAMMAR.peg v0.2 reflects all 8 parser gaps
3. ~~Pipeline parsing~~: **Resolved** — Full pipeline operator implemented in Phase 2 Sprint 1
4. **CI pipeline**: Not yet set up (GitHub Actions)
5. ~~mypy~~: **Resolved** — 0 errors across 25 source files
6. **Neural stubs**: Phase 1 interpreter uses fallback values, real model loading in Phase 3

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
| 2026-03-07 | Condition parser: _parse_additive() | Prevent pipeline `\|>` tokens from being consumed inside conditions | Allow `_parse_expression()` in conditions |
| 2026-03-07 | Keyword-safe dotted names | Module names like `list` are keywords; import paths must accept them | Rename stdlib modules |

---

## How to Update This File

After completing a task or making a decision:
1. Move items from "Being Built" to "What Exists"
2. Add new issues/questions to "Known Issues"
3. Log decisions in "Decision Log"
4. Update the "Last updated" date at top
5. Bump "Current phase" and "Current sprint" as needed
