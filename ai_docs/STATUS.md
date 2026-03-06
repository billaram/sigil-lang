# Project Status — KEEP THIS UPDATED

> **Last updated**: 2026-03-06
> **Current phase**: Phase 1 (Minimal Language) — Lexer + Parser complete
> **Current sprint**: PRP/mar1-mar15.md
> **Next milestone**: AST ↔ S-expression, type checker, interpreter

---

## What Exists and Works

### Documentation (Complete)
- Full vision, architecture, syntax spec, type system spec, interop design
- Formal PEG grammar (validated against 5 examples — 8 gaps found and fixed in parser)
- Operational semantics
- 8 research documents + 65-reference bibliography
- Sprint plan (PRP/mar1-mar15.md)

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

### Lexer (Complete — 91 tests)
- `src/sigil/errors.py` — Error hierarchy + SourceLocation
- `src/sigil/lexer/tokens.py` — TokenType enum (80+ keywords), Token dataclass, UNIT_SUFFIXES
- `src/sigil/lexer/lexer.py` — Full tokenizer with indentation engine
- Features: numbers (int/float/underscore), strings (regular/triple-quoted/escape), symbols, keywords, operators, delimiters, comments (single/multi/doc/nested), unit suffixes, tabs rejected
- `tests/lexer/test_lexer.py` — 91 tests, all passing

### Parser (Complete — 75 tests)
- `src/sigil/ast/nodes.py` — Full AST node definitions (40+ frozen dataclasses)
- `src/sigil/parser/parser.py` — Recursive descent parser
- Features: all declaration types (type/const/rule/compute/neural/main), conditions (12 variants), expressions (precedence climbing, field access, function calls, pipelines, match), statements (given/return/if/for/becomes/evaluate), actions (simple/set/block)
- `tests/parser/test_parser.py` — 75 tests, all passing
- All 5 examples parse into correct ASTs

### Test Suite
- **166 tests total**, all passing
- `tests/conftest.py` — shared fixtures for all 5 example files
- Lexer: 91 unit + integration tests
- Parser: 75 unit + integration tests

---

## Grammar Gaps Found and Fixed

8 gaps between GRAMMAR.peg and the 5 example programs, all handled in the parser:

1. **Space-based field access**: `reading temperature` → `reading.temperature` (consecutive identifiers as field access)
2. **Parameterless compute**: `compute NAME returns TYPE:` without `from` clause
3. **`becomes` keyword**: Assignment operator (`y becomes y + [...]`)
4. **`empty list` / `empty`**: Expression for empty collections
5. **`is not assigned`**: Special condition for null/unset checks
6. **Nested inline records**: `vital_signs: record:` inside another record
7. **Actions as variable setting**: `then age_eligible is true` → SetAction
8. **Multi-word actions + positional args**: `trigger alert with severity :high`, `log status :normal`

---

## What's Next (After This Sprint)

### Phase 1 remainder (est. 2 more weeks):
- Milestone 1.3: AST ↔ S-expression conversion, basic type checker
- Milestone 1.4: Tree-walking interpreter, REPL, trace generation

### Phase 2: Core Language (est. 6 weeks):
- Compute blocks, control flow, pattern matching
- Module system
- Advanced rules (priority, composition, backward chaining)
- Standard library

### Phase 3+: See `docs/ROADMAP.md`

---

## Known Issues / Open Questions

1. ~~Rust not installed~~: **Resolved** — Rust 1.94.0 installed, maturin build working with PyO3 0.25
2. **Grammar doc needs updating**: `docs/spec/GRAMMAR.peg` should be updated to reflect the 8 gaps found
3. **Pipeline parsing**: Partially implemented but not exercised by current examples
4. **CI pipeline**: Not yet set up (GitHub Actions)
5. **mypy**: Not yet run on the codebase

---

## Decision Log

| Date | Decision | Rationale | Alternatives Rejected |
|------|----------|-----------|----------------------|
| 2026-03-06 | Name: Sigil | Symbolic mark with power; short; .sigil extension | Synap, Rune, Loom |
| 2026-03-06 | Host: Python + Rust core | Python for ML ecosystem; Rust via PyO3 for perf | Pure Rust, JVM, Zig |
| 2026-03-06 | Syntax: Constrained NL | Readable + parseable + LLM-generable | S-expressions, ML-style, hybrid |
| 2026-03-06 | Impl: Tree-walking first | Proven path; fast iteration | Bytecode VM, transpiler |
| 2026-03-06 | Parser: Hand-written RD | Maximum control; educational; debuggable | PEG library, parser combinators |
| 2026-03-06 | Build: setuptools (temp) | Rust not installed; maturin deferred to Phase 2+ | Block on Rust install |
| 2026-03-06 | Grammar: Examples drive spec | 8 grammar gaps found; examples are ground truth | Strict grammar-first |

---

## How to Update This File

After completing a task or making a decision:
1. Move items from "Being Built" to "What Exists"
2. Add new issues/questions to "Known Issues"
3. Log decisions in "Decision Log"
4. Update the "Last updated" date at top
5. Bump "Current phase" and "Current sprint" as needed
