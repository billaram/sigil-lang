# Sigil: Development Roadmap

## Overview

Sigil development follows an iterative, milestone-driven approach. Each phase produces a working artifact — the language grows incrementally from a minimal interpreter to a full production system.

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
Foundation   Minimal     Core        Ecosystem   Production  Advanced
(2 weeks)    Language    Language    Integration  Readiness   Features
             (4 weeks)   (6 weeks)   (4 weeks)   (4 weeks)   (ongoing)
```

---

## Phase 0: Foundation (Weeks 1-2)
**Goal**: Project scaffolding, research synthesis, language specification

### Deliverables
- [x] Project repository and structure
- [x] Vision document (VISION.md)
- [x] Architecture document (ARCHITECTURE.md)
- [x] Syntax specification (SYNTAX.md)
- [x] Interop design (INTEROP.md)
- [x] Research foundations (FOUNDATIONS.md)
- [ ] Formal PEG grammar (GRAMMAR.peg)
- [ ] Operational semantics (SEMANTICS.md)
- [ ] Type system specification (TYPE_SYSTEM.md)
- [ ] Python project setup (pyproject.toml, CI, linting)
- [ ] Rust crate setup (Cargo.toml, PyO3 skeleton)

### Exit Criteria
- Grammar specification reviewed and finalized
- Build system compiles both Python and Rust components
- CI pipeline runs (even with no tests yet)

---

## Phase 1: Minimal Language (Weeks 3-6)
**Goal**: A working interpreter that can lex, parse, and evaluate basic Sigil programs

### Milestone 1.1: Lexer (Week 3)
```
Input: raw Sigil source text
Output: token stream
```

- [ ] Token type definitions (all ~30 keywords + operators + literals)
- [ ] Indentation tracking (INDENT/DEDENT tokens)
- [ ] String interpolation tokenization
- [ ] Unit literal recognition (`100 degrees`, `50 percent`)
- [ ] Comment handling (single-line, multi-line, doc comments)
- [ ] Error reporting with line/column numbers
- [ ] **Tests**: 50+ lexer test cases

### Milestone 1.2: Parser (Week 4)
```
Input: token stream
Output: AST
```

- [ ] PEG parser implementation (hand-written recursive descent or library-based)
- [ ] Rule declaration parsing
- [ ] Condition expression parsing (when/and/or/not)
- [ ] Comparison operators (exceeds, is below, is between, etc.)
- [ ] Literal parsing (numbers, strings, symbols, units, lists, records)
- [ ] Type declaration parsing
- [ ] Compute block parsing
- [ ] Import statement parsing
- [ ] Error recovery (produce partial AST from malformed input)
- [ ] **Tests**: 50+ parser test cases

### Milestone 1.3: AST & Type Checker (Week 5)
```
Input: untyped AST
Output: typed AST
```

- [ ] AST node definitions (dataclasses or attrs)
- [ ] Surface AST ↔ Core AST (S-expression) conversion
- [ ] Basic type inference (literals, operators)
- [ ] Type checking for rule conditions
- [ ] Unit type checking (catch unit mismatches)
- [ ] Pretty-printer (AST → Sigil source)
- [ ] **Tests**: 30+ type checker test cases

### Milestone 1.4: Tree-Walking Interpreter (Week 6)
```
Input: typed AST + input facts
Output: decision + trace
```

- [ ] Environment (scope, binding, lookup)
- [ ] Rule evaluation (condition matching, action execution)
- [ ] Forward chaining (facts → conclusions)
- [ ] Basic trace generation
- [ ] REPL (interactive Sigil shell)
- [ ] CLI runner (`sigil run file.sigil`)
- [ ] **Tests**: 50+ interpreter test cases

### Phase 1 Exit Criteria
- Can lex, parse, type-check, and evaluate this program:
  ```sigil
  rule temperature_check:
    when temperature exceeds 100
    and status is :active
    then alert with severity :critical
  ```
- REPL works interactively
- 180+ tests passing
- Execution trace produced for every rule evaluation

---

## Phase 2: Core Language (Weeks 7-12)
**Goal**: Full language features — functions, modules, neural declarations, standard library

### Milestone 2.1: Compute Blocks & Control Flow (Weeks 7-8)
- [ ] Function definitions (`compute ... from ... returns ...`)
- [ ] Pattern matching (`match ... :`)
- [ ] Conditional expressions (`if/else if/else`)
- [ ] Iteration (`for each ... in ...`)
- [ ] Pipeline operator (`|> filter, |> map, |> sort`)
- [ ] Let bindings (`given ... as ...`)
- [ ] Closures and higher-order functions
- [ ] **Tests**: 60+ test cases

### Milestone 2.2: Module System (Week 9)
- [ ] Module declaration and resolution
- [ ] Import/export mechanism
- [ ] Circular dependency detection
- [ ] Private/public visibility
- [ ] Module caching
- [ ] **Tests**: 30+ test cases

### Milestone 2.3: Advanced Rules (Week 10)
- [ ] Rule priority and conflict resolution
- [ ] Rule composition (rules referencing other rules)
- [ ] Backward chaining (goal-driven evaluation)
- [ ] Quantifiers (any/all/none over collections)
- [ ] Temporal rules (`when X for duration Y then Z`)
- [ ] Rule metadata (version, author, tags)
- [ ] **Tests**: 40+ test cases

### Milestone 2.4: Standard Library (Weeks 11-12)
- [ ] `sigil.math` — arithmetic, statistics, rounding
- [ ] `sigil.text` — string operations, regex, formatting
- [ ] `sigil.logic` — boolean algebra, constraint helpers
- [ ] `sigil.time` — temporal operations, duration arithmetic
- [ ] `sigil.trace` — trace formatting, filtering, export (JSON, table)
- [ ] `sigil.io` — file reading, basic HTTP
- [ ] `sigil.types` — type constructors, validators
- [ ] **Tests**: 80+ test cases (stdlib)

### Phase 2 Exit Criteria
- Full loan eligibility example runs end-to-end
- Module system works across files
- Standard library covers basic operations
- 400+ total tests passing

---

## Phase 3: Ecosystem Integration (Weeks 13-16)
**Goal**: Python FFI, Rust core, neural bridge — Sigil connects to the real world

### Milestone 3.1: Python FFI (Week 13)
- [ ] `import python` statement execution
- [ ] Type marshaling (Sigil ↔ Python)
- [ ] Python function wrapping with Sigil types
- [ ] Inline Python blocks
- [ ] Error translation (Python exceptions → Sigil errors)
- [ ] **Tests**: 30+ FFI test cases

### Milestone 3.2: Neural Bridge (Week 14)
- [ ] `neural` declaration implementation
- [ ] Model registry and loading
- [ ] Confidence type and threshold enforcement
- [ ] Mandatory fallback execution
- [ ] Neural/symbolic trace distinction
- [ ] Integration with HuggingFace transformers
- [ ] **Tests**: 20+ neural bridge test cases

### Milestone 3.3: Rust Core (Weeks 15-16)
- [ ] PyO3 skeleton and maturin build
- [ ] Constraint solver in Rust
- [ ] Pattern matcher (basic Rete) in Rust
- [ ] Trace serialization in Rust
- [ ] `using rust` directive in interpreter
- [ ] Benchmark: Rust vs Python execution paths
- [ ] **Tests**: 30+ Rust core test cases

### Phase 3 Exit Criteria
- Python libraries callable from Sigil
- Neural declarations work with real models
- Rust core provides measurable speedup (>10x on benchmarks)
- 500+ total tests passing

---

## Phase 4: Production Readiness (Weeks 17-20)
**Goal**: Error handling, tooling, documentation, packaging — ready for real users

### Milestone 4.1: Error Experience (Week 17)
- [ ] Rich error messages with context and suggestions
- [ ] Error recovery in parser (continue after errors)
- [ ] Warning system (unused rules, unreachable conditions)
- [ ] Stack traces that map to Sigil source lines

### Milestone 4.2: Developer Tooling (Week 18)
- [ ] Formatter (`sigil fmt`)
- [ ] Linter (`sigil lint`) — unused rules, type warnings
- [ ] REPL improvements (history, autocomplete, multi-line)
- [ ] Tree-sitter grammar for editor syntax highlighting

### Milestone 4.3: NL-to-Sigil Generator (Week 19)
- [ ] LLM-powered natural language → Sigil translation
- [ ] Prompt engineering for Sigil generation
- [ ] Validation pipeline (parse → type-check → verify generated code)
- [ ] Interactive refinement loop
- [ ] `sigil parse "natural language description"` CLI command

### Milestone 4.4: Packaging & Documentation (Week 20)
- [ ] PyPI package (`pip install sigil-lang`)
- [ ] Comprehensive user guide
- [ ] API reference (auto-generated)
- [ ] Tutorial series (5 tutorials)
- [ ] Example programs (10+)
- [ ] Contributing guide

### Phase 4 Exit Criteria
- Package installable via pip
- 10+ working examples
- Documentation covers all language features
- NL-to-Sigil generation works for basic rule descriptions
- 600+ total tests passing

---

## Phase 5: Advanced Features (Ongoing)
**Goal**: Performance, scale, and ecosystem growth

### 5.1: Bytecode VM
- Stack-based bytecode compiler
- VM interpreter in Rust
- 10-100x performance improvement over tree-walking

### 5.2: LSP Server
- Language Server Protocol implementation
- VS Code extension
- Real-time diagnostics, autocomplete, go-to-definition

### 5.3: WASM Target
- Compile Sigil programs to WebAssembly
- Browser-based Sigil execution
- Edge deployment (Cloudflare Workers, Deno Deploy)

### 5.4: Distributed Execution
- Rule partitioning across nodes
- Shared fact space with consistency guarantees
- Millions of decisions per second

### 5.5: Formal Verification
- Rule completeness checking (are all cases covered?)
- Conflict detection (do rules contradict each other?)
- Termination analysis (do rule chains always halt?)
- Integration with SMT solvers (Z3)

### 5.6: Visual Rule Builder
- Web-based visual editor for Sigil rules
- Drag-and-drop rule composition
- Live trace visualization
- Collaborative editing

---

## Testing Strategy

| Phase | Unit Tests | Integration Tests | Property Tests | Benchmarks |
|-------|-----------|-------------------|---------------|------------|
| 1 | 180+ | 10+ | - | - |
| 2 | 400+ | 30+ | 20+ | - |
| 3 | 500+ | 50+ | 30+ | 10+ |
| 4 | 600+ | 80+ | 40+ | 20+ |

**Testing principles:**
- Every language feature has explicit test cases
- Integration tests use real-world examples (loan, triage, compliance)
- Property-based tests (hypothesis) for parser and type checker
- Benchmarks track performance regression

## Success Metrics

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| Test count | 180+ | 400+ | 500+ | 600+ |
| Example programs | 5 | 10 | 15 | 20+ |
| Rule eval latency | <10ms | <5ms | <1ms (Rust) | <1ms |
| Parse latency | <50ms | <20ms | <10ms | <10ms |
| NL→Sigil accuracy | - | - | - | >80% |
| Docs pages | 5 | 10 | 15 | 20+ |
