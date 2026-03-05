# Sigil: Technical Architecture

## System Overview

```
                    ┌─────────────────────────────────────────────┐
                    │              SIGIL ECOSYSTEM                 │
                    │                                             │
  Natural Language  │  ┌──────────┐    ┌──────────┐              │
  ─────────────────►│  │  Neural   │───►│  .sigil  │              │
  (human or LLM)   │  │  Parser   │    │  source  │              │
                    │  │ (Python)  │    │   file   │              │
                    │  └──────────┘    └────┬─────┘              │
                    │                       │                     │
                    │                       ▼                     │
                    │              ┌─────────────────┐            │
                    │              │   SIGIL COMPILER │            │
                    │              │   PIPELINE       │            │
                    │              │                  │            │
                    │              │  ┌────────────┐  │            │
                    │              │  │   Lexer    │  │            │
                    │              │  │ (Python)   │  │            │
                    │              │  └─────┬──────┘  │            │
                    │              │        │ tokens   │            │
                    │              │        ▼          │            │
                    │              │  ┌────────────┐  │            │
                    │              │  │  Parser    │  │            │
                    │              │  │  (PEG)     │  │            │
                    │              │  └─────┬──────┘  │            │
                    │              │        │ CST     │            │
                    │              │        ▼          │            │
                    │              │  ┌────────────┐  │            │
                    │              │  │    AST     │  │            │
                    │              │  │  Builder   │  │            │
                    │              │  └─────┬──────┘  │            │
                    │              │        │ AST     │            │
                    │              │        ▼          │            │
                    │              │  ┌────────────┐  │            │
                    │              │  │   Type     │  │            │
                    │              │  │  Checker   │  │            │
                    │              │  └─────┬──────┘  │            │
                    │              │        │ typed   │            │
                    │              │        │ AST     │            │
                    │              └────────┼─────────┘            │
                    │                       │                     │
                    │                       ▼                     │
                    │              ┌─────────────────┐            │
                    │              │  INTERPRETER     │            │
                    │              │  (tree-walking)  │            │
                    │              │                  │            │
                    │              │  ┌────────────┐  │            │
                    │              │  │   Rule     │  │   ┌──────────────┐
                    │              │  │  Engine    │◄─┼──►│  Rust Core   │
                    │              │  └────────────┘  │   │ (sigil_core) │
                    │              │  ┌────────────┐  │   │              │
                    │              │  │ Constraint │  │   │ - solver     │
                    │              │  │  Solver    │  │   │ - matcher    │
                    │              │  └────────────┘  │   │ - trace opt  │
                    │              │  ┌────────────┐  │   └──────────────┘
                    │              │  │   Trace    │  │
                    │              │  │  Logger    │  │   ┌──────────────┐
                    │              │  └────────────┘  │   │ Python FFI   │
                    │              │  ┌────────────┐  │   │              │
                    │              │  │  Neural    │◄─┼──►│ - torch      │
                    │              │  │  Bridge    │  │   │ - transformers│
                    │              │  └────────────┘  │   │ - numpy      │
                    │              └─────────┬────────┘   └──────────────┘
                    │                       │                     │
                    │                       ▼                     │
                    │              ┌─────────────────┐            │
                    │              │     OUTPUT       │            │
                    │              │                  │            │
                    │              │  Decision        │            │
                    │              │  + Trace         │            │
                    │              │  + Explanation    │            │
                    │              └─────────────────┘            │
                    └─────────────────────────────────────────────┘
```

## Component Architecture

### 1. Lexer (`src/sigil/lexer/`)

The lexer converts Sigil source text into a stream of tokens.

**Design decisions:**
- **Indentation-aware**: Like Python, Sigil uses indentation for block structure (more natural for NL-style syntax)
- **Context-sensitive keywords**: `when`, `then`, `and` are keywords only in rule context; they can be identifiers elsewhere
- **String interpolation**: `"Temperature is {sensor.temp} degrees"` — common in NL-oriented code
- **Unicode identifiers**: Support for domain-specific terminology

**Token categories:**
```
KEYWORDS:    rule, when, then, and, or, not, if, else, given, define,
             as, is, exceeds, below, between, any, all, none, in,
             import, export, module, type, neural, explain, with,
             true, false, none, using, from, compute, return, trace
OPERATORS:   +, -, *, /, =, !=, <, >, <=, >=, .
DELIMITERS:  (, ), [, ], {, }, :, ,
LITERALS:    INTEGER, FLOAT, STRING, BOOLEAN
IDENTIFIERS: [a-zA-Z_][a-zA-Z0-9_]*
INDENT:      indentation increase
DEDENT:      indentation decrease
NEWLINE:     logical line separator
COMMENT:     -- single line, {- multi-line -}
```

### 2. Parser (`src/sigil/parser/`)

PEG (Parsing Expression Grammar) parser producing a concrete syntax tree.

**Why PEG:**
- Unambiguous by construction (ordered choice eliminates ambiguity)
- Linear-time parsing via packrat memoization
- Composable — new syntax can be added without breaking existing rules
- Natural fit for constrained NL (handles keyword-heavy grammar well)
- Well-studied for DSLs

**Parser library**: We'll use a Python PEG library (e.g., `parsimonious`, `pe`, or a hand-written recursive descent parser for maximum control).

**Error recovery**: The parser must produce useful ASTs even from incomplete/malformed input — critical for:
- LLM-generated code that may have minor errors
- Interactive REPL usage
- Editor/LSP integration

### 3. AST (`src/sigil/ast/`)

The Abstract Syntax Tree is the core data structure. Sigil's AST has two representations:

**Surface AST** (from parsing constrained NL):
```python
RuleDecl(
    name="temperature_alert",
    conditions=[
        Comparison(
            left=FieldAccess("sensor", "temperature"),
            op=Exceeds,
            right=Literal(100, unit="degrees")
        ),
        Comparison(
            left=FieldAccess("sensor", "status"),
            op=Is,
            right=Literal("active")
        )
    ],
    conjunction=And,
    actions=[
        Action("trigger", "alert", params={"severity": "critical"})
    ],
    explanation="Temperature exceeded safe threshold"
)
```

**Core AST** (S-expression equivalent, for tooling/manipulation):
```python
SExpr(
    op="rule",
    args=[
        Symbol("temperature_alert"),
        SExpr(op="when", args=[
            SExpr(op="and", args=[
                SExpr(op=">", args=[
                    SExpr(op=".", args=[Symbol("sensor"), Symbol("temperature")]),
                    Literal(100)
                ]),
                SExpr(op="=", args=[
                    SExpr(op=".", args=[Symbol("sensor"), Symbol("status")]),
                    Keyword("active")
                ])
            ])
        ]),
        SExpr(op="then", args=[...]),
        SExpr(op="explain", args=[...])
    ]
)
```

Both representations are interconvertible. The surface AST is produced by the parser; the core AST is used by the interpreter and tooling.

### 4. Type System (`src/sigil/types/`)

Sigil has a pragmatic type system optimized for rule correctness:

**Base types:**
```
Number      -- unified numeric (int or float, determined by context)
Text        -- UTF-8 strings
Boolean     -- true / false
Symbol      -- :keyword style atoms
Unit        -- numbers with units (100 degrees, 50 percent, 3 seconds)
List[T]     -- homogeneous lists
Record{...} -- named field collections (structural typing)
Option[T]   -- explicit nullability
```

**Domain types (for neuro-symbolic domains):**
```
Confidence  -- 0.0 to 1.0, result of neural operations
Trace       -- execution trace record
Rule        -- first-class rule values
Constraint  -- composable constraint objects
```

**Type checking goals:**
- Catch unit mismatches at parse time (`temperature in celsius > 100 degrees fahrenheit` → error)
- Ensure rule completeness (exhaustive conditions)
- Verify constraint satisfiability where possible
- Type-check across the neural/symbolic boundary (neural returns must match expected types)

### 5. Interpreter (`src/sigil/interpreter/`)

Tree-walking interpreter with built-in tracing.

**Execution model:**
```
1. Load program AST
2. Resolve imports (Python FFI, Rust FFI, other Sigil modules)
3. Register rules in rule engine
4. For each input:
   a. Match input against rule conditions
   b. Evaluate matching rules (with conflict resolution)
   c. Execute actions
   d. Record trace
   e. Return (decision, trace, explanation)
```

**Environment model:**
- Lexical scoping within rules
- Module-level bindings for definitions
- Immutable by default; `mutable` keyword for explicit state
- Closures for higher-order rule composition

**Conflict resolution** (when multiple rules match):
```sigil
-- Priority is explicit
rule high_priority with priority 10:
  when temperature exceeds 200 then emergency_shutdown

rule low_priority with priority 1:
  when temperature exceeds 100 then alert
```

### 6. Rule Engine (`src/sigil/interpreter/rule_engine.py`)

The core symbolic execution component:

- **Forward chaining**: Given facts, derive conclusions (data-driven)
- **Backward chaining**: Given a goal, find supporting facts (goal-driven)
- **Rete algorithm**: Efficient pattern matching for large rule sets (future optimization)

**Rule composition:**
```sigil
rule base_eligibility:
  when age is between 21 and 65
  and income exceeds 30000
  then eligible_base is true

rule credit_check:
  when credit_score exceeds 680
  then credit_ok is true

rule final_eligibility:
  when eligible_base is true
  and credit_ok is true
  then approve_loan
```

Rules compose by sharing the fact space. The trace shows exactly which rules fired and in what order.

### 7. Neural Bridge (`src/sigil/interpreter/neural_bridge.py`)

The explicit boundary between neural and symbolic:

```sigil
neural classify_sentiment from review_text:
  model "distilbert-sentiment"
  returns Confidence
  threshold 0.8
  fallback to neutral

-- The neural result feeds into symbolic rules
rule handle_review:
  given sentiment from classify_sentiment(review.text)
  when sentiment is negative with confidence above 0.9
  then escalate to support_team
```

**Neural bridge guarantees:**
- Every neural call is explicitly marked
- Confidence scores are first-class values
- Fallback behavior is mandatory
- Neural results are cached with TTL
- Traces distinguish neural vs symbolic steps

### 8. FFI Layer (`src/sigil/ffi/`)

#### Python FFI
```sigil
import python pandas as pd
import python sklearn.ensemble.RandomForestClassifier

define training_data as pd.read_csv("data.csv")
define model as RandomForestClassifier(n_estimators: 100)
```

Implementation: Python FFI is native since the interpreter runs on Python. Sigil values marshal to/from Python objects with type checking at the boundary.

#### Rust FFI (`src/sigil_core/`)
```sigil
import rust sigil_core::solver
import rust sigil_core::constraint_engine

-- Hot-path symbolic execution in Rust
using rust sigil_core::evaluate_rules(rules, facts)
```

Implementation: PyO3/maturin for Rust-Python binding. The Rust core handles:
- High-performance constraint solving
- Pattern matching (Rete algorithm)
- Trace serialization
- Bytecode VM (future)

### 9. Standard Library (`src/sigil/stdlib/`)

```
sigil.rules      -- rule combinators, priority, conflict resolution
sigil.types      -- type constructors, validators, unit conversions
sigil.trace      -- trace formatting, filtering, export
sigil.io         -- file I/O, network, serialization
sigil.math       -- numeric operations, statistics
sigil.text       -- string manipulation, pattern matching
sigil.time       -- temporal reasoning, scheduling
sigil.logic      -- boolean algebra, constraint helpers
sigil.neural     -- neural backend configuration, model registry
sigil.explain    -- explanation generation, natural language output
```

## Data Flow

### Compilation Pipeline

```
Source (.sigil)
    │
    ▼
[Lexer] ──── character stream → token stream
    │
    ▼
[Parser] ──── token stream → CST (concrete syntax tree)
    │
    ▼
[AST Builder] ──── CST → AST (surface form)
    │
    ▼
[Desugarer] ──── surface AST → core AST (S-expression form)
    │
    ▼
[Type Checker] ──── core AST → typed AST (with type annotations)
    │
    ▼
[Optimizer] ──── typed AST → optimized AST (constant folding, dead rule elimination)
    │
    ▼
[Interpreter] ──── optimized AST → execution with traces
```

### Runtime Data Flow

```
Input Facts (dict/record)
    │
    ├──► [Rule Index] ──── fast lookup of potentially matching rules
    │         │
    │         ▼
    ├──► [Condition Evaluator] ──── evaluate rule conditions against facts
    │         │
    │         ▼
    │    [Conflict Resolver] ──── select winning rules by priority/specificity
    │         │
    │         ▼
    │    [Action Executor] ──── execute rule actions
    │         │
    │         ├──► [Fact Assertion] ──── add new facts (forward chaining)
    │         ├──► [Side Effects] ──── alerts, API calls, etc.
    │         └──► [Trace Entry] ──── record what happened and why
    │
    ▼
Output: (decision: Value, trace: Trace, explanation: Text)
```

## Performance Targets

| Operation | Target | Rationale |
|-----------|--------|-----------|
| Lexing + Parsing | < 10ms for 1000-line program | Must be interactive |
| Type checking | < 50ms for 1000-line program | Must not slow down iteration |
| Rule evaluation (symbolic) | < 1ms per decision | Core value proposition |
| Rule evaluation (with neural) | < 500ms per decision | LLM latency dominated |
| Trace generation | < 0.1ms overhead per rule | Must be always-on |
| Python FFI call | < 1ms overhead per call | Amortized over computation |
| Rust FFI call | < 0.01ms overhead per call | Near-native performance |

## Error Handling Philosophy

Sigil distinguishes three error categories:

1. **Parse errors**: Invalid syntax → helpful error message with suggestion
2. **Type errors**: Type mismatch → caught at check time, not runtime
3. **Runtime errors**: Evaluation failure → trace shows exactly where and why

```
Error at line 5, column 12:
  when temperature exceeds "hot"
                           ^^^^^
  Type mismatch: 'exceeds' expects Number, got Text ("hot")

  Did you mean:
    when temperature exceeds 100
    when temperature_label is "hot"
```

## Future Architecture (Phase 3+)

### Bytecode VM
Replace tree-walking with a stack-based bytecode VM for 10-100x performance improvement on symbolic execution.

### LSP Server
Language Server Protocol implementation for editor integration (syntax highlighting, autocomplete, diagnostics, go-to-definition).

### WASM Target
Compile Sigil to WebAssembly for browser-based execution — enabling client-side rule evaluation.

### Distributed Execution
Rule evaluation across multiple nodes for large-scale decision systems (millions of decisions/second).
