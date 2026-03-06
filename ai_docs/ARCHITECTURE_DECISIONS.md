# Architecture Decision Records

Every significant design decision, why it was made, and what was rejected.
Read this before proposing changes to the architecture.

---

## ADR-001: Language Name — Sigil

**Date**: 2026-03-06
**Status**: Accepted

**Context**: Need a name that evokes the bridge between neural and symbolic worlds.

**Decision**: Sigil — a symbolic mark with inherent power/meaning. Short, memorable, distinctive. File extension `.sigil`.

**Alternatives rejected**:
- Synap (too biological, hard to search)
- Rune (existing usages in gaming, Unicode)
- Loom (too generic, textile connotation)

---

## ADR-002: Python + Rust Core (Not Pure Rust, Not JVM)

**Date**: 2026-03-06
**Status**: Accepted

**Context**: The language needs access to the ML/AI ecosystem AND high-performance symbolic execution.

**Decision**: Python interpreter with Rust core for hot paths, connected via PyO3/maturin.

**Why Python**:
- The ML ecosystem (PyTorch, HuggingFace, scikit-learn) is in Python
- Rapid prototyping of language features
- Sigil users (data scientists, domain experts) know Python
- Zero-cost FFI since the interpreter runs on Python

**Why Rust core** (not pure Python):
- Symbolic execution needs <1ms latency for production use
- Constraint solving and pattern matching benefit from native performance
- Rust compiles to WASM (future browser deployment)
- Memory safety without GC overhead

**Why not pure Rust**:
- Slower iteration on language design
- ML ecosystem access requires FFI anyway
- Target users are more familiar with Python

**Why not JVM** (Kotlin/Clojure style):
- JVM startup time hurts CLI experience
- ML ecosystem is in Python, not Java
- JVM memory footprint is heavy for edge/embedded deployment

**Why not Zig**:
- Ecosystem too young; fewer libraries
- No direct Python interop story
- Good option to revisit for systems-level deployment later

---

## ADR-003: Constrained Natural Language Syntax

**Date**: 2026-03-06
**Status**: Accepted

**Context**: Sigil needs to be readable by domain experts AND reliably generable by LLMs.

**Decision**: Constrained NL — formal PEG grammar that *reads* like English but parses deterministically.

**Key properties**:
- ~30 keywords, all common English words
- `when X exceeds Y` instead of `if X > Y` (but symbolic operators also supported)
- Indentation-based blocks (like Python)
- Flat structure, minimal nesting
- Explicit types at module boundaries

**Why not S-expressions** (LISP-style):
- Domain experts cannot read `(when (> (. sensor temp) 100))`
- S-expressions are the CORE layer (hidden), not the surface
- Sigil has a two-layer design: NL surface ↔ S-expression core

**Why not ML/Haskell style**:
- Pattern matching syntax is powerful but intimidating for non-programmers
- Haskell's type system adds complexity beyond what Sigil needs
- We borrow concepts (ADTs, pattern matching) but with NL syntax

**Why not free-form NL** (like AppleScript):
- AppleScript proved this fails — rigid syntax that *looks* flexible creates confusion
- PEG grammar ensures deterministic parsing
- Constrained NL has succeeded (Inform 7, within its domain)

**The two-layer principle**:
The NL surface desugars to S-expressions internally. This gives us:
- Human readability (surface)
- Machine manipulability (core)
- LLM-friendly generation (surface)
- Tool-friendly analysis (core)

---

## ADR-004: Hand-Written Recursive Descent Parser

**Date**: 2026-03-06
**Status**: Accepted

**Context**: Need a parser for Sigil's PEG grammar.

**Decision**: Hand-written recursive descent parser in Python.

**Why not a PEG library** (parsimonious, pe, Lark):
- Maximum control over error messages (critical for UX)
- No dependency on library maintenance/compatibility
- Easier to debug (Python stack traces map to grammar rules)
- Educational value — understanding the parser deeply informs language design
- Can always switch to a library later if maintenance burden grows

**Why not parser combinators**:
- Functionally equivalent to hand-written RD
- Library overhead for same flexibility
- Python combinator libraries have performance concerns

**Why not generated parsers** (ANTLR, tree-sitter for parsing):
- Less control over error recovery and messages
- Generated code is hard to debug
- Tree-sitter is planned for EDITOR integration, not compilation

---

## ADR-005: Tree-Walking Interpreter First

**Date**: 2026-03-06
**Status**: Accepted

**Context**: Need an execution strategy for Sigil programs.

**Decision**: Start with tree-walking interpreter. Migrate to bytecode VM later.

**The proven path** (used by Python, Ruby, Lua, JavaScript):
1. Tree-walking interpreter (rapid iteration, easy debugging)
2. Bytecode VM (10-100x performance improvement)
3. JIT compilation (if needed)

**Why tree-walking first**:
- Simplest to implement (days, not weeks)
- Easy to add tracing (insert trace points at every AST node)
- Python function call overhead is acceptable for rule evaluation (<10ms)
- Language semantics are still evolving — easy to change evaluation rules
- "Make it work, make it right, make it fast" — we're at step 1

**Why not bytecode from the start**:
- Premature optimization — we don't know the hot paths yet
- Instruction set design requires stable semantics first
- Debugging bytecode is harder than debugging AST evaluation
- The Rust core will handle performance-critical paths anyway

**Migration plan**:
- Phase 1-2: Tree-walking interpreter (Python)
- Phase 3: Rust core for hot paths (constraint solving, pattern matching)
- Phase 5: Bytecode VM in Rust (if tree-walking + Rust core isn't fast enough)

---

## ADR-006: Immutable AST Nodes (Frozen Dataclasses)

**Date**: 2026-03-06
**Status**: Accepted

**Context**: How should AST nodes be represented?

**Decision**: `@dataclass(frozen=True)` with tuple (not list) for sequences.

**Why frozen**:
- AST nodes should never be mutated after construction
- Enables hashing (caching, deduplication, set operations)
- Prevents bugs from accidental mutation
- Consistent with Sigil's immutability-by-default semantics
- Forces creation of new nodes for AST transformations (clean functional style)

**Why dataclasses** (not attrs, not NamedTuple, not plain classes):
- Standard library (no dependency)
- Good IDE support (autocomplete, refactoring)
- `frozen=True` provides immutability
- `__eq__`, `__hash__`, `__repr__` auto-generated

---

## ADR-007: Significant Whitespace (Indentation-Based Blocks)

**Date**: 2026-03-06
**Status**: Accepted

**Context**: How should blocks be delimited?

**Decision**: Significant whitespace, Python-style. Spaces only (no tabs).

**Why indentation** (not braces, not `end` keywords):
- Natural for NL-style syntax — `when...then` doesn't want braces
- Reduces visual noise
- Forces readable formatting
- Python/YAML developers are already familiar
- More AI-friendly (MoonBit research shows flat structure aids LLM generation)

**Why spaces only**:
- Eliminates tabs-vs-spaces ambiguity
- Python community settled this (PEP 8)
- LLMs generate spaces more reliably than tabs

**Indentation rules**:
- 2 spaces per level (consistent with example .sigil files)
- INDENT/DEDENT tokens emitted by lexer (Python's approach)
- Blank lines and comment-only lines don't affect indentation
- Tab characters produce a lexer error with suggestion to use spaces

---

## ADR-008: Neuro-Symbolic Boundary via `neural` Keyword

**Date**: 2026-03-06
**Status**: Accepted

**Context**: Sigil programs can invoke ML models. How should this boundary be marked?

**Decision**: The `neural` keyword is the only way to introduce non-determinism. It requires:
1. A model identifier
2. A return type declaration
3. A confidence threshold
4. A mandatory fallback value

**Why explicit marking**:
- Users and auditors must know where non-determinism exists
- Traces distinguish neural vs symbolic evaluation steps
- Type checker can enforce constraints across the boundary
- Fallback guarantees the program always produces a result

**Why mandatory fallback**:
- Neural models can fail (timeout, low confidence, error)
- A program that crashes on model failure is unusable in production
- The fallback must type-check against the declared return type

---

## Future ADRs (to be written when decisions are made)

- ADR-009: Standard library scope and design
- ADR-010: Module system resolution strategy
- ADR-011: Conflict resolution in rule sets
- ADR-012: Error recovery strategy in parser
- ADR-013: Trace format (structured data? JSON? custom?)
- ADR-014: Bytecode instruction set design (Phase 5)
- ADR-015: LSP server architecture (Phase 5)
