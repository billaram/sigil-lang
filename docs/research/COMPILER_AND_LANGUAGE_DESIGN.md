# Compiler and Language Design: Best Practices for Sigil

## 1. Parser Technology

### PEG (Parsing Expression Grammars)

Sigil uses PEG for parsing. Here's why, and the alternatives considered.

**PEG fundamentals** (Bryan Ford, POPL 2004):
- PEGs define languages via recursive descent with ordered choice
- Unlike CFGs (Context-Free Grammars), PEGs are inherently unambiguous
- The `/` operator (ordered choice) tries alternatives in order and commits to the first match
- This eliminates the "dangling else" and operator precedence ambiguities that plague CFG-based parsers

**Packrat parsing**:
- PEGs can be parsed in linear time O(n) via packrat memoization
- Memoize every rule at every position → guaranteed no backtracking revisits
- Trade-off: O(n) memory for O(n) time
- In practice, memory is acceptable for source files (not multi-GB inputs)

**Why PEG for Sigil specifically**:
1. **Keyword-heavy grammar**: Sigil uses English keywords (`when`, `then`, `exceeds`, `is between`). PEGs handle keyword-heavy grammars naturally via ordered choice.
2. **Unambiguous by construction**: Essential for both human understanding and LLM generation. No parser generator warnings about shift/reduce conflicts.
3. **Composable**: New syntax can be added by composing PEG rules without breaking existing grammar. Critical for language evolution.
4. **No separate lexer needed**: PEGs can handle both lexical and syntactic analysis in a single grammar (scannerless parsing). Though Sigil uses a separate lexer for indentation handling.

**Alternatives considered and rejected**:

| Parser Type | Why Rejected |
|-------------|-------------|
| LR/LALR (yacc, bison) | Ambiguity resolution is manual; shift/reduce conflicts with NL keywords |
| LL (recursive descent) | Would work, but PEG adds memoization and ordered choice for free |
| Earley | O(n³) worst case; overkill for an unambiguous grammar |
| GLR (tree-sitter) | Handles ambiguity by producing multiple parse trees; we want exactly one |
| Parser combinators | Equivalent to PEG in practice; libraries available in Python (good option) |

**Modern PEG developments**:
- **GPeg** (SLE 2021): Enables incremental reparsing in logarithmic time — only re-parses changed regions
- **DuckDB's runtime-extensible PEG parser** (CIDR 2025): PEGs can be extended at runtime with new rules
- **Grammar-constrained LLM decoding** (ACL 2025): PEG grammars used directly as decoding constraints for LLM output

### Tree-sitter (For Editor Integration)

While Sigil's compiler uses a PEG parser, **Tree-sitter** is the right choice for editor integration:

- **Incremental parsing**: Only re-parses changed regions (essential for IDE responsiveness)
- **Error recovery**: Produces useful ASTs from broken code (essential for editing in progress)
- **Used by**: Neovim, Helix, Zed, GitHub (syntax highlighting, code navigation)
- **How it works**: GLR-based with a custom DSL for grammar specification

Sigil should have both:
1. PEG parser for the compiler (correctness, simplicity)
2. Tree-sitter grammar for editors (incrementality, error recovery)

---

## 2. Implementation Strategy

### The Proven Path

Nearly every successful language follows the same implementation path:

```
Tree-walking interpreter → Bytecode VM → (Optional) Native compilation
```

| Language | Stage 1 | Stage 2 | Stage 3 |
|----------|---------|---------|---------|
| Python | Tree-walking | CPython bytecode VM | (PyPy JIT) |
| Ruby | Tree-walking (MRI 1.8) | YARV bytecode VM (1.9+) | (TruffleRuby JIT) |
| Lua | Tree-walking | Bytecode VM | LuaJIT |
| JavaScript | Tree-walking (early) | Bytecode VM | V8 TurboFan JIT |
| Java | — | JVM bytecode | HotSpot JIT |

**Sigil follows this path**:
- **Phase 1**: Tree-walking interpreter in Python (rapid iteration, easy debugging)
- **Phase 3**: Rust core for hot paths (constraint solving, pattern matching)
- **Phase 5**: Bytecode VM in Rust (10-100x over tree-walking)
- **Future**: LLVM backend for native compilation (if needed)

### Tree-Walking Interpreter Design

A tree-walking interpreter directly evaluates the AST:

```python
def evaluate(node: ASTNode, env: Environment) -> Value:
    match node:
        case Literal(value):
            return value
        case Identifier(name):
            return env.lookup(name)
        case BinaryOp(op, left, right):
            l = evaluate(left, env)
            r = evaluate(right, env)
            return apply_op(op, l, r)
        case RuleDecl(name, conditions, action):
            return evaluate_rule(name, conditions, action, env)
        case ComputeDecl(name, params, body):
            return Closure(params, body, env)
        ...
```

**Advantages**:
- Simple to implement (can be done in a week)
- Easy to debug (Python stack traces map to AST nodes)
- Natural for a traced language (insert trace points at every evaluation)
- Modification is cheap (change evaluation semantics without recompiling)

**Disadvantages**:
- Slow (Python function call overhead per AST node)
- Memory intensive (full AST in memory)

For Sigil's use case (rule evaluation, not number crunching), tree-walking performance is acceptable. Rules evaluate in <10ms, which meets the initial target.

### Bytecode VM Design (Future)

When performance matters, compile to a stack-based bytecode VM:

```
// Bytecode for: temperature > 100
LOAD_FIELD "temperature"    // push field value
LOAD_CONST 100              // push constant
COMPARE_GT                  // pop two, push boolean
```

**Stack-based vs register-based**:
| Property | Stack-based | Register-based |
|----------|------------|----------------|
| Instruction size | Smaller (no register operands) | Larger |
| Code generation | Simpler (just push/pop) | More complex (register allocation) |
| Dispatch overhead | More instructions | Fewer instructions |
| Examples | CPython, JVM, CLR | LuaJIT, Dalvik |

**Recommendation**: Start with stack-based (simpler). Optimize to register-based only if profiling shows dispatch overhead is the bottleneck.

---

## 3. LLVM (For Native Compilation)

**LLVM provides "compiler infrastructure as a service"**:
- **LLVM IR**: Strongly typed RISC-like intermediate representation
- **Optimization passes**: Battle-tested optimization pipeline (40+ passes)
- **Multi-target**: x86, ARM, RISC-V, WebAssembly, and more

**Languages built on LLVM**: Rust, Swift, Clang (C/C++/ObjC), Julia, Kotlin/Native, Zig, Crystal

**When Sigil would need LLVM**:
- If standalone native binaries are required
- If WebAssembly compilation is a priority (LLVM has a WASM backend)
- If embedded deployment (no Python runtime) is needed

**For now**: LLVM is overkill. Tree-walking + Rust hot paths provides sufficient performance. LLVM is a Phase 5+ consideration.

---

## 4. Language Interop Patterns

### Pattern A: Shared VM (Clojure/Java, Kotlin/JVM, Scala/Java)

```
Clojure source → Clojure compiler → JVM bytecode
Java source    → javac            → JVM bytecode
                                     ↓
                              JVM executes both
```

- **Overhead**: Near-zero (same bytecode, same GC, same types)
- **Interop quality**: Seamless object sharing
- **How Clojure does it**: All functions compile to JVM classes. `(.method object args)` syntax for Java interop. The compiler emits the same bytecode javac would produce.

**Relevance to Sigil**: Sigil's Python FFI follows this pattern — Sigil runs on the Python VM, so Python objects are directly accessible.

### Pattern B: ABI-Level FFI (Zig/C, Rust/C)

```
Zig source → Zig compiler → native binary (with C ABI)
C source   → Clang        → native binary (with C ABI)
                              ↓
                   Same ABI, direct function calls
```

- **How Zig does it**: `@cImport` and `@cInclude` directly parse C header files using Clang. Zero overhead — C functions are called directly. Zig can be used as a drop-in C compiler (`zig cc`).
- **How Rust does it**: `extern "C"` blocks declare C functions. Minimal overhead (function pointer dispatch).

**Relevance to Sigil**: The Rust core (sigil_core) uses this pattern via PyO3 — Rust functions are exposed to Python with minimal overhead.

### Pattern C: Managed FFI (Python/C, Java/C via JNI/Panama)

```
Python code → Python interpreter → ctypes/cffi → C library
```

- **Project Panama** (JDK 22, March 2024): Modern Java-C FFI
  - 4-5x faster than JNI in benchmarks
  - 90% reduction in implementation effort vs JNI
  - Safe off-heap memory allocation
  - No native code compilation required

**Relevance to Sigil**: PyO3/maturin is Sigil's managed FFI from Python to Rust. It handles memory management, type conversion, and error translation.

### Pattern D: Code Generation (UniFFI)

```
Rust source + UDL definition → UniFFI → Kotlin bindings
                                      → Swift bindings
                                      → Python bindings
```

- **UniFFI** (Mozilla): Generate FFI bindings from a single Rust crate to multiple target languages
- **Relevance to Sigil (future)**: If Sigil needs bindings for languages beyond Python (e.g., JavaScript/WASM, Swift for iOS), UniFFI could generate them from the Rust core.

---

## 5. Indentation-Sensitive Parsing

Sigil uses significant indentation (like Python, Haskell, YAML). This requires special handling:

### The INDENT/DEDENT Token Approach (Python's method)

The lexer tracks indentation levels and emits synthetic INDENT and DEDENT tokens:

```
rule temperature_check:       → RULE ID COLON NEWLINE
  when temperature exceeds 100 → INDENT WHEN ... NEWLINE
  then alert                   → THEN ... NEWLINE DEDENT
```

**Implementation**:
1. Lexer maintains an indentation stack (starts with [0])
2. At each line start, measure leading whitespace
3. If indent > top of stack: push indent, emit INDENT
4. If indent < top of stack: pop until matching level, emit DEDENT for each pop
5. If indent == top of stack: no INDENT/DEDENT emitted
6. At EOF: emit DEDENT for each remaining level > 0

**Challenges**:
- Tabs vs spaces (Sigil: spaces only, like Python PEP 8)
- Mixed indentation detection
- Blank lines and comments (shouldn't affect indentation tracking)
- Continuation lines (long expressions split across lines)

---

## 6. Error Recovery and Reporting

### Error Message Design

Good error messages are critical for both human users and LLM generators:

```
Error at line 12, column 8 in temperature_check.sigil:
  when temperature exceeds "hot"
                           ^^^^^
  Type mismatch: 'exceeds' expects Number, got Text ("hot")

  Suggestions:
    - Use a numeric threshold: when temperature exceeds 100
    - Compare text values with 'is': when temperature_label is "hot"
```

**Design principles** (from Elm's error message philosophy):
1. Show the source location with context
2. Explain what went wrong in plain English
3. Suggest what the user probably meant
4. If the error is from LLM generation, suggest the correct Sigil syntax

### Parser Error Recovery

The parser must continue after errors to report multiple issues:

**Synchronization tokens**: When an error is detected, skip tokens until a synchronization point (e.g., NEWLINE at top indent level, `rule` keyword, `define` keyword).

**Error nodes in AST**: Invalid syntax produces `ErrorNode` in the AST, allowing partial analysis of the rest of the program.

---

## 7. Reference Implementations Studied

| Resource | Type | Key Lessons for Sigil |
|----------|------|----------------------|
| *Crafting Interpreters* (Nystrom, 2021) | Book | Complete tree-walking → bytecode path in Java/C |
| CPython source code | Reference | Indentation lexing, bytecode compilation, C extensions |
| Lua 5.4 source code | Reference | Minimal, embeddable interpreter; register-based VM |
| Racket/PLT | Framework | Language-oriented programming; macros; DSL building |
| Lean 4 compiler | Reference | Dependent types; tactic framework; meta-programming |
| MoonBit compiler | Reference | AI-friendly grammar; multi-backend; fast compilation |
| Zig compiler | Reference | C interop; comptime; incremental compilation |
| Ruff (Python linter in Rust) | Reference | Rust for Python tooling; 10-100x faster than Python |

---

## 8. Testing Strategy for Language Implementations

### Test Categories

| Category | What It Tests | Sigil Example |
|----------|-------------|---------------|
| **Lexer tests** | Tokenization correctness | `"100 degrees"` → `[NUMBER(100), UNIT(degrees)]` |
| **Parser tests** | AST construction | Source → expected AST structure |
| **Type checker tests** | Type errors, inference | Unit mismatch detection |
| **Interpreter tests** | Evaluation correctness | Rule + facts → expected decision + trace |
| **Integration tests** | End-to-end pipeline | `.sigil` file → full output |
| **Property tests** | Invariants hold for random inputs | Parse ∘ prettyprint ∘ parse = parse (roundtrip) |
| **Error tests** | Error messages are helpful | Malformed input → expected error message |
| **Benchmark tests** | Performance regression | Rule evaluation < 1ms for 100-rule system |

### Property-Based Testing

Using Hypothesis (Python) or proptest (Rust):

```python
@given(sigil_programs())  # generate random valid Sigil programs
def test_parse_roundtrip(program):
    ast = parse(program)
    source = prettyprint(ast)
    ast2 = parse(source)
    assert ast == ast2  # parse(prettyprint(parse(x))) == parse(x)
```

Key properties:
1. **Roundtrip**: parse → prettyprint → parse produces equivalent AST
2. **Determinism**: Same program + same input → same output, always
3. **Trace completeness**: Every condition evaluation appears in the trace
4. **Type soundness**: Well-typed programs don't produce type errors at runtime
