# CLI Reference

The `sigil` command-line tool provides commands for running, checking, and inspecting Sigil programs.

---

## Installation

```bash
pip install sigil-lang
```

Verify:

```bash
sigil --help
```

---

## Commands

### `sigil run`

Execute a Sigil program.

```bash
sigil run FILE [--trace] [--input JSON]
```

| Flag | Description |
|------|-------------|
| `FILE` | Path to a `.sigil` file |
| `--trace` | Show full execution trace |
| `--input JSON` | Provide input data as a JSON object |

**Examples:**

```bash
# Run a program
sigil run hello.sigil

# Run with input data
sigil run check.sigil --input '{"temperature": 120}'

# Run with full trace output
sigil run check.sigil --input '{"temperature": 120}' --trace
```

**Input format:**

The `--input` flag accepts a JSON object. Keys become variable bindings in the Sigil environment. Values are automatically converted:

| JSON | Sigil |
|------|-------|
| `"text"` | Text |
| `42`, `3.14` | Number |
| `true`, `false` | Boolean |
| `null` | None |
| `[1, 2, 3]` | List |
| `{"k": "v"}` | Record |
| `":symbol"` | Symbol (strings starting with `:`) |

---

### `sigil check`

Type-check a Sigil program without running it.

```bash
sigil check FILE
```

**Examples:**

```bash
sigil check loan_eligibility.sigil
```

Output shows errors, warnings, and suggestions:

```
line 12: error: Type mismatch in comparison
  hint: Use a numeric threshold
line 20: warning: Unused variable 'temp'

1 error(s), 1 warning(s)
```

Exit code is `1` if there are errors, `0` otherwise.

---

### `sigil repl`

Start an interactive Read-Eval-Print Loop.

```bash
sigil repl
```

The REPL lets you enter Sigil declarations and expressions interactively:

```
sigil> define x as 42
sigil> rule check: when x exceeds 10 then print "big"
sigil> evaluate check
big
```

---

### `sigil lex`

Dump the token stream for a Sigil file. Useful for debugging the lexer.

```bash
sigil lex FILE
```

**Example:**

```bash
sigil lex hello.sigil
```

Output:

```
   1:0    COMMENT        '-- hello.sigil'
   4:0    DEFINE         'define'
   4:7    IDENTIFIER     'greeting'
   4:16   AS             'as'
   4:19   STRING         '"Hello from Sigil!"'
   ...
```

---

### `sigil parse-ast`

Dump the AST (Abstract Syntax Tree) for a Sigil file. Useful for debugging the parser.

```bash
sigil parse-ast FILE
```

**Example:**

```bash
sigil parse-ast hello.sigil
```

---

### `sigil parse`

Parse natural language into Sigil code.

```bash
sigil parse "TEXT"
```

!!! info "Not yet implemented"
    The NL-to-Sigil parser is planned for Phase 4. This command currently outputs a placeholder message.

---

### `sigil fmt`

Format a Sigil file.

```bash
sigil fmt FILE
```

!!! info "Not yet implemented"
    The formatter is planned for Phase 4.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (lex error, parse error, type error, runtime error, or file not found) |
