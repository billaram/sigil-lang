# Code Conventions & Patterns

Rules for writing code in the Sigil project. Follow these strictly.

---

## Python Conventions

### General
- **Python 3.11+** — use modern syntax (match/case, `type` aliases, `|` unions)
- **Type hints everywhere** — all function signatures, all class attributes
- **Linting**: `ruff check src/ tests/` must pass
- **Formatting**: `ruff format src/ tests/`
- **Type checking**: `mypy src/sigil/` should pass (strict mode)
- **Line length**: 100 chars max

### Naming
```python
# Modules: snake_case
sigil/lexer/tokens.py

# Classes: PascalCase
class TokenType(Enum): ...
class RuleDecl: ...

# Functions: snake_case
def tokenize(source: str) -> list[Token]: ...
def parse_rule(tokens: TokenStream) -> RuleDecl: ...

# Constants: UPPER_SNAKE_CASE
MAX_INDENT_LEVEL = 100
KEYWORDS = frozenset({"rule", "when", "then", ...})

# Private: leading underscore
def _advance(self) -> Token: ...
```

### Data Structures

**AST nodes**: Use `@dataclass(frozen=True)` — immutable by default.
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Literal:
    value: int | float | str | bool
    location: SourceLocation

@dataclass(frozen=True)
class RuleDecl:
    name: str
    conditions: tuple[Condition, ...]  # tuple, not list (immutable)
    action: Action
    priority: int = 0
    explanation: str | None = None
    location: SourceLocation = ...
```

**Why frozen dataclasses?**
- AST nodes should never be mutated after creation
- Enables hashing (useful for caching, deduplication)
- Makes bugs from accidental mutation impossible
- Aligns with Sigil's own immutability-by-default philosophy

**Use tuples, not lists, for immutable sequences in AST nodes.**

**Tokens**: Use `@dataclass(frozen=True)` with a `TokenType` enum.
```python
class TokenType(Enum):
    # Keywords
    RULE = "rule"
    WHEN = "when"
    THEN = "then"
    ...
    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    ...
    # Structure
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    NEWLINE = "NEWLINE"
    EOF = "EOF"

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int
```

### Error Handling

**Custom exception hierarchy:**
```python
class SigilError(Exception):
    """Base for all Sigil errors."""
    def __init__(self, message: str, location: SourceLocation | None = None):
        self.location = location
        super().__init__(message)

class SigilLexError(SigilError): ...
class SigilParseError(SigilError): ...
class SigilTypeError(SigilError): ...
class SigilRuntimeError(SigilError): ...
```

**Error messages must include:**
1. Source location (file, line, column)
2. The problematic source text
3. What went wrong (plain English)
4. Suggestion for fixing it (when possible)

### Module Organization

Each subpackage exposes its public API through `__init__.py`:
```python
# src/sigil/lexer/__init__.py
from sigil.lexer.lexer import tokenize
from sigil.lexer.tokens import Token, TokenType

__all__ = ["tokenize", "Token", "TokenType"]
```

Functions and classes are defined in dedicated files, not in `__init__.py`.

---

## Testing Conventions

### File Structure
```
tests/
├── conftest.py              # Shared fixtures
├── lexer/
│   ├── test_tokens.py       # Token type tests
│   ├── test_lexer.py        # Lexer unit tests
│   └── test_lexer_integration.py  # Lex full .sigil files
├── parser/
│   ├── test_parser.py       # Parser unit tests
│   └── test_parser_integration.py # Parse full .sigil files
├── interpreter/
│   └── ...
└── integration/
    └── test_end_to_end.py   # Source → decision + trace
```

### Test Naming
```python
# test_<what>_<scenario>
def test_lexer_tokenizes_integer_literal():
def test_lexer_handles_indentation_increase():
def test_lexer_rejects_unterminated_string():
def test_parser_parses_simple_rule():
def test_parser_handles_nested_conditions():
```

### Test Patterns
```python
# Unit test: one input, one expected output
def test_lexer_tokenizes_number():
    tokens = tokenize("42")
    assert tokens == [Token(TokenType.NUMBER, "42", 1, 1), Token(TokenType.EOF, "", 1, 3)]

# Integration test: full example file
def test_lex_temperature_example():
    source = Path("examples/basics/temperature.sigil").read_text()
    tokens = tokenize(source)
    assert all(t.type != TokenType.ERROR for t in tokens)

# Property test: invariant holds for random inputs
@given(sigil_numbers())
def test_lexer_roundtrips_numbers(num_str):
    tokens = tokenize(num_str)
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == num_str

# Error test: bad input produces good error
def test_lexer_error_on_unterminated_string():
    with pytest.raises(SigilLexError, match="Unterminated string"):
        tokenize('"hello')
```

### Fixtures
```python
# conftest.py
import pytest
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

@pytest.fixture
def hello_source():
    return (EXAMPLES_DIR / "basics" / "hello.sigil").read_text()

@pytest.fixture
def temperature_source():
    return (EXAMPLES_DIR / "basics" / "temperature.sigil").read_text()

@pytest.fixture
def loan_source():
    return (EXAMPLES_DIR / "rules" / "loan_eligibility.sigil").read_text()
```

---

## Git Conventions

### Commit Messages
```
<type>: <short description>

<optional body explaining why>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `spec`

Examples:
```
feat: implement lexer with indentation tracking
test: add 50 lexer test cases covering all token types
spec: fix GRAMMAR.peg to handle block-form then clauses
docs: update STATUS.md after lexer completion
```

### Branch Strategy
- `main` — stable, all tests pass
- Feature branches when needed: `feat/lexer`, `feat/parser`

---

## File Organization Rules

1. **One concept per file.** `tokens.py` has token definitions. `lexer.py` has the lexer. Don't merge them.
2. **Keep files under 400 lines.** If a file grows beyond this, split it.
3. **No circular imports.** Dependency flows: `tokens` ← `lexer` ← `parser` ← `ast` ← `types` ← `interpreter`
4. **Test files mirror source files.** `src/sigil/lexer/lexer.py` → `tests/lexer/test_lexer.py`

---

## Documentation in Code

- **Docstrings**: Module-level docstrings required. Function docstrings for public API.
- **No inline comments on obvious code.** Only comment *why*, never *what*.
- **Type hints ARE the documentation** for function signatures.

```python
# Good
def tokenize(source: str, filename: str = "<stdin>") -> list[Token]:
    """Tokenize Sigil source code into a list of tokens.

    Handles indentation tracking, string interpolation, and unit literals.
    Raises SigilLexError on invalid input with source location.
    """

# Bad — over-documented
def tokenize(source: str, filename: str = "<stdin>") -> list[Token]:
    """Tokenize Sigil source code into a list of tokens.

    Args:
        source: The source code string to tokenize. Must be valid UTF-8.
        filename: The filename for error reporting. Defaults to "<stdin>".

    Returns:
        A list of Token objects representing the tokenized input.
        The last token is always EOF.

    Raises:
        SigilLexError: If the source contains invalid tokens.

    Examples:
        >>> tokenize("42")
        [Token(NUMBER, "42", 1, 1), Token(EOF, "", 1, 3)]
    """
    # This level of docs is overkill for an internal function.
    # The type hints already tell you the args, return type.
    # Save verbose docs for the public-facing user guide.
```

---

## Sigil Language Conventions (for .sigil files)

When writing or modifying example `.sigil` files:
- 2-space indentation
- Keywords in lowercase
- Symbols prefixed with `:` (`:active`, `:critical`)
- One blank line between top-level declarations
- Comments with `--`
- File header comment with filename and description
