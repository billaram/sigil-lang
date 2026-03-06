# Getting Started

## Prerequisites

- **Python 3.11+** — Sigil's interpreter is written in Python
- **pip** — Python package manager

Check your Python version:

```bash
python --version  # Should be 3.11 or higher
```

## Installation

### From PyPI (recommended)

```bash
pip install sigil-lang
```

### From source (development)

```bash
git clone https://github.com/billaram/sigil-lang.git
cd sigil-lang
pip install -e ".[dev]"
```

Verify the installation:

```bash
sigil --help
```

## Hello World

Create a file called `hello.sigil`:

```sigil
define greeting as "Hello from Sigil!"

rule hello_world:
  when true
  then print greeting
  explain "This is the simplest possible Sigil program"
```

Run it:

```bash
sigil run hello.sigil
```

Output:

```
Hello from Sigil!
```

## Your first rule

Rules are the heart of Sigil. Create `check.sigil`:

```sigil
define MAX_TEMP as 100

rule temperature_check:
  when temperature exceeds MAX_TEMP
  then print "ALERT: Temperature too high!"
  explain "Temperature exceeded the safe threshold"
```

Run it with input data:

```bash
sigil run check.sigil --input '{"temperature": 120}'
```

The rule fires because `120 > 100`. Try changing the temperature to `80` — the rule won't fire.

## Running with traces

Add `--trace` to see exactly how Sigil evaluated your program:

```bash
sigil run check.sigil --input '{"temperature": 120}' --trace
```

Traces show every condition evaluated, every rule that fired, and why. In regulated domains (finance, healthcare), the trace *is* the output.

## Interactive REPL

Start the interactive REPL to experiment:

```bash
sigil repl
```

```
sigil> define x as 42
sigil> rule check: when x exceeds 10 then print "big number"
sigil> evaluate check
big number
```

## Next steps

- **[Language Tour](../tour/index.md)** — Learn every feature step by step
- **[Sigil for Python Devs](../guides/sigil-for-python-devs.md)** — Quick translation guide
- **[Cookbook](../cookbook/index.md)** — Guided walkthroughs of real examples
