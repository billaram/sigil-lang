# Context Loading Guide for AI Agents

This document describes how context is loaded for AI coding assistants working on Sigil.

---

## Automatic Context (via `.claude/rules/`)

Context is now **auto-loaded** based on which files you're editing. No need to manually read files.

### Global Rules (always loaded)
- `code-conventions.md` — Code style, naming, patterns
- `known-issues.md` — Known bugs and their fixes

### Path-Scoped Rules (loaded when editing matching files)
| Rule | Triggers when editing |
|------|----------------------|
| `sigil-syntax.md` | `**/*.sigil`, `src/sigil/parser/**`, `src/sigil/lexer/**` |
| `lexer.md` | `src/sigil/lexer/**`, `tests/lexer/**` |
| `parser.md` | `src/sigil/parser/**`, `tests/parser/**`, `src/sigil/ast/**` |
| `interpreter.md` | `src/sigil/interpreter/**`, `tests/interpreter/**` |
| `typechecker.md` | `src/sigil/types/**`, `tests/typechecker/**` |
| `modules.md` | `src/sigil/modules/**`, `tests/modules/**` |
| `stdlib.md` | `src/sigil/stdlib/**`, `tests/stdlib/**` |
| `testing.md` | `tests/**` |

### Deep Context (read manually when needed)
```
ai_docs/STATUS.md                  → What exists, what's next
ai_docs/CONVENTIONS.md             → Full code conventions
docs/design/SYNTAX.md              → Language syntax spec
docs/spec/GRAMMAR.peg              → Formal PEG grammar
docs/spec/SEMANTICS.md             → Operational semantics
docs/design/TYPE_SYSTEM.md         → Type system spec
docs/ARCHITECTURE.md               → System architecture
ai_docs/ARCHITECTURE_DECISIONS.md  → Why decisions were made
```

---

## Skills (Reusable Workflows)

Invoke with `/skill-name`:
- `/run-tests [subsystem]` — Run pytest with right flags
- `/validate-examples` — Run all .sigil examples
- `/fix-issue` — Structured bug-fixing workflow
- `/update-status` — Update STATUS.md after work
- `/add-syntax` — 10-step new syntax workflow
- `/new-sprint` — Create sprint plan from template

---

## Specialist Agents

Use via Task tool for domain-specific work:
- **compiler-expert** — Lexer, parser, AST, grammar
- **neuro-symbolic-expert** — Rule engines, chaining, neural bridge
- **testing-qa** — Test writing, coverage, validation
- **code-reviewer** — Read-only review (haiku model for speed)

---

## Dependency Graph

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
6. [ ] All example .sigil files still work (if touching lexer/parser)
7. [ ] `ai_docs/STATUS.md` updated if state changed
8. [ ] No new dependencies added without justification
