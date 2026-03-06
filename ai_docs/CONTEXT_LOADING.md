# Context Loading Guide for AI Agents

This document tells AI coding assistants (Claude Code, etc.) how to efficiently
load context for working on the Sigil project.

---

## Quick Start (< 2 minutes)

If you need to make a small change or fix a bug:

1. Read `CLAUDE.md` (loaded automatically)
2. Read `ai_docs/STATUS.md` — know what's implemented
3. Read the relevant source file you're modifying
4. Run tests: `pytest tests/ -v`

---

## Full Context Load (for substantial work)

### Step 1: Understand the project (read in order)
```
CLAUDE.md                          → Project overview, commands, constraints
ai_docs/STATUS.md                  → What exists, what's next, open issues
ai_docs/CONVENTIONS.md             → Code style, patterns, testing rules
PRP/<latest-sprint>.md             → What we're currently building
```

### Step 2: Understand the language (read as needed)
```
docs/design/SYNTAX.md              → Language syntax (THE syntax reference)
docs/spec/GRAMMAR.peg              → Formal grammar (THE parsing reference)
docs/spec/SEMANTICS.md             → What programs mean
docs/design/TYPE_SYSTEM.md         → Type system
```

### Step 3: Understand the architecture (read for design work)
```
docs/ARCHITECTURE.md               → System architecture
ai_docs/ARCHITECTURE_DECISIONS.md  → Why decisions were made
docs/design/INTEROP.md             → Python/Rust FFI
docs/VISION.md                     → Philosophy and principles
```

### Step 4: Understand the domain (read for research/design)
```
docs/research/NEURO_SYMBOLIC_AI_LANDSCAPE.md
docs/research/LISP_AND_FUNCTIONAL_PROGRAMMING.md
docs/research/EXISTING_DSLS_AND_LANGUAGES.md
docs/research/COMPILER_AND_LANGUAGE_DESIGN.md
docs/research/LANGUAGE_INTEROP_DEEP_DIVE.md
docs/research/BIBLIOGRAPHY.md
```

---

## Task-Specific Context

### Working on the Lexer
```
Read: docs/spec/GRAMMAR.peg (lexical rules section)
Read: src/sigil/lexer/ (all files)
Read: tests/lexer/ (all files)
Read: ai_docs/CONVENTIONS.md (token/dataclass patterns)
Reference: examples/*.sigil (tokenization targets)
```

### Working on the Parser
```
Read: docs/spec/GRAMMAR.peg (full grammar)
Read: docs/design/SYNTAX.md (syntax reference)
Read: src/sigil/parser/ (all files)
Read: src/sigil/ast/ (AST node definitions)
Read: tests/parser/ (all files)
Reference: examples/*.sigil (parse targets)
```

### Working on the Interpreter
```
Read: docs/spec/SEMANTICS.md (operational semantics)
Read: docs/ARCHITECTURE.md (execution model section)
Read: src/sigil/interpreter/ (all files)
Read: src/sigil/ast/ (AST nodes being evaluated)
Read: tests/interpreter/ (all files)
```

### Working on the Type System
```
Read: docs/design/TYPE_SYSTEM.md (type system spec)
Read: src/sigil/types/ (all files)
Read: tests/ (type-related tests)
```

### Working on FFI / Rust Core
```
Read: docs/design/INTEROP.md (FFI design)
Read: ai_docs/ARCHITECTURE_DECISIONS.md (ADR-002)
Read: src/sigil/ffi/ (Python FFI)
Read: src/sigil_core/ (Rust crate)
```

---

## Dependency Graph (What Depends on What)

```
tokens.py ← lexer.py ← parser.py ← ast/nodes.py ← types/ ← interpreter/
                                                           ← ffi/
                                                           ← stdlib/
```

Never introduce circular dependencies. This flow is sacred.

---

## Validation Checklist (Before Submitting Changes)

1. [ ] `ruff check src/ tests/` passes
2. [ ] `pytest tests/ -v` passes
3. [ ] New code has tests
4. [ ] AST nodes are frozen dataclasses
5. [ ] Error messages include source location
6. [ ] All 5 example .sigil files still work (if touching lexer/parser)
7. [ ] `ai_docs/STATUS.md` updated if state changed
8. [ ] No new dependencies added without justification
