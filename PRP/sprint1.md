# Sprint 1 Complete: Lexer + Parser

> **Sprint**: Mar 1–15, 2026
> **Status**: DONE
> **What we built**: A working lexer and parser that can tokenize and parse all 5 Sigil example programs into Abstract Syntax Trees.

---

## Try It Yourself (Step by Step)

### Step 0: Prerequisites

You need **Python 3.11+** installed. Check with:

```bash
python3 --version
# Should print Python 3.11.x or higher (we used 3.14.3)
```

### Step 1: Clone and Enter the Project

```bash
cd /Users/ramkumar/code/billaram/sigil-lang
```

If starting fresh from a clone:
```bash
git clone https://github.com/billaram/sigil-lang.git
cd sigil-lang
```

### Step 2: Create a Virtual Environment

```bash
python3 -m venv .venv
```

This creates an isolated Python environment in `.venv/` so we don't pollute your system Python.

### Step 3: Activate the Virtual Environment

```bash
source .venv/bin/activate
```

Your prompt should now show `(.venv)` at the beginning. **You must do this every time you open a new terminal.**

To confirm it worked:
```bash
which python
# Should print: /Users/ramkumar/code/billaram/sigil-lang/.venv/bin/python
```

### Step 4: Install Sigil in Dev Mode

```bash
pip install -e ".[dev]"
```

What this does:
- `-e` = "editable" mode — changes to source code take effect immediately
- `.[dev]` = install the project + dev dependencies (pytest, ruff, mypy, hypothesis)

Confirm the `sigil` command works:
```bash
sigil --help
```

You should see:
```
usage: sigil [-h] {lex,parse-ast,run,repl,parse,check,fmt} ...

Sigil: A neuro-symbolic programming language

positional arguments:
  {lex,parse-ast,run,repl,parse,check,fmt}
                        Available commands
...
```

### Step 5: Read Your First Sigil Program

Open `examples/basics/hello.sigil` in your editor, or view it:

```bash
cat examples/basics/hello.sigil
```

```sigil
-- hello.sigil
-- The simplest Sigil program: a single rule evaluation

define greeting as "Hello from Sigil!"

rule hello_world:
  when true
  then print greeting
  explain "This is the simplest possible Sigil program"
```

This is a complete Sigil program. It:
1. Defines a constant `greeting` with value `"Hello from Sigil!"`
2. Declares a rule `hello_world` that always fires (when true) and prints the greeting

### Step 6: Lex It (Tokenize)

The **lexer** breaks source code into tokens — the smallest meaningful pieces (keywords, identifiers, strings, operators, etc.).

```bash
sigil lex examples/basics/hello.sigil
```

Output:
```
     4:1    DEFINE          'define'
     4:8    IDENTIFIER      'greeting'
     4:17   AS              'as'
     4:20   STRING          'Hello from Sigil!'
     4:39   NEWLINE         '\n'
     6:1    RULE            'rule'
     6:6    IDENTIFIER      'hello_world'
     6:17   COLON           ':'
     6:18   NEWLINE         '\n'
     7:1    INDENT          ''
     7:3    WHEN            'when'
     7:8    TRUE            'true'
     7:12   NEWLINE         '\n'
     8:3    THEN            'then'
     8:8    IDENTIFIER      'print'
     8:14   IDENTIFIER      'greeting'
     8:22   NEWLINE         '\n'
     9:3    EXPLAIN         'explain'
     9:11   STRING          'This is the simplest possible Sigil program'
     9:56   NEWLINE         '\n'
    10:1    DEDENT          ''
    10:1    EOF             ''
```

Each line shows: `line:column  TOKEN_TYPE  'value'`

Notice:
- **Comments** (lines 1–2) are skipped — they're not tokens
- **INDENT/DEDENT** tokens mark where blocks begin and end (like `{` and `}` in C)
- `define`, `rule`, `when`, `then`, `explain` are **keyword** tokens (not identifiers)
- `greeting`, `hello_world`, `print` are **identifier** tokens

### Step 7: Parse It (Build the AST)

The **parser** takes the token stream and builds an **Abstract Syntax Tree** (AST) — a structured representation of the program's meaning.

```bash
sigil parse-ast examples/basics/hello.sigil
```

Output:
```
Program(
  module=None
  imports=()
  declarations=
    (
      ConstDecl(
        name='greeting'
        value=
          Literal(
            value='Hello from Sigil!'
            kind='string'
          )
      )
      RuleDecl(
        name='hello_world'
        conditions=
          (
            BooleanCond(
              expression=
                Literal(
                  value=True
                  kind='bool'
                )
              value=True
            )
          )
        action=
          SimpleAction(
            name='greeting'
            target='print'
            params=()
          )
        priority=0
        given_clauses=()
        explain='This is the simplest possible Sigil program'
        trace=()
        metadata=()
      )
    )
)
```

This is the AST. It tells us:
- **Program** has no module declaration, no imports, and 2 declarations
- **ConstDecl**: `greeting = "Hello from Sigil!"` (a string literal)
- **RuleDecl**: `hello_world` with:
  - Condition: `BooleanCond(true is true)` — always fires
  - Action: `SimpleAction(print greeting)` — calls `print` with `greeting`
  - Explain: the explanation string
  - Priority: 0 (default)

### Step 8: Try a Bigger Example

Now try the temperature monitoring program — it has types, constants, multiple rules with priorities, and compound conditions:

```bash
cat examples/basics/temperature.sigil
```

```sigil
module examples.temperature

type SensorReading is record:
  sensor_id: Text
  temperature: Number
  status: Symbol

define SAFE_THRESHOLD as 100
define WARNING_THRESHOLD as 80
define CRITICAL_THRESHOLD as 150

rule emergency_shutdown with priority 100:
  when reading temperature exceeds CRITICAL_THRESHOLD
  then shutdown_system
  explain "Temperature {reading.temperature} exceeds critical threshold"

rule temperature_alert with priority 10:
  when reading temperature exceeds SAFE_THRESHOLD
  and reading status is :active
  then trigger alert with severity :high
  explain "Temperature exceeded safe threshold"
...
```

Lex it:
```bash
sigil lex examples/basics/temperature.sigil
```

Parse it:
```bash
sigil parse-ast examples/basics/temperature.sigil
```

In the AST output, notice how:
- `reading temperature` becomes `FieldAccess(object=Identifier('reading'), field='temperature')` — space-based field access!
- `:active` and `:high` are `SymbolLit` nodes — Sigil's atom/enum-like values
- `and` joins conditions into `CompoundCond(operator='and', left=..., right=...)`
- Each rule has a `priority` extracted from `with priority N`

### Step 9: Try All 5 Examples

```bash
sigil parse-ast examples/rules/loan_eligibility.sigil
sigil parse-ast examples/neuro_symbolic/medical_triage.sigil
sigil parse-ast examples/neuro_symbolic/compliance_checker.sigil
```

All 5 examples lex and parse without errors. These cover:
- **hello.sigil** — minimal rule
- **temperature.sigil** — types, constants, multi-rule with priorities
- **loan_eligibility.sigil** — types, rules, compute blocks, neural declarations, main block
- **medical_triage.sigil** — neural integration, quantified conditions (`any X in Y`)
- **compliance_checker.sigil** — complex conditions, list constants, for-each loops

### Step 10: Run the Tests

```bash
pytest tests/ -v
```

You should see **166 tests, all passing**:
- 91 lexer tests (numbers, strings, symbols, keywords, operators, comments, indentation, edge cases)
- 75 parser tests (declarations, conditions, expressions, statements, error cases, all 5 examples)

To run just the lexer or parser tests:
```bash
pytest tests/lexer/ -v     # 91 lexer tests
pytest tests/parser/ -v    # 75 parser tests
```

### Step 11: Run the Linter

```bash
ruff check src/ tests/
```

Should print: `All checks passed!`

---

## What We Built (Architecture)

```
source text
    |
    v
 LEXER (src/sigil/lexer/lexer.py)
    | tokenize(source) -> list[Token]
    v
 Token Stream: [DEFINE, IDENTIFIER('greeting'), AS, STRING('Hello...'), NEWLINE, ...]
    |
    v
 PARSER (src/sigil/parser/parser.py)
    | parse(tokens) -> Program
    v
 Abstract Syntax Tree:
    Program
    ├── ConstDecl(name='greeting', value=Literal('Hello from Sigil!'))
    └── RuleDecl(name='hello_world', ...)
```

### Files Created

| File | What | Lines |
|------|------|-------|
| `src/sigil/errors.py` | Error types + SourceLocation | ~50 |
| `src/sigil/lexer/tokens.py` | TokenType enum (80+ keywords), Token dataclass | ~250 |
| `src/sigil/lexer/lexer.py` | Full tokenizer with indentation engine | ~400 |
| `src/sigil/ast/nodes.py` | 40+ frozen dataclass AST nodes | ~570 |
| `src/sigil/parser/parser.py` | Recursive descent parser | ~900 |
| `src/sigil/cli.py` | CLI with `lex` and `parse-ast` commands | ~110 |
| `tests/lexer/test_lexer.py` | 91 lexer tests | ~550 |
| `tests/parser/test_parser.py` | 75 parser tests | ~600 |
| `tests/conftest.py` | Shared test fixtures | ~40 |

### Key Design Decisions

1. **Hand-written recursive descent parser** — no parser libraries. Maximum control, fully debuggable.
2. **Frozen dataclasses for AST** — immutable nodes, tuples instead of lists. Safe to share and inspect.
3. **Indentation-based blocks** — Python-style. The lexer emits INDENT/DEDENT tokens so the parser doesn't deal with whitespace.
4. **Space-based field access** — `reading temperature` parses the same as `reading.temperature`. This is what makes Sigil read like English.
5. **80+ keywords** — `rule`, `when`, `then`, `exceeds`, `is below`, `is between`, etc. These are what make conditions readable.

### Grammar Gaps We Found

The formal grammar (GRAMMAR.peg) had 8 gaps when compared against the 5 example programs. All were fixed in the parser:

| Gap | Example | How We Handle It |
|-----|---------|-------------------|
| Space-based field access | `reading temperature` | Consecutive identifiers → FieldAccess |
| Parameterless compute | `compute collect_reasons returns List:` | `from` clause is optional |
| `becomes` keyword | `y becomes y + [...]` | BecomeStmt node |
| `empty list` | `fallback to empty list` | EmptyExpr node |
| `is not assigned` | `override is not assigned` | IsAssignedCond node |
| Actions setting values | `then age_eligible is true` | SetAction node |
| Multi-word actions | `trigger alert with severity :high` | SimpleAction with target + params |
| Positional action args | `log status :normal` | Auto-detected positional args |

---

## What's Next: Sprint 2

The lexer and parser turn `.sigil` source code into ASTs. But the AST just sits there — it doesn't **do** anything yet. The next sprint adds meaning:

### Phase 1.3: Type Checker
- Validate that types are used correctly (can't add a Text to a Number)
- Check that fields accessed on records actually exist
- Verify rule conditions reference declared variables

### Phase 1.4: Tree-Walking Interpreter
- **Execute** Sigil programs — evaluate rules, run compute blocks
- `sigil run examples/basics/hello.sigil` will actually print `"Hello from Sigil!"`
- Generate **execution traces** — the audit trail of which rules fired and why
- Interactive **REPL** — type Sigil expressions and see results

### What Running Hello Will Look Like (Goal)

```bash
$ sigil run examples/basics/hello.sigil
Hello from Sigil!

$ sigil run examples/basics/hello.sigil --trace
[trace] Evaluating rule 'hello_world'
[trace]   Condition: true is true → PASS
[trace]   Action: print greeting → "Hello from Sigil!"
[trace]   Explain: "This is the simplest possible Sigil program"
Hello from Sigil!
```

### What Running Temperature Will Look Like (Goal)

```bash
$ sigil run examples/basics/temperature.sigil --trace
[input] reading = SensorReading(sensor_id: "S1", temperature: 95, status: :active)

[trace] Evaluating rule 'emergency_shutdown' (priority 100)
[trace]   Condition: reading.temperature (95) exceeds CRITICAL_THRESHOLD (150) → FAIL

[trace] Evaluating rule 'temperature_alert' (priority 10)
[trace]   Condition: reading.temperature (95) exceeds SAFE_THRESHOLD (100) → FAIL

[trace] Evaluating rule 'temperature_warning' (priority 5)
[trace]   Condition: reading.temperature (95) is between 80 and 100 → PASS
[trace]   Condition: reading.status (:active) is :active → PASS
[trace]   Action: trigger alert with severity :medium
[trace]   Explain: "Temperature 95 approaching safe threshold"

Result: Alert triggered with severity :medium
```

That's the vision. The AST is the bridge — Sprint 1 built the bridge, Sprint 2 will walk across it.

---

## Quick Reference

```bash
# Activate environment (do this first, every terminal)
source .venv/bin/activate

# Lex a file (show tokens)
sigil lex examples/basics/hello.sigil

# Parse a file (show AST)
sigil parse-ast examples/basics/hello.sigil

# Run all tests
pytest tests/ -v

# Run just lexer/parser tests
pytest tests/lexer/ -v
pytest tests/parser/ -v

# Lint
ruff check src/ tests/

# All 5 example files
sigil parse-ast examples/basics/hello.sigil
sigil parse-ast examples/basics/temperature.sigil
sigil parse-ast examples/rules/loan_eligibility.sigil
sigil parse-ast examples/neuro_symbolic/medical_triage.sigil
sigil parse-ast examples/neuro_symbolic/compliance_checker.sigil
```
