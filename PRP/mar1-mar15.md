# Sigil — Sprint Plan: March 1–15, 2026

## Where We Are

**Phase 0 (Foundation) is ~80% complete.**

Done:
- Project repo, structure, .gitignore, LICENSE, pyproject.toml
- Vision, Architecture, Syntax spec, Type System spec, Interop design
- PEG grammar draft (GRAMMAR.peg), Operational semantics (SEMANTICS.md)
- 6 research documents + bibliography (65 references)
- 5 example .sigil programs (hello, temperature, loan, triage, compliance)
- CLI scaffold (sigil run/repl/parse/check/fmt — stubs only)
- Python package skeleton (lexer/, parser/, ast/, interpreter/, types/, stdlib/, ffi/)

Not done:
- No actual implementation code (all __init__.py are empty)
- No Rust crate (Cargo.toml, PyO3 skeleton)
- No tests
- No CI
- Grammar not battle-tested against examples

---

## Sprint Goal

> **Close Phase 0 and deliver a working lexer + parser (Phase 1, Milestones 1.1–1.2) that can tokenize and parse all 5 existing example programs into ASTs.**

This is deliberately scoped to be testable, demo-able, and feedback-ready at every step.

---

## Week 1: Mar 1–7 — Close Foundation + Lexer

### Day 1–2: Close Phase 0

- [ ] **P0-1: Validate grammar against examples**
  Walk through each of the 5 .sigil examples line-by-line against GRAMMAR.peg.
  Identify gaps, ambiguities, or unsupported constructs. Fix the grammar.
  _Deliverable: Updated GRAMMAR.peg + notes on changes_

- [ ] **P0-2: Python project bootstrapping**
  - `pip install -e ".[dev]"` works
  - `ruff check` passes on all Python files
  - `pytest` runs (even if 0 tests)
  - `sigil --help` works from CLI
  _Deliverable: Working dev environment_

- [ ] **P0-3: Rust crate skeleton**
  - `src/sigil_core/` with Cargo.toml, lib.rs, PyO3 stub
  - `maturin develop` compiles (even if the crate is empty)
  - Sigil can `import sigil._sigil_core` without error
  _Deliverable: Rust build pipeline connected_

**PAUSE — checkpoint review, gather feedback on grammar/spec**

### Day 3–5: Lexer Implementation (Milestone 1.1)

- [ ] **L1: Token type definitions**
  `src/sigil/lexer/tokens.py` — enum/dataclass for all token types:
  keywords, operators, delimiters, literals, INDENT/DEDENT, NEWLINE, EOF

- [ ] **L2: Core lexer**
  `src/sigil/lexer/lexer.py` — character-by-character scanner:
  - Number literals (int, float, underscore separator)
  - String literals (simple + interpolation placeholders)
  - Symbol literals (`:keyword`)
  - Identifiers and keyword recognition
  - Operators and delimiters
  - Single-line comments (`--`)

- [ ] **L3: Indentation engine**
  Indentation stack tracking, INDENT/DEDENT token emission.
  Handle blank lines, comment-only lines, mixed indent detection.

- [ ] **L4: Unit literal support**
  Recognize `100 degrees`, `50 percent`, `3.5 seconds` as NUMBER + UNIT token pairs.

- [ ] **L5: Lexer tests**
  `tests/lexer/test_lexer.py` — 50+ test cases:
  - Each token type in isolation
  - Full tokenization of `hello.sigil`
  - Full tokenization of `temperature.sigil`
  - Edge cases: empty file, only comments, nested indentation
  - Error cases: unterminated string, invalid character

**PAUSE — run tests, review token stream output on real examples**

### Day 6–7: Lexer polish + buffer

- [ ] **L6: Error reporting**
  Line/column tracking. Helpful error messages on invalid tokens.
  `SigilLexError` exception with source location.

- [ ] **L7: Lexer CLI integration**
  `sigil lex file.sigil` — dumps token stream to stdout (debugging tool).
  Useful for us to inspect and validate before building the parser.

- [ ] **L8: Lex all 5 examples successfully**
  Integration test: tokenize each example, assert no errors, spot-check token counts.

---

## Week 2: Mar 8–15 — Parser (Milestone 1.2)

### Day 8–9: AST Node Definitions

- [ ] **A1: AST node types**
  `src/sigil/ast/nodes.py` — dataclass definitions for:
  - `Program`, `ModuleDecl`, `ImportDecl`
  - `TypeDecl`, `ConstDecl`
  - `RuleDecl`, `Condition`, `Action`, `ExplainClause`
  - `ComputeDecl`, `NeuralDecl`
  - `Expression` variants: `Literal`, `Identifier`, `BinaryOp`, `FieldAccess`, `FuncCall`
  - `Statement` variants: `GivenStmt`, `ReturnStmt`, `IfStmt`, `ForStmt`

- [ ] **A2: AST pretty-printer**
  `ast.dump()` method — prints AST as indented tree (for debugging).
  This is our primary inspection tool during parser development.

**PAUSE — review AST node design, ensure it covers all example programs**

### Day 10–12: Recursive Descent Parser

- [ ] **P1: Parser skeleton**
  `src/sigil/parser/parser.py` — hand-written recursive descent.
  Decision: recursive descent over library-based PEG for maximum control,
  clarity, and educational value. We can switch to a PEG library later if needed.

- [ ] **P2: Top-level parsing**
  Parse module declarations, imports, constant definitions.
  `parse_program()` → `Program` node.

- [ ] **P3: Rule parsing**
  Parse `rule name:` blocks — the core construct.
  - `when` conditions (comparisons: exceeds, is below, is between, is, in)
  - `and`/`or`/`not` combinators
  - `then` actions (simple + block form)
  - `explain` clause
  - `with priority N` metadata

- [ ] **P4: Expression parsing**
  Pratt parser or precedence climbing for expressions:
  - Arithmetic (`+`, `-`, `*`, `/`)
  - Field access (`sensor.temperature`)
  - Function calls (`calculate_rate(applicant)`)
  - Literals, identifiers, lists, records

- [ ] **P5: Compute block parsing**
  Parse `compute name from params:` blocks.
  `given ... as`, `return`, `if/else`, `for each`, `match`.

### Day 13–14: Parser Tests + Integration

- [ ] **P6: Parser tests**
  `tests/parser/test_parser.py` — 50+ test cases:
  - Each construct in isolation (rule, compute, type, import, constant)
  - Condition operator variants
  - Expression precedence
  - Nested blocks (if inside compute inside rule)
  - Error cases: missing colon, bad indentation, incomplete rule

- [ ] **P7: Parse all 5 examples**
  Integration test: parse each .sigil example into AST, assert structure.
  `hello.sigil` — trivial (1 rule)
  `temperature.sigil` — multiple rules with priority
  `loan_eligibility.sigil` — types, rules, compute, everything
  `medical_triage.sigil` — neural declarations, quantifiers
  `compliance_checker.sigil` — complex conditions, list literals

- [ ] **P8: Parser CLI integration**
  `sigil parse-ast file.sigil` — dumps AST to stdout.
  Visual inspection + automated comparison.

**PAUSE — big checkpoint. We now have: source → tokens → AST for all examples.**

### Day 15: Sprint Retrospective + Buffer

- [ ] **R1: Sprint retrospective**
  What worked, what didn't, what surprised us.
  Capture lessons in `PRP/retro-mar1-mar15.md`.

- [ ] **R2: Update ROADMAP.md**
  Mark completed items, adjust estimates for Phase 1 remainder (1.3 AST/types, 1.4 interpreter).

- [ ] **R3: Plan next sprint**
  Draft `PRP/mar16-mar31.md` — targeting interpreter (tree-walking eval + traces).

---

## Definition of Done (Sprint)

At the end of March 15, we should be able to run:

```bash
# Tokenize any example
sigil lex examples/basics/temperature.sigil

# Parse any example into AST
sigil parse-ast examples/rules/loan_eligibility.sigil

# All tests pass
pytest tests/ -v
```

And see clean token streams and well-formed ASTs for all 5 example programs.

---

## Principles for This Sprint

1. **Test before moving on.** Every component gets tests before we build the next layer. No "we'll test later."

2. **Pause points are real.** We stop, inspect output, and discuss before continuing. This catches design issues early.

3. **Examples drive development.** The 5 .sigil examples are the spec. If the lexer/parser can't handle them, we fix the implementation or the grammar — not the examples.

4. **Prefer simple and correct over clever.** Hand-written recursive descent over parser combinator magic. Dataclasses over metaclass tricks. Explicit over implicit.

5. **Ship incrementally.** Each deliverable (grammar fix, lexer, parser) is independently useful and reviewable.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Grammar has gaps not caught by manual review | High | Medium | Lex/parse all 5 examples as integration tests |
| Indentation parsing is trickier than expected | Medium | Medium | Study CPython's tokenizer; keep it simple (spaces only, no tabs) |
| Recursive descent gets messy with NL keywords | Medium | High | Keep parser functions small; one function per grammar rule |
| Rust/maturin setup takes too long | Low | Low | It's a skeleton — if it blocks, defer to next sprint |
| Scope creep into interpreter | Medium | Medium | Hard stop at AST. No evaluation this sprint. |

---

## Files to Create/Modify

### New files
```
src/sigil/lexer/tokens.py        — Token type definitions
src/sigil/lexer/lexer.py         — Lexer implementation
src/sigil/ast/nodes.py           — AST node dataclasses
src/sigil/parser/parser.py       — Recursive descent parser
src/sigil_core/Cargo.toml        — Rust crate config
src/sigil_core/src/lib.rs        — PyO3 stub
tests/lexer/test_lexer.py        — Lexer tests (50+)
tests/parser/test_parser.py      — Parser tests (50+)
tests/conftest.py                — Shared test fixtures
PRP/retro-mar1-mar15.md          — Sprint retrospective (end of sprint)
```

### Modified files
```
docs/spec/GRAMMAR.peg            — Fixes from validation pass
docs/ROADMAP.md                  — Progress updates
pyproject.toml                   — Possible dependency additions
src/sigil/cli.py                 — Add `lex` and `parse-ast` commands
```
