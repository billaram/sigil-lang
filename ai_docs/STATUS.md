# Project Status — KEEP THIS UPDATED

> **Last updated**: 2026-03-06
> **Current phase**: Phase 0 (Foundation) → Phase 1 (Minimal Language)
> **Current sprint**: PRP/mar1-mar15.md
> **Next milestone**: Working lexer + parser for all 5 example programs

---

## What Exists and Works

### Documentation (Complete)
- Full vision, architecture, syntax spec, type system spec, interop design
- Formal PEG grammar (draft — needs validation against examples)
- Operational semantics
- 8 research documents + 65-reference bibliography
- Sprint plan (PRP/mar1-mar15.md)

### Project Infrastructure (Partial)
- [x] Git repo initialized on `main` branch
- [x] `pyproject.toml` with maturin build, dev dependencies, CLI entry point
- [x] `.gitignore`, `LICENSE` (MIT)
- [x] Python package skeleton (`src/sigil/` with empty subpackages)
- [x] CLI scaffold (`src/sigil/cli.py`) — stubs for run/repl/parse/check/fmt
- [ ] `pip install -e ".[dev]"` — NOT YET TESTED
- [ ] Rust crate (`src/sigil_core/`) — NOT YET CREATED
- [ ] CI pipeline — NOT YET CREATED
- [ ] Linting passes — NOT YET TESTED

### Example Programs (5 Complete)
All serve as acceptance criteria for the lexer/parser:
1. `examples/basics/hello.sigil` (9 lines) — minimal rule
2. `examples/basics/temperature.sigil` (35 lines) — multi-rule with priority
3. `examples/rules/loan_eligibility.sigil` (109 lines) — types, rules, compute, neural
4. `examples/neuro_symbolic/medical_triage.sigil` (91 lines) — neural + quantifiers
5. `examples/neuro_symbolic/compliance_checker.sigil` (95 lines) — complex conditions

### Implementation Code
**Nothing is implemented yet.** All `__init__.py` files are empty stubs. The CLI prints "not yet implemented" messages.

---

## What's Being Built Now (Current Sprint: Mar 1–15)

See `PRP/mar1-mar15.md` for full details. Summary:

### Week 1 targets:
- Validate grammar against all 5 examples
- Python dev environment working (pip install, ruff, pytest)
- Rust crate skeleton (Cargo.toml, PyO3 stub)
- **Lexer implementation** with indentation tracking, 50+ tests

### Week 2 targets:
- AST node definitions (dataclasses)
- **Recursive descent parser**, 50+ tests
- Parse all 5 examples successfully
- CLI commands: `sigil lex`, `sigil parse-ast`

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

1. **Grammar gaps**: GRAMMAR.peg has not been validated against examples. Likely has gaps around:
   - `then:` block form (multi-line action)
   - `neural` declaration syntax details
   - Quantifiers (`any X in Y has Z`)
   - Pipeline operator precedence

2. **Indentation edge cases**: Need to decide on:
   - Tab handling (reject? convert?)
   - Continuation lines (how to wrap long `when` conditions)
   - Empty lines inside blocks

3. **Keyword ambiguity**: Words like `in`, `is`, `has`, `with` are both keywords and common identifiers. Need clear context rules.

4. **No initial commit yet**: All files are unstaged. Need first git commit.

---

## Decision Log

| Date | Decision | Rationale | Alternatives Rejected |
|------|----------|-----------|----------------------|
| 2026-03-06 | Name: Sigil | Symbolic mark with power; short; .sigil extension | Synap, Rune, Loom |
| 2026-03-06 | Host: Python + Rust core | Python for ML ecosystem; Rust via PyO3 for perf | Pure Rust, JVM, Zig |
| 2026-03-06 | Syntax: Constrained NL | Readable + parseable + LLM-generable | S-expressions, ML-style, hybrid |
| 2026-03-06 | Impl: Tree-walking first | Proven path; fast iteration | Bytecode VM, transpiler |
| 2026-03-06 | Parser: Hand-written RD | Maximum control; educational; debuggable | PEG library, parser combinators |

---

## How to Update This File

After completing a task or making a decision:
1. Move items from "Being Built" to "What Exists"
2. Add new issues/questions to "Known Issues"
3. Log decisions in "Decision Log"
4. Update the "Last updated" date at top
5. Bump "Current phase" and "Current sprint" as needed
