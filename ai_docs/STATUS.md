# Project Status — KEEP THIS UPDATED

> **Last updated**: 2026-03-12
> **Current phase**: Phase 4 (Production Readiness) — COMPLETE (all 5 sprints)
> **Completed sprints**: Phase 1, Phase 2 (3 sprints), Phase 3 (3 sprints + Neural Bridge v2), Phase 4 (5 sprints)
> **Next**: Phase 5 — see docs/ROADMAP.md
> **Previous phases**: Phase 1 — COMPLETE, Phase 2 — COMPLETE, Phase 3 — COMPLETE

---

## What Exists and Works

### Documentation (Complete)
- Full vision, architecture, syntax spec, type system spec, interop design
- Formal PEG grammar (validated against 5 examples — 8 gaps found and fixed in parser)
- Operational semantics
- 8 research documents + 65-reference bibliography
- Sprint plans: `PRP/mar-phase1-sprint1.md` (done), `PRP/mar-phase1-sprint2.md` (done)
- Phase 2 plans: `PRP/phase2-sprint1.md` (done), `PRP/phase2-sprint2.md` (done), `PRP/phase2-sprint3.md`
- Phase 3 plan: `PRP/phase3-plan.md`
- `docs/SIGIL_CODE_EXAMPLES.md` — Sigil Code interactive agent usage examples

### Project Infrastructure (Working)
- [x] Git repo initialized on `main` branch
- [x] `pyproject.toml` with maturin build (Rust 1.94.0 + PyO3 0.25)
- [x] `.gitignore`, `LICENSE` (MIT)
- [x] Python package skeleton (`src/sigil/` with all subpackages)
- [x] CLI: `sigil --help`, `sigil lex`, `sigil parse-ast`, `sigil run`, `sigil check`, `sigil repl`, `sigil fmt`, `sigil lint`, `sigil parse`, `sigil code` all working
- [x] `maturin develop` — builds Rust core + installs Python package
- [x] Virtual environment at `.venv` (Python 3.14.3)
- [x] Rust crate (`src/sigil_core/`) — ReteNetwork, ConstraintSolver, trace serialization
- [x] Linting passes — `ruff check src/ tests/` clean
- [x] mypy passes — `mypy src/sigil/` clean (0 errors, 25 files)
- [x] CI pipeline — `.github/workflows/ci.yml` (Python 3.11-3.13, lint, test)

### Example Programs (20 Complete)
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

**Phase 2 Sprint 3 examples** (3 new):
16. `examples/rules/backward_chaining.sigil` — can-fly bird logic with query
17. `examples/advanced/temporal_monitor.sigil` — temperature monitoring with `within`
18. `examples/advanced/proof_tree.sigil` — multi-level backward chaining proof

**Phase 3 examples** (2 new):
19. `examples/interop/python_math.sigil` — Python FFI (math + json imports)
20. `examples/interop/rust_speedup.sigil` — Rust core rule matching
21. `examples/neuro_symbolic/sentiment_analysis.sigil` — Neural bridge with HF model

**Phase 4 examples** (4 new):
22. `examples/getting_started/hello.sigil` — Minimal first program
23. `examples/getting_started/calculator.sigil` — Compute functions
24. `examples/patterns/priority_rules.sigil` — Conflict resolution
25. `examples/patterns/backward_chaining.sigil` — Query-driven evaluation

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

### Backward Chaining Engine (Complete — Phase 2 Sprint 3)
- `src/sigil/interpreter/backward.py` — Goal-driven rule evaluation:
  - ProofNode dataclass for proof tree representation
  - BackwardChainer class: rule index, recursive goal proving, cycle detection (max depth 50)
  - Proof trees recorded in ProgramTrace for auditability
  - `query` statement in evaluator wires into backward chainer

### Interpreter (Complete — Phase 1 + Phase 2 + Phase 3 enhancements)
- `src/sigil/interpreter/values.py` — Symbol, Record, Variant, Closure, Value union, format_value, values_equal
- `src/sigil/interpreter/environment.py` — Immutable environment with scope chain
- `src/sigil/interpreter/trace.py` — ConditionTrace, RuleTrace, NeuralTrace, ProgramTrace, TraceTimer, format_trace
- `src/sigil/interpreter/builtins.py` — print, max, min, len builtins
- `src/sigil/interpreter/evaluator.py` — Full tree-walking evaluator (~1300 lines):
  - Expression evaluator (15+ types: literals, field access, binary ops, function calls, match, pipeline, lambda, etc.)
  - Condition evaluator (12 condition types with short-circuit AND/OR)
  - Rule evaluator (priority-based forward chaining, max 100 iterations)
  - Action evaluator (simple, set, block)
  - Statement evaluator (given, return, if, for, becomes, evaluate)
  - Compute function evaluator with return signal
  - Closure/lambda support with lexical scoping
  - Import evaluation with selective, aliased, and full import modes
  - **Python FFI imports** — `import python X` loads real Python modules via importlib
  - **Neural bridge** — `_call_neural()` uses ModelRegistry with confidence thresholds and fallbacks
  - String interpolation in explain clauses
- `src/sigil/cli.py` — `sigil run` with --input (JSON) and --trace flags, module loader integration

### Python FFI (Complete — Phase 3 Sprint 1)
- `src/sigil/ffi/marshal.py` — Bidirectional type marshaling: Sigil ↔ Python
  - `sigil_to_python()`, `python_to_sigil()`, `wrap_python_callable()`
  - Handles: int, float, str, bool, None, Symbol→str, Record→dict, list, callable wrapping
- `src/sigil/ffi/python_interop.py` — Python module importer
  - `import_python_module()` — importlib-based, marshals public API
  - `import_python_names()` — selective imports
  - Graceful degradation: missing modules bind empty record (errors on use, not import)
- `src/sigil/ffi/errors.py` — Error translation (Python exceptions → SigilRuntimeError)
- 45 tests (15 marshal, 15 interop, 5 errors, 10 end-to-end)

### Neural Bridge (Complete — Phase 3 Sprint 2 + v2 Enhancement)
- `src/sigil/neural/backend.py` — `ModelBackend` protocol, `ModelResult`, `NeuralConfig`, `CandidateResult`
- `src/sigil/neural/registry.py` — `ModelRegistry` singleton with prefix-based backend routing + timeout enforcement
  - Built-in prefixes: `hf:`, `mock:`, `claude:`, `openai:`, `onnx:`, `python:`
  - Lazy model loading, caching, thread-based timeout
- `src/sigil/neural/huggingface.py` — HuggingFace Transformers backend
  - Text-classification + zero-shot-classification (with `labels` field)
  - Pipeline caching by (model_id, task_type)
- `src/sigil/neural/anthropic_backend.py` — Anthropic Claude backend (requires `anthropic` SDK)
- `src/sigil/neural/openai_backend.py` — OpenAI GPT backend (requires `openai` SDK)
- `src/sigil/neural/onnx_backend.py` — ONNX Runtime backend (requires `onnxruntime`)
- `src/sigil/neural/python_callable.py` — Python callable backend (dotted path to function)
- `src/sigil/neural/mock_backend.py` — Deterministic mock backend (echo, fail, low_confidence, fixed)
- `src/sigil/interpreter/evaluator.py` — `_build_neural_config()` extracts all NeuralDecl fields into NeuralConfig
- `src/sigil/interpreter/trace.py` — `NeuralTrace` dataclass, rendered in `format_trace()`
- `NeuralConfig` supports: labels, hypothesis_template, system_prompt, temperature, max_tokens, top_p, top_k, stop_sequences, output_schema, num_candidates, beam_size, timeout_seconds
- 76 tests (5 config, 5 backend, 7 registry, 8 HuggingFace, 8 Anthropic, 9 OpenAI, 4 ONNX, 6 Python callable, 6 mock, 18 integration)

### Rust Core (Complete — Phase 3 Sprint 3)
- `src/sigil_core/src/values.rs` — `SigilValue` Rust enum with `from_python()`/`to_python()` + serde
- `src/sigil_core/src/matcher.rs` — Rete-lite pattern matcher
  - `ReteNetwork` PyO3 class: add rules, match facts, priority sorting
  - 6 condition operators: equals, not-equals, greater/less than, between, contains
- `src/sigil_core/src/solver.rs` — Constraint solver
  - `ConstraintSolver` PyO3 class: equals, not-equals, greater/less, between, one-of
  - `check()` returns violation list, `is_satisfied()` convenience method
- `src/sigil_core/src/trace.rs` — Trace serialization
  - `serialize_trace_json()` (pretty), `serialize_trace_compact()` (no whitespace)
  - Handles rule traces, neural traces, output lines, duration
- `Cargo.toml` — serde + serde_json dependencies
- Benchmarks: `benchmarks/bench_rust_vs_python.py`
  - Pattern matching: ~2.4x speedup (release mode, 50 rules)
  - Trace serialization: ~1.3x speedup (release mode)
  - Constraint solving: marshaling overhead dominates at small scale
- 30 tests (13 matcher, 12 solver, 5 trace)

### Module System (Complete — Phase 2 Sprint 2)
- `src/sigil/modules/resolver.py` — Module path resolution (stdlib, python, relative, project-relative)
- `src/sigil/modules/loader.py` — Module loading, caching, circular dependency detection
- `src/sigil/ast/nodes.py` — `ExportDecl` AST node
- Import evaluation in `evaluator.py` — selective (`from X import a, b`), aliased (`import X as Y`), full import
- Export declarations control module visibility
- Circular dependency detection via loading set

### Standard Library (Complete — Phase 2 Sprint 2 + 3)
- `src/sigil/stdlib/_builtins.py` — Python-backed stdlib functions:
  - **sigil.math**: sqrt, abs, floor, ceil, round, pow, log, sin, cos, PI, E
  - **sigil.text**: length, substring, split, join, lowercase, uppercase, trim, replace, starts_with, ends_with
  - **sigil.list**: range, reverse, flatten, unique, zip, sum, count, length
  - **sigil.logic**: xor, implies, nand, type_of, is_number, is_text, is_list
  - **sigil.time**: now, now_ms, format_timestamp, elapsed, duration_seconds
  - **sigil.trace**: to_json, fired_rules, rule_count, duration_ms
  - **sigil.io**: read_file, write_file, file_exists, parse_json, to_json
- `src/sigil/stdlib/__init__.py` — Registry with `get_stdlib_module()`

### Type Checker (Complete — Phase 1 + Phase 2 enhancements)
- `src/sigil/types/checker.py` — Two-phase type checker (~550 lines):
  - Phase 1: Scan declarations, build symbol table, collect settable names
  - Phase 2: Walk bodies checking for 11 error/warning types
  - Check #1: Undefined variables
  - Check #2: Undefined fields (on typed compute params)
  - Check #3: Comparison type mismatches
  - Check #4: Function arity
  - Check #5: Duplicate declarations
  - Check #6: Match exhaustiveness (Phase 2 Sprint 1)
  - Check #7: Pipeline validation (Phase 2 Sprint 1)
  - Check #8: Lambda type checking (Phase 2 Sprint 1)
  - Check #9: Return type consistency (Phase 2 Sprint 3)
  - Check #10: Gradual type inference from given literals (Phase 2 Sprint 3)
  - Check #11: Unit awareness — warn on unit suffix mismatches (Phase 2 Sprint 3)

### REPL (Enhanced — Phase 4)
- `src/sigil/interpreter/repl.py` — Interactive REPL (~320 lines)
- Special commands: `:env`, `:rules`, `:funcs`, `:types`, `:trace`, `:reset`, `:help`
- Readline history persistence to `~/.sigil_history`
- Tab completion: keywords, commands, stdlib modules, bound variables

### Error Experience (Complete — Phase 4 Sprint 1)
- `src/sigil/errors.py` — All errors support `suggestion` field rendered as `hint:`
- `SigilParseErrors` — Multi-error collection from panic-mode parser recovery
- `SigilRuntimeError` — Call stack tracking with source-mapped tracebacks
- Parser: panic-mode synchronization, recovers at declaration boundaries
- Evaluator: "did you mean?" via Levenshtein distance for undefined functions
- Type checker: unused compute/constant declaration warnings

### Formatter (Complete — Phase 4 Sprint 2)
- `src/sigil/formatter/formatter.py` — AST→source round-trip formatter (~380 lines)
- `sigil fmt file.sigil` — print formatted source
- `sigil fmt file.sigil --check` — exit 1 if needs formatting
- Handles all AST node types, consistent 2-space indentation

### Linter (Complete — Phase 4 Sprint 2)
- `src/sigil/linter/linter.py` — Semantic linter extending type checker
- Checks: empty rule body, duplicate conditions, confidence_threshold range
- `sigil lint file.sigil` / `sigil lint file.sigil --strict`

### NL-to-Sigil Generator (Complete — Phase 4 Sprint 3)
- `src/sigil/generator/` — LLM-powered code generation
- `SigilGenerator` with pluggable `LLMBackend` protocol
- `AnthropicLLM` default backend (requires `anthropic` SDK)
- Validation pipeline: parse → type-check → report
- Interactive refinement loop (auto-retry with error feedback)
- `sigil parse "description"` / `sigil parse "description" --interactive`
- `docs/SIGIL_CODE_EXAMPLES.md` — usage examples and workflows

### Sigil Code Interactive Agent (Complete — Phase 4 Sprint 5)
- `src/sigil/agent/session.py` — Session manager (CLI entry point, conversation state)
- `src/sigil/agent/loop.py` — ReACT loop via Anthropic `tool_use` API (observe→think→act cycle)
- `src/sigil/agent/tools.py` — 7 tools: `validate`, `execute`, `format_code`, `write_file`, `read_file`, `list_project`, `scaffold`
- `src/sigil/agent/prompts.py` — System prompt assembly with Sigil syntax reference
- `src/sigil/agent/templates.py` — 4 project templates: basic, rules, neural, full
- `sigil code` CLI subcommand — launches interactive agent session
- 58 tests (22 tool, 12 loop, 14 prompt, 6 template, 4 session/CLI)

### Test Suite
- **1000 tests total**, all passing:
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
  - 15 backward chaining unit tests
  - 6 query/temporal evaluator integration tests
  - 7 sigil.time stdlib tests
  - 7 sigil.trace stdlib tests
  - 9 sigil.io stdlib tests
  - 15 enhanced type inference tests
  - 7 Sprint 3 example integration tests
  - 3 backward chaining deep integration tests
  - **Phase 3 (99 new tests):**
  - 15 FFI marshal tests
  - 15 FFI python_interop tests
  - 5 FFI error translation tests
  - 10 FFI end-to-end tests
  - 5 neural backend tests
  - 5 neural config tests
  - 7 neural registry tests
  - 8 neural HuggingFace tests (mocked, inc. zero-shot)
  - 8 neural Anthropic backend tests (mocked)
  - 9 neural OpenAI backend tests (mocked)
  - 4 neural ONNX backend tests (mocked)
  - 6 neural Python callable tests
  - 6 neural MockBackend tests
  - 18 neural integration tests
  - 13 Rust pattern matcher tests
  - 12 Rust constraint solver tests
  - 5 Rust trace serialization tests
  - **Phase 4 (135 new tests):**
  - 10 error message tests
  - 10 error recovery tests
  - 7 stack trace tests
  - 6 warning tests
  - 17 formatter tests
  - 11 linter tests
  - 10 generator tests
  - 6 validator tests
  - 5 prompt assembly tests
  - 4 interactive refinement tests
  - 10 import/packaging tests
  - 29 example parse tests (parametrized across all .sigil files)
  - **Sigil Code Agent (58 new tests):**
  - 22 tool tests (validate, execute, format_code, write_file, read_file, list_project, scaffold)
  - 12 loop tests (mock Anthropic backend, ReACT cycle, tool dispatch)
  - 14 prompt validation tests (system prompt assembly, syntax reference inclusion)
  - 6 template tests (basic, rules, neural, full + toolchain validation)
  - 4 session/CLI tests

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

### Sprint 3: Advanced Rules + Polish — COMPLETE
- [x] Backward chaining engine (goal-driven `query` statement)
- [x] Temporal rule foundations (`within` constraints, parsed + recorded in trace)
- [x] Standard library: sigil.time, sigil.trace, sigil.io
- [x] Enhanced type inference (return type consistency, gradual, unit awareness)
- [x] Performance benchmarks (lexer, parser, evaluator)
- [x] 3 new examples, 83 new tests → 665 total

## Phase 3 Plan (3 Sprints)

### Sprint 1: Python FFI — COMPLETE
- [x] Type marshaling layer (`ffi/marshal.py`)
- [x] Error translation (`ffi/errors.py`)
- [x] Python module importer (`ffi/python_interop.py`)
- [x] Evaluator wired for `import python X` (full, selective, aliased)
- [x] Graceful degradation for missing modules
- [x] 45 new tests + 1 example → 710 total

### Sprint 2: Neural Bridge — COMPLETE
- [x] `ModelBackend` protocol + `ModelResult` dataclass
- [x] `ModelRegistry` with prefix-based backend routing
- [x] HuggingFace backend (mock-tested, real model optional)
- [x] `NeuralTrace` in trace system
- [x] `_call_neural()` replaces `_call_neural_stub()` in evaluator
- [x] 24 new tests + 1 example → 734 total

### Neural Bridge v2 — COMPLETE (3 sprints)
- [x] Sprint A: `NeuralConfig` + `CandidateResult` + `MockBackend` + zero-shot HuggingFace + evaluator `_build_neural_config()`
- [x] Sprint B: `AnthropicBackend` (claude: prefix) + `OpenAIBackend` (openai: prefix) + structured JSON→Record output
- [x] Sprint C: `ONNXBackend` (onnx: prefix) + `PythonCallableBackend` (python: prefix) + timeout enforcement
- [x] 43 new tests (76 neural total) + 2 new examples → 807 total

### Sprint 3: Rust Core — COMPLETE
- [x] `SigilValue` Rust enum with PyO3 + serde traits
- [x] Rete-lite pattern matcher (`ReteNetwork` PyO3 class)
- [x] Constraint solver (`ConstraintSolver` PyO3 class)
- [x] Trace serialization (JSON pretty + compact)
- [x] Benchmarks (pattern matching ~2.4x, trace ~1.3x speedup)
- [x] 30 new tests + 1 example + benchmark → 764 total

## Phase 4 Plan (5 Sprints) — COMPLETE

### Sprint 1: Error Experience — COMPLETE
- [x] Error suggestion infrastructure (`suggestion` field on all errors)
- [x] Parser panic-mode recovery (`SigilParseErrors`, `_synchronize()`)
- [x] Lexer error suggestions (tabs, unterminated strings)
- [x] Evaluator call stack tracking + "did you mean?" (Levenshtein)
- [x] Unused declaration warnings in type checker
- [x] `--warnings-as-errors` flag on `sigil check`
- [x] 33 new tests → 823 total

### Sprint 2: Developer Tooling — COMPLETE
- [x] AST→source formatter (`sigil fmt`)
- [x] Semantic linter (`sigil lint`)
- [x] REPL readline history + tab completion
- [x] 28 new tests → 851 total

### Sprint 3: NL-to-Sigil Generator — COMPLETE
- [x] `SigilGenerator` with pluggable `LLMBackend` protocol
- [x] Prompt engineering (syntax reference + examples + constraints)
- [x] Validation pipeline (parse → type-check)
- [x] Interactive refinement loop (auto-retry)
- [x] CLI: `sigil parse "description"` with `--interactive`
- [x] 25 new tests → 876 total

### Sprint 4: Packaging & CI — COMPLETE
- [x] GitHub Actions CI (`.github/workflows/ci.yml`)
- [x] 4 new example programs (getting_started + patterns)
- [x] `CONTRIBUTING.md`
- [x] Packaging tests (imports + example parse validation)
- [x] 39 new tests → 942 total (29 parametrized example tests)

### Sprint 5: Sigil Code Interactive Agent — COMPLETE
- [x] ReACT loop via Anthropic `tool_use` API (observe→think→act)
- [x] 7 tools: validate, execute, format_code, write_file, read_file, list_project, scaffold
- [x] 4 project templates (basic, rules, neural, full)
- [x] System prompt with Sigil syntax reference and constraints
- [x] CLI: `sigil code` launches interactive agent session
- [x] 58 new tests → 1000 total

### Phase 5+: See `docs/ROADMAP.md`

---

## Known Issues / Open Questions

1. ~~Rust not installed~~: **Resolved** — Rust 1.94.0 installed, maturin build working with PyO3 0.25
2. ~~Grammar doc needs updating~~: **Resolved** — GRAMMAR.peg v0.2 reflects all 8 parser gaps
3. ~~Pipeline parsing~~: **Resolved** — Full pipeline operator implemented in Phase 2 Sprint 1
4. ~~CI pipeline~~: **Resolved** — `.github/workflows/ci.yml` with Python 3.11-3.13 matrix
5. ~~mypy~~: **Resolved** — 0 errors across 25 source files
6. ~~Neural stubs~~: **Resolved** — Phase 3 replaced stubs with pluggable ModelBackend + ModelRegistry
7. **Rust core marshaling overhead**: At small scale (5 constraints), Python-to-Rust marshaling dominates computation. Speedup visible at 50+ rules. Full Rete with persistent Rust-side data (Phase 5) will eliminate this.
8. **HuggingFace models in CI**: transformers not installed by default; neural tests use mocks. Real model tests should be `@pytest.mark.slow`.

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
| 2026-03-11 | Neural backend: pluggable protocol | `ModelBackend` protocol + prefix-based `ModelRegistry`; extensible for custom backends | Hardcoded HuggingFace, direct API calls |
| 2026-03-11 | Python FFI: graceful import failure | Missing modules bind empty record; errors at use time, not import time. Preserves backward compat with examples using `import python transformers` | Hard fail on missing module |
| 2026-03-11 | Rust core: Rete-lite first | Simplified alpha-node matching; full Rete with beta-node joins deferred to Phase 5 | Full Rete from start, no Rust core |
| 2026-03-11 | Rust deps: serde + serde_json | Standard Rust serialization; needed for trace JSON export | bincode (binary), custom format |
| 2026-03-11 | Neural v2: NeuralConfig dataclass | All neural field params in one frozen dataclass; parser already accepts arbitrary IDENTIFIER fields | Per-field extraction in evaluator |
| 2026-03-11 | Neural v2: 6 backends | hf:, claude:, openai:, onnx:, python:, mock: — all optional except mock/python | Single backend, manual selection |
| 2026-03-11 | Neural v2: timeout via threading | Thread-based timeout around backend.predict(); TimeoutError triggers fallback | asyncio (would infect evaluator), signal (not cross-platform) |
| 2026-03-12 | Generator prompts: `**` → `pow()` | `**` operator not in Sigil grammar; prompt examples in `generator/prompts.py` line 114 replaced with `pow()` stdlib call | Keep `**` (would require lexer/parser changes) |
| 2026-03-12 | Sigil Code agent: ReACT loop | Tool-use based agent loop using Anthropic API; 7 tools for validate/execute/format/scaffold workflow | Direct code generation (no iteration), CLI wizard (no AI) |

---

## How to Update This File

After completing a task or making a decision:
1. Move items from "Being Built" to "What Exists"
2. Add new issues/questions to "Known Issues"
3. Log decisions in "Decision Log"
4. Update the "Last updated" date at top
5. Bump "Current phase" and "Current sprint" as needed
