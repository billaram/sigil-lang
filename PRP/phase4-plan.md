# Phase 4: Production Readiness — Implementation Plan

**Status**: DRAFT
**Created**: 2026-03-11
**Sprints**: 4 (matching ROADMAP milestones 4.1–4.4)

## Context

Phase 3 is complete (807 tests, 6 neural backends, Rust core, Python FFI). Sigil has a working neuro-symbolic engine with real model inference, but it's developer-hostile: errors crash on first problem with bare messages, no formatter or linter exists, the REPL has no history, and there's no way for non-programmers to generate Sigil code. Phase 4 makes Sigil usable by real humans.

## Current State (What Already Exists)

| Component | Status | Notes |
|-----------|--------|-------|
| CLI | 7 commands, 2 stubs (`fmt`, `parse`) | `lint` not defined |
| Error hierarchy | `SigilError` → 4 subclasses | Location only, no suggestions or recovery |
| REPL | 7 commands, multi-line detection | No history, no autocomplete |
| Parser recovery | None | Crashes on first error |
| Type checker | 550 lines, 11 diagnostic types | Has `suggestion` field, not widely used |
| Formatter | Stub only (`sigil fmt` prints placeholder) | No AST→source printer |
| Linter | Does not exist | Type checker covers some ground |
| Tree-sitter | `GRAMMAR.peg` exists | No tree-sitter bindings |
| CI/CD | Not created | Local-only: ruff, mypy, pytest |
| Test suite | 807 tests, 46 files | All passing |

## Design Decisions

- **Error recovery**: Panic-mode synchronization (skip to next declaration on error), not full recovery — pragmatic and avoids rewriting the parser
- **Formatter**: AST round-trip (`parse → format`) — ensures formatting always produces valid code
- **Linter**: Extension of type checker (Phase 2 scan), not a separate tool — reuses the symbol table
- **REPL**: Use `readline` stdlib module for history + tab completion — no external dependencies
- **NL-to-Sigil**: Claude API via existing `anthropic_backend.py` infrastructure — Sigil already has Claude integration
- **Tree-sitter**: Generate from GRAMMAR.peg manually — no automated PEG→tree-sitter converter exists
- **Packaging**: Standard `build` + `twine` workflow — maturin handles the Rust wheel

---

## Sprint 1: Error Experience (~30 tests)

**Goal**: Parser reports multiple errors, all errors include suggestions, stack traces map to source.

### What to Build

#### 1. Error Suggestion Infrastructure
**File**: `src/sigil/errors.py` — enhance base classes

Add `suggestion: str | None` field to all error subclasses:
```python
@dataclass(frozen=True)
class SigilError(Exception):
    message: str
    location: SourceLocation | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        loc = f"{self.location}: " if self.location else ""
        hint = f"\n  hint: {self.suggestion}" if self.suggestion else ""
        return f"{loc}{self.message}{hint}"
```

Update `SigilLexError`, `SigilParseError`, `SigilTypeError`, `SigilRuntimeError` to pass through `suggestion`.

#### 2. Parser Error Recovery (Panic Mode)
**File**: `src/sigil/parser/parser.py` — add recovery

Add panic-mode synchronization:
- New `_synchronize()` method: skip tokens until a declaration keyword (`rule`, `compute`, `neural`, `type`, `define`, `import`, `export`, `main`) or EOF
- New `_errors: list[SigilParseError]` accumulator on Parser class
- `_parse_program()` wraps each top-level declaration parse in try/except → catch `SigilParseError`, record it, call `_synchronize()`, continue
- After parsing, if `_errors` is non-empty, raise a new `SigilParseErrors` (plural) that wraps all collected errors
- Only top-level recovery — within a declaration, first error still aborts that declaration

New class:
```python
class SigilParseErrors(SigilError):
    """Multiple parse errors collected via error recovery."""
    errors: tuple[SigilParseError, ...]
```

#### 3. Rich Error Messages with Suggestions
**File**: `src/sigil/parser/parser.py` — improve `_error()` and `_expect()`

Add contextual suggestions:
- `Expected COLON, got NEWLINE` → `hint: add ':' after the declaration header`
- `Expected IDENTIFIER, got KEYWORD 'list'` → `hint: 'list' is a reserved keyword; use a different name`
- `Expected INDENT, got ...` → `hint: add 2 spaces of indentation for the block body`
- `Unexpected token at top level` → `hint: declarations must start with 'rule', 'compute', 'neural', 'type', 'define', 'import', 'export', or 'main'`

**File**: `src/sigil/lexer/lexer.py` — improve lexer errors
- Tab character → `hint: use spaces (2 per level) instead of tabs`
- Unterminated string → `hint: add closing '"' to the string literal`
- Invalid number → `hint: numbers must be digits, optionally with a decimal point`

**File**: `src/sigil/interpreter/evaluator.py` — improve runtime errors
- Undefined variable → `hint: did you mean '<closest_match>'?` (Levenshtein distance)
- Type mismatch in comparison → `hint: '<var>' is a <type>, but compared as <other_type>`
- Neural model not found → `hint: install the backend with 'pip install sigil-lang[<backend>]'`

#### 4. Source-Mapped Stack Traces
**File**: `src/sigil/interpreter/evaluator.py` — add call stack tracking

- New `_call_stack: list[SourceLocation]` on Evaluator
- Push location on function/rule entry, pop on exit
- On `SigilRuntimeError`, attach `call_stack` to error
- Format as Sigil-style traceback:

```
Traceback (most recent call last):
  rule temperature_check (examples/basic.sigil:5)
    compute calculate_risk (examples/basic.sigil:12)
      given risk as predict(data)
SigilRuntimeError: Neural model 'hf:nonexistent' not found
  hint: check the model ID or register a custom backend
```

**File**: `src/sigil/errors.py` — add `format_traceback(error, call_stack)` function

#### 5. Warning System
**File**: `src/sigil/types/checker.py` — extend Phase 2 scan

Add new diagnostic types (all WARNING severity):
- **Unused rule**: rule declared but never referenced in `query` or chaining
- **Unused compute**: compute function declared but never called
- **Unused define**: constant defined but never referenced
- **Unreachable condition**: `when true and false` (constant folding check)
- **Shadowed variable**: `given x as ...` where `x` already bound in same scope

**File**: `src/sigil/cli.py` — update `check` command
- Print warnings after errors
- Add `--warnings-as-errors` flag for CI use

### Files (Sprint 1)

```
MOD:  src/sigil/errors.py                   — suggestion field, SigilParseErrors, format_traceback
MOD:  src/sigil/parser/parser.py            — _synchronize(), _errors accumulator, rich messages
MOD:  src/sigil/lexer/lexer.py              — suggestion hints on lex errors
MOD:  src/sigil/interpreter/evaluator.py    — call stack tracking, did-you-mean, runtime hints
MOD:  src/sigil/types/checker.py            — unused/unreachable/shadow warnings
MOD:  src/sigil/cli.py                      — --warnings-as-errors flag
NEW:  tests/errors/test_error_messages.py   — 8 tests (suggestions, formatting)
NEW:  tests/parser/test_error_recovery.py   — 10 tests (multi-error, synchronization)
NEW:  tests/errors/test_stack_traces.py     — 5 tests (traceback formatting)
MOD:  tests/typechecker/test_warnings.py    — 7 tests (unused, unreachable, shadow)
```

### Sprint 1 Exit Criteria

```bash
# Parser reports multiple errors:
echo 'rule bad1:\n  when x\nrule bad2:\n  when y' | sigil check -
# → error 1: Expected condition operator...
# → error 2: Expected condition operator...
# → 2 errors found

# Suggestions appear:
echo 'rule test\n  when x > 1' | sigil check -
# → Expected COLON, got NEWLINE
# →   hint: add ':' after the declaration header

# Stack traces work:
sigil run broken_example.sigil
# → Traceback with Sigil source locations

pytest tests/errors/ tests/parser/test_error_recovery.py -v  # 23+ new tests
pytest tests/ -v --tb=short                                    # All 830+ pass
```

---

## Sprint 2: Developer Tooling (~35 tests)

**Goal**: `sigil fmt` formats code, `sigil lint` catches issues, REPL gets history and autocomplete.

### What to Build

#### 1. AST Pretty-Printer / Formatter
**File**: `src/sigil/formatter/formatter.py` (NEW)

AST→source round-trip formatter:
- `format_program(program: ast.Program) -> str`
- Consistent 2-space indentation
- One blank line between top-level declarations
- Aligned field values in neural declarations
- Sorted imports (stdlib → python → rust → relative)
- Line wrapping at 100 characters for long conditions
- Preserves comments (requires comment attachment in AST — see below)

**File**: `src/sigil/ast/nodes.py` — add comment attachment
- Add `leading_comments: tuple[str, ...] = ()` to `Program` and top-level declaration nodes
- Parser stores comments encountered before each declaration

**File**: `src/sigil/formatter/__init__.py` (NEW)

Key formatting rules:
```
rule name with priority N:        ← space before colon
  when condition                  ← 2-space indent
  and other_condition             ← aligned with 'when'
  then action                     ← aligned with 'when'
  explain "reason"                ← aligned with 'when'

compute func from x: Number returns Number:
  return x + 1                    ← 2-space indent

neural classify from text: Text:
  model       "hf:model-name"    ← aligned field values
  returns     Symbol
  confidence_threshold 0.7
  fallback to :unknown
```

#### 2. Linter
**File**: `src/sigil/linter/linter.py` (NEW)

Extends type checker diagnostics with semantic checks:
- `lint_program(program: ast.Program) -> list[Diagnostic]`
- Runs type checker first, then adds:
  - **Unused imports**: imported name never referenced
  - **Duplicate conditions**: same condition repeated in a rule's when-block
  - **Missing fallback**: neural declaration without explicit fallback (already enforced by parser, but lint catches edge cases)
  - **Confidence threshold out of range**: value < 0 or > 1
  - **Empty rule body**: rule with conditions but no actions
  - **Rule never fires**: rule conditions reference variables never defined
  - **Overly broad catch**: `on error: fallback` without logging/tracing

**File**: `src/sigil/linter/__init__.py` (NEW)

**File**: `src/sigil/cli.py` — add `lint` command
```python
@app.command()
def lint(file: Path, strict: bool = False):
    """Lint a Sigil program for issues."""
    # Parse → type check → lint → report
```

#### 3. REPL Improvements
**File**: `src/sigil/interpreter/repl.py` — enhance with readline

- **History**: Use `readline` module for input history (up/down arrow)
  - Persist history to `~/.sigil_history` (like Python's `~/.python_history`)
  - `readline.read_history_file()` on startup, `readline.write_history_file()` on exit
- **Tab completion**: `readline.set_completer()` with custom completer
  - Complete keywords: `rule`, `compute`, `neural`, `when`, `then`, etc.
  - Complete bound variables from current environment
  - Complete REPL commands (`:env`, `:rules`, etc.)
  - Complete stdlib module names (`sigil.math`, `sigil.text`, etc.)
- **Improved prompts**: `sigil> ` for first line, `  ...> ` for continuation
- **Color output** (optional, detect terminal):
  - Errors in red, warnings in yellow, results in green
  - Use ANSI codes with terminal detection (`sys.stdout.isatty()`)

#### 4. Tree-sitter Grammar
**File**: `tree-sitter-sigil/grammar.js` (NEW)

Tree-sitter grammar for editor syntax highlighting:
- Translate `GRAMMAR.peg` rules to tree-sitter `grammar.js` format
- Cover: keywords, operators, strings, numbers, symbols, comments, indentation
- Provide `queries/highlights.scm` for syntax highlighting queries
- Provide `queries/locals.scm` for scope tracking

```
tree-sitter-sigil/
├── grammar.js           ← tree-sitter grammar definition
├── queries/
│   ├── highlights.scm   ← syntax highlighting rules
│   └── locals.scm       ← scope/variable tracking
├── package.json         ← npm package for tree-sitter
└── test/
    └── corpus/          ← tree-sitter test cases
        ├── rules.txt
        ├── compute.txt
        ├── neural.txt
        └── expressions.txt
```

### Files (Sprint 2)

```
NEW:  src/sigil/formatter/__init__.py
NEW:  src/sigil/formatter/formatter.py       — AST→source formatter
NEW:  src/sigil/linter/__init__.py
NEW:  src/sigil/linter/linter.py             — semantic linter
MOD:  src/sigil/ast/nodes.py                 — comment attachment fields
MOD:  src/sigil/interpreter/repl.py          — readline history, tab completion, colors
MOD:  src/sigil/cli.py                       — sigil lint command, sigil fmt wired up
NEW:  tree-sitter-sigil/grammar.js
NEW:  tree-sitter-sigil/queries/highlights.scm
NEW:  tree-sitter-sigil/queries/locals.scm
NEW:  tree-sitter-sigil/package.json
NEW:  tree-sitter-sigil/test/corpus/rules.txt
NEW:  tests/formatter/test_formatter.py      — 12 tests (round-trip, indentation, alignment)
NEW:  tests/linter/test_linter.py            — 10 tests (unused, duplicate, range, empty)
MOD:  tests/interpreter/test_repl.py         — +5 tests (history, completion)
NEW:  tests/formatter/test_comment_preservation.py — 3 tests
```

### Sprint 2 Exit Criteria

```bash
# Formatter:
sigil fmt examples/basic/temperature.sigil   # prints formatted source
sigil fmt examples/ --check                  # exits 1 if any file needs formatting

# Linter:
sigil lint examples/basic/temperature.sigil  # reports issues
sigil lint examples/ --strict                # warnings are errors

# REPL:
sigil repl
sigil> rule test:↑↓                          # history navigation works
sigil> sig<TAB>                               # completes to 'sigil.math'

# Tree-sitter:
cd tree-sitter-sigil && npx tree-sitter generate && npx tree-sitter test

pytest tests/formatter/ tests/linter/ -v     # 25+ new tests
pytest tests/ -v --tb=short                  # All 865+ pass
```

---

## Sprint 3: NL-to-Sigil Generator (~20 tests)

**Goal**: `sigil parse "describe a rule..."` generates valid Sigil code from natural language.

### What to Build

#### 1. Sigil Code Generator
**File**: `src/sigil/generator/generator.py` (NEW)

LLM-powered NL→Sigil translation:
```python
class SigilGenerator:
    def __init__(self, backend: str = "claude:claude-sonnet-4-20250514"):
        ...

    def generate(self, description: str, context: str | None = None) -> GenerationResult:
        """Generate Sigil code from natural language description."""
        ...

    def refine(self, code: str, feedback: str) -> GenerationResult:
        """Refine previously generated code based on feedback."""
        ...
```

```python
@dataclass(frozen=True)
class GenerationResult:
    code: str                    # Generated Sigil source
    valid: bool                  # Parsed + type-checked successfully
    diagnostics: tuple[str, ...]  # Any warnings from validation
    explanation: str             # LLM's explanation of what it generated
```

#### 2. Prompt Engineering
**File**: `src/sigil/generator/prompts.py` (NEW)

System prompt with:
- Full Sigil syntax reference (condensed from SYNTAX.md)
- Type system rules
- Common patterns (rule, compute, neural, type, define)
- Examples of good Sigil code (5-10 curated examples)
- Constraints: no Python syntax, use Sigil keywords, explicit types at boundaries

Template:
```
You are a Sigil programming language expert. Generate valid Sigil code from the user's description.

<sigil-syntax-reference>
{condensed syntax guide}
</sigil-syntax-reference>

<examples>
{curated example programs}
</examples>

Rules:
1. Output ONLY Sigil code (no markdown fences, no explanation)
2. Use proper indentation (2 spaces)
3. Include type annotations on function parameters
4. Every neural declaration must have model, returns, confidence_threshold, fallback
5. Use symbols (:name) for enum-like values
```

#### 3. Validation Pipeline
**File**: `src/sigil/generator/validator.py` (NEW)

Three-stage validation of generated code:
1. **Parse**: tokenize + parse → check for syntax errors
2. **Type check**: run type checker → collect diagnostics
3. **Dry run** (optional): evaluate with mock neural backend → verify no runtime errors

```python
def validate_generated(code: str) -> ValidationResult:
    """Parse → type-check → optional dry-run."""
    ...

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    parse_errors: tuple[str, ...]
    type_errors: tuple[str, ...]
    warnings: tuple[str, ...]
```

#### 4. Interactive Refinement Loop
**File**: `src/sigil/generator/interactive.py` (NEW)

Multi-turn generation with feedback:
```python
def interactive_generate(initial_description: str) -> str:
    """Multi-turn generation: generate → validate → refine → validate → done."""
    result = generator.generate(initial_description)
    if result.valid:
        return result.code

    # Auto-refine: feed validation errors back to LLM
    for attempt in range(MAX_REFINEMENT_ATTEMPTS):
        feedback = format_validation_errors(result.diagnostics)
        result = generator.refine(result.code, feedback)
        if result.valid:
            return result.code

    return result.code  # Best effort
```

#### 5. Wire CLI Command
**File**: `src/sigil/cli.py` — replace `parse` stub

```python
@app.command()
def parse(text: str, model: str = "claude:claude-sonnet-4-20250514", interactive: bool = False):
    """Generate Sigil code from natural language description."""
    ...
```

#### 6. Generator Module Init
**File**: `src/sigil/generator/__init__.py` (NEW)

### Files (Sprint 3)

```
NEW:  src/sigil/generator/__init__.py
NEW:  src/sigil/generator/generator.py       — SigilGenerator, GenerationResult
NEW:  src/sigil/generator/prompts.py         — system prompt, examples, templates
NEW:  src/sigil/generator/validator.py       — parse→typecheck→dry-run pipeline
NEW:  src/sigil/generator/interactive.py     — multi-turn refinement loop
MOD:  src/sigil/cli.py                       — wire sigil parse command
NEW:  tests/generator/test_generator.py      — 6 tests (mocked LLM, generate, refine)
NEW:  tests/generator/test_validator.py      — 5 tests (parse, typecheck, dry-run)
NEW:  tests/generator/test_prompts.py        — 3 tests (prompt assembly, example inclusion)
NEW:  tests/generator/test_interactive.py    — 4 tests (refinement loop, max attempts)
MOD:  tests/generator/conftest.py            — mock LLM fixtures
```

### Sprint 3 Exit Criteria

```bash
# Basic generation:
sigil parse "a rule that flags high-risk transactions over $10000"
# → prints valid Sigil code

# With validation feedback:
sigil parse "classify customer sentiment" --interactive
# → generates, validates, refines if needed

# Mocked tests (no API key needed):
pytest tests/generator/ -v                   # 18+ new tests
pytest tests/ -v --tb=short                  # All 885+ pass

# Real test (requires ANTHROPIC_API_KEY):
ANTHROPIC_API_KEY=... sigil parse "a neural classifier for email spam"
```

---

## Sprint 4: Packaging & Documentation (~15 tests)

**Goal**: `pip install sigil-lang` works, documentation covers all features, CI runs on every push.

### What to Build

#### 1. PyPI Packaging
**File**: `pyproject.toml` — verify/update build configuration

Ensure correct metadata:
```toml
[project]
name = "sigil-lang"
version = "0.4.0"
description = "A neuro-symbolic programming language"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
keywords = ["neuro-symbolic", "programming-language", "rules-engine", "ai"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Rust",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
```

**File**: `Makefile` or `scripts/release.sh` (NEW) — release automation
```bash
# Build wheel (Python + Rust):
maturin build --release

# Upload to PyPI:
twine upload dist/*

# Or test PyPI first:
twine upload --repository testpypi dist/*
```

Verify:
- `pip install sigil-lang` installs cleanly (Python-only, no Rust required)
- `pip install sigil-lang[hf]` installs with HuggingFace
- `pip install sigil-lang[all]` installs everything
- `sigil run`, `sigil repl`, `sigil check`, `sigil fmt`, `sigil lint` all work post-install

#### 2. GitHub Actions CI
**File**: `.github/workflows/ci.yml` (NEW)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: dtolnay/rust-toolchain@stable
      - run: pip install -e ".[dev]"
      - run: maturin develop
      - run: ruff check src/ tests/
      - run: mypy src/sigil/
      - run: pytest tests/ -v --tb=short
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install ruff
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/
```

#### 3. User Guide
**File**: `docs/guide/` (NEW directory)

```
docs/guide/
├── 01-getting-started.md    — Installation, first program, running
├── 02-rules.md              — Rule syntax, conditions, actions, priority, chaining
├── 03-compute.md            — Functions, types, pattern matching, pipelines
├── 04-neural.md             — Neural declarations, backends, fallbacks, tracing
├── 05-modules.md            — Imports, exports, stdlib, Python FFI
├── 06-tooling.md            — CLI commands, REPL, formatter, linter
└── 07-examples.md           — Walkthrough of 5 complete example programs
```

Each guide chapter: ~500 words + code examples + expected output.

#### 4. API Reference
**File**: `docs/api/` (NEW directory) — auto-generated from docstrings

```
docs/api/
├── lexer.md       — tokenize(), TokenType, Token
├── parser.md      — parse(), AST node reference
├── evaluator.md   — evaluate(), Evaluator class
├── types.md       — type_check(), Diagnostic
├── neural.md      — ModelBackend, ModelRegistry, NeuralConfig
├── ffi.md         — marshal, python_interop
├── stdlib.md      — all stdlib functions by module
└── cli.md         — CLI command reference
```

**File**: `scripts/generate_api_docs.py` (NEW) — extract docstrings → markdown

#### 5. Tutorial Series
**File**: `docs/tutorials/` (NEW directory)

```
docs/tutorials/
├── tutorial-01-hello-sigil.md        — First rule, running, traces
├── tutorial-02-loan-eligibility.md   — Multi-rule system with priority
├── tutorial-03-neural-classifier.md  — Neural + symbolic pipeline
├── tutorial-04-python-integration.md — Calling Python from Sigil
├── tutorial-05-full-application.md   — End-to-end content moderation system
```

#### 6. Contributing Guide
**File**: `CONTRIBUTING.md` (NEW)

- Development setup (clone, venv, pip install, maturin develop)
- Project structure overview
- How to add new syntax (link to /add-syntax skill)
- How to add new stdlib functions
- How to add new neural backends
- Testing requirements (all tests must pass, lint clean)
- PR process

#### 7. README Update
**File**: `README.md` — comprehensive rewrite

- What is Sigil (1 paragraph)
- Quick example (rule + neural)
- Installation (`pip install sigil-lang`)
- Quick start (3 commands)
- Feature highlights (6 bullets)
- Links to docs, tutorials, examples
- Badge: CI status, PyPI version, Python versions

#### 8. Example Programs
**File**: `examples/` — ensure 20+ working examples

Audit existing examples and add missing ones:
- `examples/getting_started/hello.sigil` — minimal first program
- `examples/getting_started/calculator.sigil` — compute functions
- `examples/patterns/priority_rules.sigil` — conflict resolution
- `examples/patterns/backward_chaining.sigil` — query-driven evaluation
- Ensure all existing examples still run (`sigil run` each one)

### Files (Sprint 4)

```
MOD:  pyproject.toml                          — metadata, classifiers, version
NEW:  .github/workflows/ci.yml               — GitHub Actions CI
NEW:  scripts/release.sh                      — release automation
NEW:  scripts/generate_api_docs.py            — docstring → markdown
NEW:  docs/guide/01-getting-started.md
NEW:  docs/guide/02-rules.md
NEW:  docs/guide/03-compute.md
NEW:  docs/guide/04-neural.md
NEW:  docs/guide/05-modules.md
NEW:  docs/guide/06-tooling.md
NEW:  docs/guide/07-examples.md
NEW:  docs/api/                               — 8 auto-generated API reference files
NEW:  docs/tutorials/tutorial-01-hello-sigil.md
NEW:  docs/tutorials/tutorial-02-loan-eligibility.md
NEW:  docs/tutorials/tutorial-03-neural-classifier.md
NEW:  docs/tutorials/tutorial-04-python-integration.md
NEW:  docs/tutorials/tutorial-05-full-application.md
NEW:  CONTRIBUTING.md
MOD:  README.md                               — comprehensive rewrite
NEW:  examples/getting_started/hello.sigil
NEW:  examples/getting_started/calculator.sigil
NEW:  examples/patterns/priority_rules.sigil
NEW:  examples/patterns/backward_chaining.sigil
NEW:  tests/packaging/test_install.py         — 5 tests (import sigil, CLI entry points)
NEW:  tests/packaging/test_examples.py        — 10 tests (all examples run without error)
```

### Sprint 4 Exit Criteria

```bash
# Package builds:
maturin build --release
pip install dist/sigil_lang-*.whl
sigil --help                                  # CLI works from installed package

# CI passes:
gh workflow run ci.yml                        # Green on all Python versions

# Docs complete:
ls docs/guide/ | wc -l                        # 7 chapters
ls docs/tutorials/ | wc -l                    # 5 tutorials
ls docs/api/ | wc -l                          # 8 API reference files

# Examples work:
sigil run examples/getting_started/hello.sigil  # runs
python scripts/validate_all_examples.py         # all 20+ pass

pytest tests/packaging/ -v                    # 15 new tests
pytest tests/ -v --tb=short                   # All 900+ pass
```

---

## Implementation Order

```
Sprint 1: Error Experience
  1. errors.py (suggestion infrastructure)
  2. parser.py (_synchronize, _errors, panic-mode recovery)
  3. lexer.py (lexer error suggestions)
  4. evaluator.py (call stack, did-you-mean, runtime hints)
  5. checker.py (unused/unreachable/shadow warnings)
  6. cli.py (--warnings-as-errors)
  7. tests
  CHECKPOINT: pytest passes, parser reports multiple errors

Sprint 2: Developer Tooling
  8. nodes.py (comment attachment)
  9. formatter.py (AST→source)
  10. linter.py (semantic checks)
  11. repl.py (readline, history, tab completion)
  12. cli.py (sigil fmt, sigil lint)
  13. tree-sitter-sigil/ (grammar + queries)
  14. tests
  CHECKPOINT: fmt + lint + repl all work

Sprint 3: NL-to-Sigil Generator
  15. prompts.py (system prompt, examples)
  16. validator.py (parse→typecheck→dry-run)
  17. generator.py (SigilGenerator)
  18. interactive.py (refinement loop)
  19. cli.py (wire sigil parse)
  20. tests (mocked LLM)
  CHECKPOINT: sigil parse "..." generates valid code

Sprint 4: Packaging & Documentation
  21. pyproject.toml (metadata, version)
  22. .github/workflows/ci.yml
  23. docs/guide/ (7 chapters)
  24. docs/tutorials/ (5 tutorials)
  25. docs/api/ (generated)
  26. README.md + CONTRIBUTING.md
  27. examples/ (audit + add missing)
  28. tests/packaging/
  CHECKPOINT: pip install sigil-lang works, CI green
```

## Verification

```bash
# After each sprint:
pytest tests/ -v --tb=short          # ALL tests pass
ruff check src/ tests/               # Lint clean
mypy src/sigil/                      # Types clean

# Final Phase 4 verification:
pytest tests/ -v --tb=short          # 900+ tests
sigil fmt examples/ --check          # All examples formatted
sigil lint examples/                 # No lint errors
sigil parse "a rule for temperature" # Generates valid Sigil
pip install dist/sigil_lang-*.whl    # Installs cleanly
gh workflow view ci                  # CI green

# Test count target: 807 + 100 = 907+ tests
```

## Risk Register

| Risk | Mitigation |
|------|------------|
| Parser recovery breaks existing programs | Recovery only at top-level boundaries; within-declaration parsing unchanged |
| Formatter doesn't round-trip perfectly | Property-based tests: `parse(format(parse(source))) == parse(source)` |
| readline not available on all platforms | Fallback to raw `input()` if readline import fails |
| NL-to-Sigil quality depends on LLM | Validation pipeline catches bad output; mock backend for tests |
| Tree-sitter grammar drifts from parser | Test corpus uses same examples as parser tests |
| PyPI naming conflict | `sigil-lang` already reserved by us (check early) |
| CI runner doesn't have Rust toolchain | Use `dtolnay/rust-toolchain` action; test Python-only path too |
| Documentation gets stale | API docs auto-generated from code; guide tested against examples |

## Dependencies Between Sprints

```
Sprint 1 (errors) ← independent, do first
Sprint 2 (tooling) ← depends on Sprint 1 (linter uses warning system)
Sprint 3 (generator) ← depends on Sprint 2 (validator uses linter)
Sprint 4 (packaging) ← depends on all above (documents everything)
```

Sprint 1 must be done first. Sprints 2 and 3 have a light dependency (linter feeds into validator). Sprint 4 is last because it documents everything built in 1-3.
