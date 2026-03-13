# Contributing to Sigil

Thank you for your interest in contributing to Sigil! This document covers the development setup, project structure, and contribution process.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/billaram/sigil-lang.git
cd sigil-lang

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Build Rust core (requires Rust toolchain)
maturin develop
```

## Running Tests

```bash
pytest tests/ -v                   # All tests
pytest tests/<subsystem>/ -v       # Subsystem tests only
ruff check src/ tests/             # Lint
ruff format src/ tests/            # Auto-format
```

## Project Structure

- `src/sigil/lexer/` -- Tokenization
- `src/sigil/parser/` -- Recursive descent parser
- `src/sigil/ast/` -- AST node definitions (frozen dataclasses)
- `src/sigil/interpreter/` -- Tree-walking evaluator
- `src/sigil/types/` -- Type checker
- `src/sigil/stdlib/` -- Standard library modules
- `src/sigil/ffi/` -- Python/Rust interop
- `src/sigil/neural/` -- Neural bridge (model backends)
- `src/sigil/formatter/` -- AST-to-source formatter
- `src/sigil/linter/` -- Semantic linter
- `src/sigil/generator/` -- NL-to-Sigil code generator
- `src/sigil_core/` -- Rust core (PyO3)
- `tests/` -- pytest test suite
- `examples/` -- Example .sigil programs

## Adding New Syntax

See the `/add-syntax` workflow in `.claude/skills/` for the 10-step process.

## Adding Stdlib Functions

1. Add the function to `src/sigil/stdlib/_builtins.py`
2. Register it in `get_stdlib_module()` in `__init__.py`
3. Add tests in `tests/stdlib/`

## Adding Neural Backends

1. Create `src/sigil/neural/<backend>_backend.py` implementing `ModelBackend`
2. Register the prefix in `ModelRegistry._try_register_defaults()`
3. Add optional dependency to `pyproject.toml`
4. Add tests with mocked API clients

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests alongside implementation
3. Ensure all tests pass: `pytest tests/ -v`
4. Ensure lint is clean: `ruff check src/ tests/`
5. Open a PR with a clear description
