# Sigil Language Project — Glossary

> 355 terms across 14 categories. Each term is tagged with its implementation status.
> Use this as a research starting point — when you find a term you want to explore,
> check if there's already a deep-dive doc in `docs/research/`.

## Table of Contents

- [Category 1: Compiler / Lexer / Parser](#category-1-compiler--lexer--parser)
- [Category 2: AST Nodes / Grammar Rules](#category-2-ast-nodes--grammar-rules)
- [Category 3: Runtime / Interpreter / Execution Model](#category-3-runtime--interpreter--execution-model)
- [Category 4: Trace System](#category-4-trace-system)
- [Category 5: Type System](#category-5-type-system)
- [Category 6: Neuro-Symbolic AI](#category-6-neuro-symbolic-ai)
- [Category 7: Rule Engine](#category-7-rule-engine)
- [Category 8: Language Design / Syntax Philosophy](#category-8-language-design--syntax-philosophy)
- [Category 9: Module System / Standard Library](#category-9-module-system--standard-library)
- [Category 10: Interoperability / FFI](#category-10-interoperability--ffi)
- [Category 11: Functional Programming Concepts (Influences)](#category-11-functional-programming-concepts-influences)
- [Category 12: Related Languages and Systems](#category-12-related-languages-and-systems)
- [Category 13: Production / Regulated Domains](#category-13-production--regulated-domains)
- [Category 14: Developer Tooling / Future Features](#category-14-developer-tooling--future-features)
- [Existing Deep-Dive Documents](#existing-deep-dive-documents)
- [Research Queue](#research-queue)

---

## Legend

**Status key:**
- **[IMPL]** — Implemented and working in the current codebase
- **[PLANNED]** — In the roadmap, not yet built
- **[REF]** — Reference concept from research/external systems, not built into Sigil

---

## Category 1: Compiler / Lexer / Parser

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Lexer** | Converts raw Sigil source text into a stream of tokens; handles indentation, keywords, literals, and comments | ARCHITECTURE.md, STATUS.md, GRAMMAR.peg, COMPILER_DESIGN.md | [IMPL] `src/sigil/lexer/` |
| **Token** | Atomic unit produced by the lexer — e.g., `KEYWORD`, `INTEGER`, `INDENT`, `DEDENT`, `SYMBOL`, `NEWLINE` | ARCHITECTURE.md, GRAMMAR.peg, STATUS.md | [IMPL] `lexer/tokens.py` |
| **INDENT / DEDENT** | Synthetic tokens emitted by the lexer when indentation increases or decreases; enables Python-style significant whitespace | ARCHITECTURE.md, COMPILER_DESIGN.md, GRAMMAR.peg | [IMPL] |
| **Indentation Engine** | The lexer subsystem that tracks a stack of indent levels and emits INDENT/DEDENT tokens | COMPILER_DESIGN.md | [IMPL] |
| **PEG (Parsing Expression Grammar)** | Grammar formalism used by Sigil: unambiguous by construction via ordered choice (`/`), parsed in linear time via packrat memoization; formal foundation is Bryan Ford's POPL 2004 paper | ARCHITECTURE.md, FOUNDATIONS.md, COMPILER_DESIGN.md, GRAMMAR.peg | [IMPL] (hand-written recursive descent) |
| **Ordered Choice (`/`)** | PEG operator that tries alternatives in sequence and commits to the first match, eliminating ambiguity that plagues CFG-based parsers | COMPILER_DESIGN.md, GRAMMAR.peg | [IMPL] |
| **Packrat Memoization** | Technique for parsing PEGs in O(n) time by caching every rule result at every input position; trades O(n) memory for guaranteed linear time | COMPILER_DESIGN.md | [REF] (hand-written RD used; packrat is the theory) |
| **Recursive Descent Parser** | Hand-written parser strategy chosen for Sigil: each grammar rule is a Python function; selected for maximum control, debuggability, and educational value | ARCHITECTURE.md, STATUS.md | [IMPL] `src/sigil/parser/parser.py` |
| **Context-Sensitive Keywords** | Keywords like `when`, `then`, `and` are only keywords inside rule bodies; can serve as identifiers elsewhere | ARCHITECTURE.md, SYNTAX.md | [IMPL] |
| **CST (Concrete Syntax Tree)** | Intermediate representation produced by the parser before AST construction; retains all syntactic detail | ARCHITECTURE.md | [IMPL] (implicit; parser directly builds AST) |
| **AST (Abstract Syntax Tree)** | Core data structure of the Sigil compiler: tree of frozen dataclass nodes representing the program's structure after parsing | ARCHITECTURE.md, STATUS.md | [IMPL] `src/sigil/ast/nodes.py` (40+ node types) |
| **Surface AST** | AST form produced directly from parsing the constrained NL source syntax | ARCHITECTURE.md | [IMPL] |
| **Core AST (S-expression layer)** | The S-expression-equivalent internal AST layer used by the interpreter and tooling; the surface AST desugars to this | ARCHITECTURE.md, VISION.md, LISP_AND_FP.md | [IMPL] (interpreter works directly on surface AST nodes) |
| **Desugarer** | Pipeline stage that converts surface AST into core AST | ARCHITECTURE.md | [PLANNED] (Phase 3+) |
| **Pretty-Printer** | Component that converts an AST back to valid Sigil source text; used for formatting and roundtrip testing | ROADMAP.md | [PLANNED] |
| **Error Recovery** | Parser capability to produce a partial AST from malformed input, enabling multiple errors to be reported at once; critical for REPL and LLM-generated code | ARCHITECTURE.md, COMPILER_DESIGN.md | [PLANNED] (Phase 4) |
| **Error Node** | Placeholder AST node inserted when a parse error is encountered, allowing analysis to continue | COMPILER_DESIGN.md | [PLANNED] |
| **Synchronization Token** | Token used as a restart point during error recovery (e.g., `rule`, `define`, or NEWLINE at top indent) | COMPILER_DESIGN.md | [PLANNED] |
| **String Interpolation** | Embedding expressions inside string literals: `"Temperature is {temp} degrees"` | ARCHITECTURE.md, SYNTAX.md | [IMPL] |
| **Unit Suffix** | Token attached to a number literal specifying its unit: `100 degrees`, `50 percent`, `3 seconds` | GRAMMAR.peg, SYNTAX.md, TYPE_SYSTEM.md | [IMPL] (lexer + type checker) |
| **Space-Based Field Access** | Parser extension allowing `reading temperature` to mean `reading.temperature` (dot-less field access for NL readability) | STATUS.md, GRAMMAR.peg | [IMPL] (`SpaceFieldAccess` grammar rule) |
| **Scannerless Parsing** | PEG capability to handle both lexical and syntactic analysis in a single grammar; Sigil uses a separate lexer for indentation instead | COMPILER_DESIGN.md | [REF] |
| **GPeg** | 2021 research extension of PEG enabling incremental reparsing in logarithmic time, re-parsing only changed regions | COMPILER_DESIGN.md, BIBLIOGRAPHY.md | [REF] |
| **Tree-sitter** | GLR-based incremental parser used for editor integration (syntax highlighting, code navigation); separate from the compiler's PEG parser | COMPILER_DESIGN.md | [PLANNED] (Phase 4) |
| **Grammar-Constrained LLM Decoding** | Using a formal grammar (e.g., Sigil's PEG) directly as a constraint on LLM token generation, ensuring only syntactically valid Sigil is produced | EXISTING_DSLS.md, COMPILER_DESIGN.md, BIBLIOGRAPHY.md | [PLANNED] (Phase 4) |

---

## Category 2: AST Nodes / Grammar Rules

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Program** | Top-level grammar rule: optional module declaration + zero or more top-level declarations + EOF | GRAMMAR.peg | [IMPL] |
| **TopLevelDecl** | Any of: `ImportDecl`, `TypeDecl`, `ConstDecl`, `RuleDecl`, `ComputeDecl`, `NeuralDecl`, `MainDecl` | GRAMMAR.peg | [IMPL] |
| **ModuleDecl** | `module name.path` — declares the module name (optional; inferred from filename if absent) | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **ImportDecl** | `import python/rust/sigil ...` — bring external symbols into scope | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **TypeDecl** | `type Name is ...` — declares a named type alias, record, enum, constrained, or unit type | GRAMMAR.peg, SYNTAX.md, TYPE_SYSTEM.md | [IMPL] |
| **ConstDecl** | `define NAME as expr` — binds a name to a constant value | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **RuleDecl** | `rule name [with priority N]:` — the primary Sigil construct; contains when/then/explain/trace/given clauses | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **ComputeDecl** | `compute name from params returns Type:` — defines a pure function | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **NeuralDecl** | `neural name from param: Type:` — declares a neural computation with model, returns, threshold, fallback | GRAMMAR.peg, SYNTAX.md | [IMPL] (stub; real model loading Phase 3) |
| **MainDecl** | `main:` — program entry point block | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **RuleBody** | The full contents of a rule: meta fields, given clauses, when clause, and/or clauses, then clause, explain clause, trace clause, using clause | GRAMMAR.peg | [IMPL] |
| **GivenClause** | `given X from expr` or `given X as expr` — binds a name within a rule or compute body | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **WhenClause** | `when Condition` — the primary condition that must be true for a rule to fire | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **AndOrClause** | `and/or [not] Condition` — additional conditions combined with the when clause | GRAMMAR.peg | [IMPL] |
| **TemporalClause** | `within N unit` — temporal constraint expressing a time window for a rule to apply | GRAMMAR.peg, STATUS.md | [IMPL] (parsed + recorded in trace; full temporal evaluation Phase 2 Sprint 3) |
| **ThenClause** | `then Action` or `then: block` — specifies what happens when a rule fires | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **ExplainClause** | `explain "..."` — human-readable explanation string emitted in the trace when the rule fires | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **TraceClause** | `trace: ...` block with fields like `category`, `retention`, `format` — configures trace metadata for a rule | GRAMMAR.peg, SYNTAX.md | [IMPL] (parsed; full trace annotation Phase 3+) |
| **UsingClause** | `using rust [path]` — hint to delegate this rule's evaluation to the Rust core | GRAMMAR.peg, INTEROP.md | [PLANNED] (Phase 3) |
| **MetaField** | `version`, `author`, or `tags` metadata attached to a rule declaration | GRAMMAR.peg, SYNTAX.md | [IMPL] (parsed) |
| **NeuralField** | Subfields inside a neural declaration: `model`, `using python`, `returns`, `confidence_threshold`, `threshold`, `candidates`, `fallback to` | GRAMMAR.peg | [IMPL] (parsed; model loading Phase 3) |
| **SetAction** | `x is value` inside a `then` clause — sets a fact variable | GRAMMAR.peg, STATUS.md | [IMPL] |
| **SimpleAction** | `trigger alert with severity :critical` style action — calls a named action with optional params | GRAMMAR.peg | [IMPL] |
| **MatchExpr** | `match expr: arm -> expr ...` — pattern matching expression | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **MatchArm** | One `Pattern -> Expression` branch inside a match expression | GRAMMAR.peg | [IMPL] |
| **PipelineExpr** | Expression using the `|>` operator to chain pipeline operations | GRAMMAR.peg, SYNTAX.md | [IMPL] |
| **PipeOp** | One operation in a pipeline: `filter where`, `sort by`, `take first/last`, `map to`, or identifier | GRAMMAR.peg | [IMPL] |
| **QuantifiedCond** | `any/all/none X in collection has Condition` — universal/existential quantification over collections | GRAMMAR.peg, SYNTAX.md, SEMANTICS.md | [IMPL] |
| **AssignedCond** | `expr is [not] assigned` — checks whether a variable is bound (non-null) | GRAMMAR.peg, STATUS.md | [IMPL] |
| **ComparisonCond** | `expr CompOp expr` — numeric/equality comparison using `exceeds`, `is below`, `is between`, `is`, `equals`, etc. | GRAMMAR.peg | [IMPL] |
| **MembershipCond** | `x in collection`, `collection contains x`, `collection is empty`, `collection has count n` | GRAMMAR.peg | [IMPL] |
| **StringCond** | `text starts with`, `ends with`, `contains`, `matches pattern` | GRAMMAR.peg | [IMPL] |
| **BooleanCond** | `expr is true / false` | GRAMMAR.peg | [IMPL] |
| **BecomesStatement** | `x becomes expr` — mutable assignment within a compute/main block | GRAMMAR.peg, STATUS.md | [IMPL] |
| **EvaluateStatement** | `evaluate all rules / ruleName with expr` — triggers rule evaluation from within a block | GRAMMAR.peg | [IMPL] |
| **QueryStatement** | `query ruleName [with expr]` — invokes the backward chaining engine | GRAMMAR.peg, STATUS.md | [IMPL] |
| **FieldAccess** | `.fieldName` postfix operator — dotted field access | GRAMMAR.peg | [IMPL] |
| **FuncCall** | `expr(args)` — function call syntax | GRAMMAR.peg | [IMPL] |
| **IndexAccess** | `expr[expr]` — list/record indexing | GRAMMAR.peg | [IMPL] |
| **SymbolLiteral** | `:identifier` — an interned atom/keyword value | GRAMMAR.peg, SYNTAX.md, TYPE_SYSTEM.md | [IMPL] |
| **RecordLiteral** | `{key: value, ...}` — anonymous record construction | GRAMMAR.peg | [IMPL] |
| **ListLiteral** | `[expr, ...]` — list literal | GRAMMAR.peg | [IMPL] |
| **EmptyExpr** | `empty list` or `empty` — empty collection literal | GRAMMAR.peg, STATUS.md | [IMPL] |
| **ExportDecl** | `export name` — marks a declaration as part of a module's public API | STATUS.md, SYNTAX.md | [IMPL] |

---

## Category 3: Runtime / Interpreter / Execution Model

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Tree-Walking Interpreter** | Evaluation strategy that directly walks the AST and evaluates each node; Sigil's Phase 1-2 implementation in Python | ARCHITECTURE.md, ROADMAP.md, COMPILER_DESIGN.md | [IMPL] `src/sigil/interpreter/evaluator.py` |
| **Environment** | Immutable mapping from identifiers to values; new bindings create a new extended environment; implements lexical scoping | SEMANTICS.md, ARCHITECTURE.md | [IMPL] `interpreter/environment.py` |
| **Value** | Union type of all runtime values in Sigil: Number, Text, Boolean, Symbol, None, List, Record, Closure, Variant | SEMANTICS.md | [IMPL] `interpreter/values.py` |
| **Symbol (runtime)** | Interned string atom (`:active`, `:critical`); a distinct value type from Text; compared by identity | TYPE_SYSTEM.md, SEMANTICS.md | [IMPL] |
| **Record (runtime)** | Key-value collection; structural typing; field access via dot or space syntax | SEMANTICS.md, TYPE_SYSTEM.md | [IMPL] |
| **Closure** | A function value capturing its definition-time environment; enables higher-order functions and lambdas | STATUS.md, SYNTAX.md | [IMPL] |
| **Variant** | A tagged union value (sum type instance), e.g., `approved with rate: 5.5` | STATUS.md, TYPE_SYSTEM.md | [IMPL] |
| **_UNBOUND** | Sentinel value representing an unset/missing record field; unbound variable comparisons return False, `is not` returns True | STATUS.md (memory) | [IMPL] |
| **Lexical Scoping** | Name resolution uses the environment at the point of definition, not call; Sigil's closures capture their definition environment | ARCHITECTURE.md, SEMANTICS.md | [IMPL] |
| **Forward Chaining** | Data-driven rule evaluation: start from known facts, apply matching rules to derive new facts, repeat until fixed point | ARCHITECTURE.md, SEMANTICS.md, ROADMAP.md | [IMPL] (max 100 iterations, `fired_rules` set) |
| **Fixed Point** | The stable state reached by forward chaining when no new facts can be derived; guarantees termination | SEMANTICS.md | [IMPL] |
| **Fired Rules Set** | Set of rule names already fired in the current evaluation pass; prevents rules from re-firing with the same facts | STATUS.md (memory) | [IMPL] |
| **Backward Chaining** | Goal-driven rule evaluation: given a goal, find rules whose conclusion matches and recursively prove their conditions | ARCHITECTURE.md, ROADMAP.md, STATUS.md | [IMPL] `interpreter/backward.py` (Phase 2 Sprint 3) |
| **ProofNode** | Dataclass representing one node in a backward-chaining proof tree, recording which rule was applied and its sub-goals | STATUS.md | [IMPL] |
| **Proof Tree** | The full tree of ProofNodes produced by backward chaining, recorded in ProgramTrace for auditability | STATUS.md | [IMPL] |
| **BackwardChainer** | Class implementing recursive goal-driven evaluation with cycle detection (max depth 50) | STATUS.md | [IMPL] `interpreter/backward.py` |
| **Short-Circuit Evaluation** | AND conditions stop evaluating as soon as one is false; OR conditions stop as soon as one is true; skipped conditions are recorded in trace | SEMANTICS.md | [IMPL] |
| **Conflict Resolution** | When multiple rules match simultaneously, the rule with highest priority wins; ties broken by specificity (more conditions), then declaration order | SEMANTICS.md, ARCHITECTURE.md | [IMPL] |
| **Rule Priority** | Integer value on a rule declaration (`with priority N`) controlling which rule wins conflicts | SYNTAX.md, SEMANTICS.md | [IMPL] |
| **Fact Space** | The shared environment of named values (facts) against which rules are evaluated; rules can add new facts via SetAction | ARCHITECTURE.md, SEMANTICS.md | [IMPL] |
| **Rule Index** | A fast lookup structure mapping condition variables to candidate rules; enables efficient matching without scanning all rules | ARCHITECTURE.md | [IMPL] (Rete-lite in Rust core) |
| **Rete Algorithm** | Network-based pattern matching algorithm for efficiently evaluating large rule sets; Sigil implements Rete-lite in `sigil_core/src/matcher.rs` with alpha nodes exposed via PyO3 `ReteNetwork` class | ARCHITECTURE.md, INTEROP.md | [IMPL] (Rust core, Phase 3) |
| **Confidence Value** | A Number between 0.0 and 1.0 attached to the result of a neural computation; checked against threshold to decide model result vs fallback | TYPE_SYSTEM.md, SEMANTICS.md, SYNTAX.md | [IMPL] |
| **Fallback** | Mandatory value declared in a neural block, returned when the model's confidence falls below the threshold; guarantees null-safety | SYNTAX.md, SEMANTICS.md, TYPE_SYSTEM.md | [IMPL] |
| **Neural Stubs** | Current Phase 1-2 implementation of neural declarations: if variable already bound, keeps value; otherwise returns the declared fallback | STATUS.md | [IMPL] |
| **Mutable Binding** | Opt-in mutability via the `mutable` keyword; all other bindings are immutable | SEMANTICS.md, SYNTAX.md | [IMPL] (in grammar; `becomes` in evaluator) |
| **Arena Allocation** | Memory allocation strategy planned for the Rust core: allocate many objects in a contiguous arena, free the whole arena at once | SEMANTICS.md | [PLANNED] (Rust core) |
| **Bytecode VM** | Stack-based virtual machine that executes compiled bytecode; 10-100x faster than tree-walking; Phase 5 target | ARCHITECTURE.md, ROADMAP.md, COMPILER_DESIGN.md | [PLANNED] (Phase 5) |
| **Stack-Based VM** | VM architecture where operands are pushed/popped from a stack; simpler to implement than register-based; chosen for Sigil's future VM | COMPILER_DESIGN.md | [PLANNED] |
| **Register-Based VM** | VM architecture using virtual registers; fewer instructions per operation; LuaJIT's approach | COMPILER_DESIGN.md | [REF] |
| **Constant Folding** | Optimization pass: evaluate constant expressions at compile time rather than runtime | ARCHITECTURE.md, ROADMAP.md | [PLANNED] (Phase 2 optimization passes) |
| **Dead Rule Elimination** | Optimization pass: remove rules whose conditions can never be true | ARCHITECTURE.md, ROADMAP.md | [PLANNED] |
| **REPL (Read-Eval-Print Loop)** | Interactive Sigil shell supporting all language features plus `:env`, `:rules`, `:funcs`, `:types`, `:trace`, `:reset`, `:help` commands | ARCHITECTURE.md, ROADMAP.md, STATUS.md | [IMPL] `interpreter/repl.py` |
| **Referential Transparency** | Property of pure compute blocks: they can be replaced by their result without changing program behavior; enables caching and memoization | LISP_AND_FP.md, SEMANTICS.md | [IMPL] (by design) |
| **Demand-Driven Evaluation** | Lazy evaluation strategy: compute only what is needed when it is needed; Haskell-inspired; future extension for backward chaining | LISP_AND_FP.md, FOUNDATIONS.md | [PLANNED] (future) |

---

## Category 4: Trace System

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Trace** | The fundamental output of every Sigil rule evaluation: an ordered record of every condition evaluated, its result, and bindings at that point | VISION.md, ARCHITECTURE.md, SEMANTICS.md, SYNTAX.md | [IMPL] `interpreter/trace.py` |
| **ProgramTrace** | Top-level trace object for a full program evaluation; contains all RuleTraces and ConditionTraces | STATUS.md | [IMPL] |
| **RuleTrace** | Trace record for one rule evaluation: which rule, which conditions, whether it fired, how long it took | STATUS.md | [IMPL] |
| **ConditionTrace** | Trace record for one condition evaluation: the expression, its Boolean result, variable bindings at that point | STATUS.md, SEMANTICS.md | [IMPL] |
| **TraceEntry** | One entry in a trace: expression, result, bindings, duration, and source (`:symbolic` or `:neural`) | SEMANTICS.md | [IMPL] |
| **TraceTimer** | Utility tracking wall-clock execution time for trace entries | STATUS.md | [IMPL] |
| **Explanation** | Human-readable string (from `explain` clause) included in the trace when a rule fires; may include interpolated variable values | VISION.md, SYNTAX.md, TYPE_SYSTEM.md | [IMPL] |
| **Audit Trail** | The trace used as a legal/compliance record of every decision; the primary output in regulated domains | VISION.md, REAL_WORLD_BRIDGE.md | [IMPL] (trace is always on) |
| **Trace Annotation** | Metadata attached to a rule's trace output: `category`, `retention`, `format`, `compliance` | SYNTAX.md | [IMPL] (parsed) |
| **Neural vs Symbolic Trace Distinction** | Trace entries are tagged as `:neural` or `:symbolic` so auditors know whether a step was deterministic. `NeuralTrace` dataclass in `ProgramTrace.neural_traces` rendered separately in `format_trace()` | SEMANTICS.md, ARCHITECTURE.md | [IMPL] (Phase 3) |
| **`sigil.trace` stdlib** | Standard library module for querying and formatting traces: `to_json`, `fired_rules`, `rule_count`, `duration_ms` | STATUS.md | [IMPL] |
| **Trace Retention** | Configuration on a trace clause specifying how long audit records should be kept (e.g., `7 years`) | SYNTAX.md | [IMPL] (parsed) |
| **Trace Format** | Configuration on trace output: `:detailed`, `:summary`, table, JSON | SYNTAX.md | [PLANNED] (Phase 4) |

---

## Category 5: Type System

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Gradual Type System** | Types are optional for prototyping but required at module boundaries and neural declarations; inference fills gaps in annotated code | TYPE_SYSTEM.md, ARCHITECTURE.md | [IMPL] `src/sigil/types/checker.py` |
| **Number** | Unified numeric base type (integer or float, context-determined) | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] |
| **Text** | UTF-8 string base type | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] |
| **Boolean** | `true` / `false` base type | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] |
| **Symbol (type)** | Interned atom type (`:keyword` style); compared by identity, not string equality | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] |
| **Unit Type** | A Number annotated with a physical unit: `Number with unit degrees`; enables dimensional analysis | TYPE_SYSTEM.md, SYNTAX.md | [IMPL] (unit awareness in type checker Phase 2 Sprint 3) |
| **Dimensional Analysis** | Checking that values with units are only compared with compatible units; catching `temperature > 30 seconds` as an error | TYPE_SYSTEM.md | [IMPL] (warnings in type checker) |
| **List[T]** | Homogeneous list type: `list of Number` | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] |
| **Record Type** | Structural product type: named field collection; `type Person is record: name: Text ...` | TYPE_SYSTEM.md, SYNTAX.md | [IMPL] |
| **Option[T]** | Explicit nullable type: `Option[Number]` — either a Number or none | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] |
| **Sum Type / Enum Type** | Tagged union: `type Decision is one of: approved ... / denied ... / review ...` | TYPE_SYSTEM.md, SYNTAX.md, LISP_AND_FP.md | [IMPL] |
| **Constrained Type** | Type with a runtime-checked value constraint: `type Percentage is Number between 0 and 100` | TYPE_SYSTEM.md, SYNTAX.md | [IMPL] (type checker checks constraints at boundaries) |
| **Structural Subtyping** | A record with more fields is a subtype of one with fewer; no explicit inheritance declaration needed | TYPE_SYSTEM.md | [IMPL] |
| **Confidence (domain type)** | `Number between 0.0 and 1.0`; the return type of neural operations; always has an associated score | TYPE_SYSTEM.md, ARCHITECTURE.md, GRAMMAR.peg | [IMPL] (stub) |
| **Trace (domain type)** | First-class type representing an execution trace record | TYPE_SYSTEM.md | [IMPL] |
| **Rule (domain type)** | First-class rule value type | TYPE_SYSTEM.md, ARCHITECTURE.md | [IMPL] |
| **Generic Type** | Parameterized type: `type Result[T] is one of: success with value: T ...` | TYPE_SYSTEM.md, GRAMMAR.peg | [IMPL] (grammar; full parametric inference Phase 3+) |
| **Type Inference** | Automatically deducing types from context: `temperature > 100` infers `temperature` is Number | TYPE_SYSTEM.md, SEMANTICS.md | [IMPL] (local inference in type checker) |
| **Hindley-Milner Inference** | Classical algorithm for type inference in functional languages; inspires Sigil's local inference | LISP_AND_FP.md | [REF] |
| **Symbol Table** | Data structure built during Phase 1 of type checking: maps all declared names to their types | STATUS.md | [IMPL] |
| **Two-Phase Type Checker** | Type checking proceeds in two passes: (1) collect all declarations and build symbol table; (2) walk bodies and check for errors | STATUS.md | [IMPL] `types/checker.py` |
| **Match Exhaustiveness** | Type checker warning when a match expression does not cover all variants of a sum type | STATUS.md | [IMPL] (Check #6) |
| **Pipeline Validation** | Type checker verifying that pipeline operations produce and consume compatible types | STATUS.md | [IMPL] (Check #7) |
| **Return Type Consistency** | Type checker verifying all return statements in a compute block return the declared type | STATUS.md | [IMPL] (Check #9) |
| **Unit Awareness** | Type checker warning when values with different unit suffixes are compared | STATUS.md | [IMPL] (Check #11) |
| **Neural/Symbolic Boundary Type** | The type-check point ensuring neural return types are explicitly declared and compatible with their usage in symbolic rules | TYPE_SYSTEM.md, ARCHITECTURE.md | [IMPL] (stub) |
| **Algebraic Data Types (ADTs)** | Sum types + product types; the core of Sigil's type system; models disjunctive outcomes and conjunctive data structures | LISP_AND_FP.md, TYPE_SYSTEM.md | [IMPL] |
| **Dependent Types** | Types that depend on values (e.g., `Vector n`); used in Lean 4 but deliberately NOT in Sigil (too complex for domain experts) | LISP_AND_FP.md, FOUNDATIONS.md | [REF] |

---

## Category 6: Neuro-Symbolic AI

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Neuro-Symbolic AI** | AI paradigm combining neural networks (for perception/learning) with symbolic systems (for reasoning/guarantees); the field Sigil is designed for | VISION.md, FOUNDATIONS.md, NS_LANDSCAPE.md | [REF] (Sigil is an implementation artifact) |
| **Kautz Taxonomy** | Henry Kautz's 2020 AAAI framework classifying six types of neuro-symbolic integration by coupling tightness; Sigil operates at Type 2-3 | FOUNDATIONS.md, NS_LANDSCAPE.md | [REF] |
| **Type 2: Symbolic[Neural]** | Integration pattern where a symbolic system invokes neural components as subroutines; the orchestrator is symbolic; most commercially successful pattern | FOUNDATIONS.md, NS_LANDSCAPE.md | [REF] (Sigil's architecture) |
| **Type 3: Neural|Symbolic** | Integration pattern where a neural network generates symbolic programs; e.g., LLM → Sigil source code | FOUNDATIONS.md, NS_LANDSCAPE.md | [PLANNED] (Phase 4 NL-to-Sigil generator) |
| **Type 5: Neural_{Symbolic}** | Tight coupling: symbolic logic tensorized as differentiable constraints; enables end-to-end gradient training through reasoning (Scallop, DeepProbLog) | FOUNDATIONS.md, NS_LANDSCAPE.md | [REF] (future research direction) |
| **DARPA Three Waves of AI** | John Launchbury's framework: Wave 1 (handcrafted knowledge), Wave 2 (statistical learning), Wave 3 (contextual adaptation = hybrid); Sigil is Wave 3 | FOUNDATIONS.md, NS_LANDSCAPE.md | [REF] |
| **Neural Bridge** | Sigil's explicit boundary layer between neural perception and symbolic execution: `neural` declarations wrap ML models with Sigil guarantees. Implemented via pluggable `ModelBackend` protocol + `ModelRegistry` | ARCHITECTURE.md, VISION.md | [IMPL] (Phase 3) `src/sigil/neural/` |
| **Confidence Threshold** | Minimum confidence a neural model must produce; below this the fallback value is used instead. Evaluated in `_call_neural()` in the interpreter | SYNTAX.md, SEMANTICS.md, TYPE_SYSTEM.md | [IMPL] |
| **Neural Backend** | The underlying ML framework invoked by a neural declaration. `ModelBackend` protocol with `load()` and `predict()` methods. HuggingFace backend built-in (`hf:` prefix) | ARCHITECTURE.md, INTEROP.md | [IMPL] (Phase 3) |
| **Model Registry** | Singleton `ModelRegistry` mapping model ID prefixes to `ModelBackend` instances. Lazy-loads models on first predict, caches loaded models. Built-in `hf:` prefix for HuggingFace | ARCHITECTURE.md, ROADMAP.md | [IMPL] (Phase 3) `src/sigil/neural/registry.py` |
| **Neural TTL Cache** | Time-to-live cache for neural results to avoid redundant model inference calls | ARCHITECTURE.md | [PLANNED] (Phase 3) |
| **Confidence Propagation** | The (deliberate) non-propagation of confidence through symbolic rules; confidence is only accessible via explicit field access, not implicitly | SEMANTICS.md | [IMPL] (by design) |
| **NL-to-Sigil Generator** | Phase 4 feature: LLM-powered translation of natural language rule descriptions into valid Sigil programs, with validation pipeline | ROADMAP.md | [PLANNED] (Phase 4) |
| **Neural Perception** | The role of LLMs/neural networks in a Sigil system: extract structured facts from unstructured input (text, images, sensor data) | VISION.md, REAL_WORLD_BRIDGE.md | [PLANNED] (Phase 3) |
| **Symbolic Reasoning** | The role of Sigil's rule engine: apply deterministic rules to structured facts to produce decisions with full traces | VISION.md, ARCHITECTURE.md | [IMPL] |
| **Confidence-to-Predicate Interface** | The core technical challenge in neuro-symbolic systems: converting a probabilistic model output (float 0-1) into a discrete symbolic fact; Sigil's `neural` keyword with `confidence_threshold` is the solution | REAL_WORLD_BRIDGE.md | [IMPL] |
| **ModelResult** | Frozen dataclass returned by `ModelBackend.predict()`: contains `value` (Sigil Value), `confidence` (float), `model_id`, `latency_ms` | neural/backend.py | [IMPL] (Phase 3) |
| **ModelBackend Protocol** | Python `Protocol` class defining the pluggable neural backend interface: `load(model_id)` and `predict(model_id, input_data) -> ModelResult` | neural/backend.py | [IMPL] (Phase 3) |
| **HuggingFace Backend** | Built-in `ModelBackend` implementation using `transformers.pipeline()` for inference. Registered with `hf:` prefix. Graceful degradation if transformers not installed | neural/huggingface.py | [IMPL] (Phase 3) |
| **NeuralTrace** | Dataclass recording a neural inference: function name, model ID, confidence, threshold, whether fallback was used, latency, and optional error message. Added to `ProgramTrace.neural_traces` | trace.py | [IMPL] (Phase 3) |
| **Neural Fallback Cascade** | When a neural model fails (error, low confidence, or no backend): (1) check confidence vs threshold, (2) if below or error, return declared fallback value, (3) always record NeuralTrace | evaluator.py | [IMPL] (Phase 3) |
| **AlphaGeometry** | DeepMind 2024 system (published in Nature) solving IMO geometry at near-gold-medalist level using neural construction suggester + symbolic deduction engine; primary validation of Sigil's Type 2 architecture | FOUNDATIONS.md, NS_LANDSCAPE.md, BIBLIOGRAPHY.md | [REF] |
| **AlphaProof** | DeepMind 2024 system achieving IMO silver medal using Gemini + AlphaZero + Lean 4 formal verification; proves neural→formal language→symbolic verification pipeline works at highest level | FOUNDATIONS.md, NS_LANDSCAPE.md, BIBLIOGRAPHY.md | [REF] |
| **Scallop** | Purpose-built neuro-symbolic DSL (PLDI 2023, U. Penn) based on Datalog + provenance semirings; enables differentiable symbolic reasoning; the closest existing work to Sigil's vision | FOUNDATIONS.md, NS_LANDSCAPE.md, EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **DeepProbLog** | NeurIPS 2018 system extending ProbLog with neural predicates; pioneered differentiable logic programming; predecessor to Scallop | NS_LANDSCAPE.md, EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **Logic Tensor Networks (LTN)** | System tensorizing first-order logic axioms as differentiable loss functions for end-to-end training | NS_LANDSCAPE.md, REAL_WORLD_BRIDGE.md | [REF] |
| **DomiKnowS** | IBM/U. Penn framework encoding concepts, relations, and constraints as a conceptual graph; finding: "authoring NeSy programs remains challenging" — key motivation for Sigil's NL syntax | NS_LANDSCAPE.md, EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **AgenticDomiKnowS (ADS)** | 2025-2026 extension of DomiKnowS with LLM-powered NL→NeSy program generation; validates Sigil's thesis | NS_LANDSCAPE.md, EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **DreamCoder** | PLDI 2021 system that learns to solve problems by writing programs and building DSLs incrementally via a wake-sleep algorithm | NS_LANDSCAPE.md, EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **SymCode** | 2025 system reframing math as verifiable code generation using SymPy; adds agentic self-debugging loops | NS_LANDSCAPE.md, BIBLIOGRAPHY.md | [REF] |
| **Chain-of-Thought Prompting** | Wei et al. 2022 NeurIPS technique: forcing LLMs to externalize intermediate symbolic steps dramatically improves reasoning accuracy; validates the neuro-symbolic thesis | FOUNDATIONS.md, NS_LANDSCAPE.md, BIBLIOGRAPHY.md | [REF] |
| **System 1 / System 2 Thinking** | Kahneman's dual-process theory applied to AlphaGeometry: neural = fast intuitive System 1; symbolic = slow deliberate System 2; Sigil's architecture embodies this | NS_LANDSCAPE.md | [REF] |
| **Provenance Semiring** | Mathematical structure (Scallop) enabling different reasoning modes over symbolic computations: probabilistic, top-k, differentiable | NS_LANDSCAPE.md, EXISTING_DSLS.md | [REF] |
| **Answer Set Programming (ASP)** | Stable-model semantics for logic programming; handles non-monotonic reasoning, defaults, exceptions; tools: Clingo, DLV; future Sigil extension | EXISTING_DSLS.md | [REF] |
| **Expert System** | Wave 1 AI: domain knowledge encoded as explicit rules evaluated by a rule engine; systems like MYCIN, DENDRAL, R1/XCON; Sigil's rule engine is a modern, LLM-augmented expert system | NS_LANDSCAPE.md, REAL_WORLD_BRIDGE.md | [REF] |
| **Two-Language Problem** | Scientific computing pain point: prototype in Python (slow), rewrite in C++ (painful); Julia solves this; Sigil addresses it differently via Python+Rust hybrid | JULIA_AND_NS.md | [REF] |

---

## Category 7: Rule Engine

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Rule Engine** | The core symbolic execution component of Sigil; evaluates rule conditions against facts, resolves conflicts, executes actions, and records traces | ARCHITECTURE.md | [IMPL] (within evaluator.py) |
| **Rule** | The primary Sigil construct: a named, prioritized conditional declaration (`when ... then ...`) | VISION.md, SYNTAX.md | [IMPL] |
| **Rule Firing** | A rule fires when all its conditions evaluate to true; its action is then executed and a trace entry is produced | SEMANTICS.md | [IMPL] |
| **Rule Composition** | Multiple rules sharing the fact space, where one rule's action (setting a fact) enables another rule's condition | ARCHITECTURE.md, SYNTAX.md | [IMPL] |
| **Rule Metadata** | Fields on a rule declaration: `version`, `author`, `tags`, `priority` | SYNTAX.md, GRAMMAR.peg | [IMPL] (parsed) |
| **Rule Combinator** | Higher-order pattern for composing rules from smaller rules; part of `sigil.rules` stdlib | ARCHITECTURE.md, ROADMAP.md | [PLANNED] |
| **Temporal Rule** | A rule with a `within N unit` clause specifying a time constraint on when conditions must be satisfied | SYNTAX.md, ROADMAP.md, STATUS.md | [IMPL] (parsed + trace; full evaluation Phase 2 Sprint 3+) |
| **Quantifier** | `any`, `all`, `none` — universal/existential quantification over a collection in a rule condition | SYNTAX.md, SEMANTICS.md, GRAMMAR.peg | [IMPL] |
| **Condition Evaluator** | Interpreter component evaluating the 12+ condition types with short-circuit AND/OR | STATUS.md | [IMPL] |
| **Action Executor** | Interpreter component executing SetAction, SimpleAction, and block actions; can assert new facts | STATUS.md, SEMANTICS.md | [IMPL] |
| **Fact Assertion** | An action that adds a new named value to the fact space, potentially triggering other rules (forward chaining) | SEMANTICS.md, ARCHITECTURE.md | [IMPL] |
| **Termination Guarantee** | Forward chaining terminates when: no new facts produced, max iterations (100) reached, or cycle detected | SEMANTICS.md | [IMPL] |
| **Conflict Detection** | Future formal verification feature: detecting when two rules produce contradictory conclusions | ROADMAP.md | [PLANNED] (Phase 5) |
| **Rule Completeness** | Future verification: checking that all possible input cases are covered by at least one rule | ROADMAP.md, ARCHITECTURE.md | [PLANNED] (Phase 5) |
| **Termination Analysis** | Formal verification that rule chains always reach a fixed point and halt | ROADMAP.md | [PLANNED] (Phase 5) |
| **SMT Solver (Z3)** | Satisfiability Modulo Theories solver; planned integration for formal rule verification | ROADMAP.md | [PLANNED] (Phase 5) |
| **Constraint Solver** | Rust-implemented constraint satisfaction engine (`ConstraintSolver` PyO3 class). Supports equals, not-equals, greater/less than, between, one-of constraints. Returns violations list or boolean satisfaction check | ARCHITECTURE.md, INTEROP.md | [IMPL] (Phase 3) `sigil_core/src/solver.rs` |
| **Pattern Matcher** | Rete-lite implementation (`ReteNetwork` PyO3 class). Compiles rules with conditions, matches against fact dictionaries, returns matches sorted by priority | ARCHITECTURE.md, INTEROP.md | [IMPL] (Phase 3) `sigil_core/src/matcher.rs` |
| **Drools** | Commercial Java rule engine; represents the "existing symbolic world" Sigil bridges from | REAL_WORLD_BRIDGE.md | [REF] |
| **OPA (Open Policy Agent)** | Open-source policy engine using Rego language; another existing symbolic system Sigil compares to | REAL_WORLD_BRIDGE.md | [REF] |

---

## Category 8: Language Design / Syntax Philosophy

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Constrained Natural Language** | Sigil's surface syntax philosophy: reads like English but parses as a PEG; not free-form NL, not code-like syntax | VISION.md, SYNTAX.md, FOUNDATIONS.md | [IMPL] (by design) |
| **AI-Native Grammar** | Grammar designed from day one for reliable LLM generation: flat structure, ~30 keywords, regular patterns, explicit types at boundaries | VISION.md, FOUNDATIONS.md, EXISTING_DSLS.md | [IMPL] (by design) |
| **Two-Layer Principle** | Sigil has a surface layer (constrained NL for humans/LLMs) and a core layer (S-expression equivalent for the interpreter/tooling); both are valid Sigil | VISION.md, ARCHITECTURE.md | [IMPL] |
| **Determinism as Default** | Every Sigil expression produces the same output for the same input unless explicitly marked `neural`; the `neural` keyword is the only source of non-determinism | VISION.md, SEMANTICS.md | [IMPL] |
| **Determinism Guarantee** | Formal theorem: for any Sigil program with no `neural` declarations, all runs on the same input produce identical results and traces | SEMANTICS.md | [IMPL] (by design) |
| **Flat Structure** | Rules are top-level declarations; minimal nesting; maximum 2 levels of indentation inside a rule body; critical for LLM generation predictability | VISION.md, EXISTING_DSLS.md | [IMPL] |
| **Significant Whitespace** | Indentation (spaces only, no tabs) defines block structure; Python-style | ARCHITECTURE.md, SYNTAX.md, COMPILER_DESIGN.md | [IMPL] |
| **Semantic Transparency** | Keywords carry their natural English meaning: `exceeds` means `>`, `is between` means `<=x<=`, `contains` means membership | EXISTING_DSLS.md | [IMPL] |
| **KV-Cache Friendliness** | Grammar property identified by MoonBit: flat, explicit structure is more efficient for LLM KV-cache, reducing token generation cost | EXISTING_DSLS.md | [REF] |
| **`neural` Keyword** | The only syntactic marker for non-determinism in Sigil; visually distinct, requires confidence threshold and fallback | VISION.md, SYNTAX.md | [IMPL] |
| **`explain` Clause** | NL description attached to a rule; interpolated into traces; enables human-readable audit records | SYNTAX.md, VISION.md | [IMPL] |
| **Pipeline Operator (`|>`)** | Functional composition operator: passes left operand as input to right operand; enables readable data transformation chains | SYNTAX.md, STATUS.md | [IMPL] |
| **`given ... as / from`** | Let-binding form: `given x as expr` evaluates expr; `given x from expr` uses existing env value if bound | SYNTAX.md, STATUS.md (memory) | [IMPL] |
| **`becomes`** | Mutable re-assignment statement for use inside compute/main blocks | SYNTAX.md, STATUS.md | [IMPL] |
| **`query`** | Statement invoking the backward chaining engine to prove a goal | SYNTAX.md, STATUS.md | [IMPL] |
| **`private` modifier** | Marks a declaration as module-private, not exported | SYNTAX.md, GRAMMAR.peg | [IMPL] |
| **`mutable` keyword** | Opt-in mutability for a binding | SEMANTICS.md, GRAMMAR.peg | [IMPL] |
| **`using rust`** | Directive in a rule or compute block to delegate evaluation to the Rust core | INTEROP.md, GRAMMAR.peg | [PLANNED] (Phase 3) |
| **Doc Comment** | Triple-dash `---` comment attached to the next declaration; supports Markdown | SYNTAX.md | [IMPL] (lexer) |
| **Multi-Line Comment** | `{- ... -}` block comments; nesting supported | SYNTAX.md, GRAMMAR.peg | [IMPL] |
| **SimPy** | ICSE 2024 study showing grammar design directly impacts LLM code generation efficiency; 13.5% token reduction with simplified Python variant | EXISTING_DSLS.md, FOUNDATIONS.md, BIBLIOGRAPHY.md | [REF] |
| **MoonBit** | 2024 language designed from inception for AI-friendliness: flat structure, mandatory types, KV-cache optimization; key reference for Sigil's grammar design | EXISTING_DSLS.md, FOUNDATIONS.md, BIBLIOGRAPHY.md | [REF] |
| **Inform 7** | 2006 language by Graham Nelson proving constrained NL can be a real programming language within a domain (interactive fiction); Sigil's closest historical analog | VISION.md, FOUNDATIONS.md, EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **AppleScript** | 1993 English-like Apple automation language; its failure mode (rigid syntax that looks like NL but isn't) is a cautionary tale for Sigil | FOUNDATIONS.md, EXISTING_DSLS.md | [REF] |
| **LMQL (LLM Query Language)** | Language for constrained LLM generation via grammar-constrained decoding; analogy: LMQL constrains LLM output, Sigil's PEG can constrain Sigil-generating LLMs | EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **SudoLang** | Pseudocode language for LLM interaction combining NL with programming constructs | EXISTING_DSLS.md, BIBLIOGRAPHY.md | [REF] |
| **DSPy** | LLM pipeline optimization framework; represents the "LLM-centric" approach Sigil deliberately contrasts with | EXISTING_DSLS.md | [REF] |
| **LangChain** | LLM orchestration framework; like DSPy, represents an approach where LLMs make decisions; Sigil's approach is the opposite | EXISTING_DSLS.md | [REF] |

---

## Category 9: Module System / Standard Library

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Module System** | Sigil's mechanism for organizing code across files: module declarations, imports, exports, caching, circular dependency detection | SYNTAX.md, STATUS.md, ROADMAP.md | [IMPL] `src/sigil/modules/` |
| **Module Resolver** | Component resolving module paths to file system locations: handles stdlib, python, relative, and project-relative paths | STATUS.md | [IMPL] `modules/resolver.py` |
| **Module Loader** | Component loading, parsing, evaluating, and caching modules; detects circular dependencies via a loading set | STATUS.md | [IMPL] `modules/loader.py` |
| **Module Caching** | Loaded modules are cached to avoid re-parsing on repeated imports | STATUS.md | [IMPL] |
| **Circular Dependency Detection** | Loader tracks modules currently being loaded; raises error if a module imports itself transitively | STATUS.md | [IMPL] |
| **Selective Import** | `from X import a, b` — imports only specific names from a module | STATUS.md, SYNTAX.md | [IMPL] |
| **Aliased Import** | `import X as Y` — imports a module under a different name | STATUS.md, SYNTAX.md | [IMPL] |
| **Export Declaration** | `export name` — marks a name as publicly accessible from other modules | STATUS.md, SYNTAX.md | [IMPL] |
| **Keyword-Safe Dotted Names** | Parser extension allowing keywords (like `list`) inside module import paths: `import sigil.list` | STATUS.md (memory), STATUS.md | [IMPL] (`_expect_identifier_or_keyword()`) |
| **`sigil.math`** | Standard library: `sqrt`, `abs`, `floor`, `ceil`, `round`, `pow`, `log`, `sin`, `cos`, `PI`, `E` | STATUS.md | [IMPL] |
| **`sigil.text`** | Standard library: `length`, `substring`, `split`, `join`, `lowercase`, `uppercase`, `trim`, `replace`, `starts_with`, `ends_with` | STATUS.md | [IMPL] |
| **`sigil.list`** | Standard library: `range`, `reverse`, `flatten`, `unique`, `zip`, `sum`, `count`, `length` | STATUS.md | [IMPL] |
| **`sigil.logic`** | Standard library: `xor`, `implies`, `nand`, `type_of`, `is_number`, `is_text`, `is_list` | STATUS.md | [IMPL] |
| **`sigil.time`** | Standard library: `now`, `now_ms`, `format_timestamp`, `elapsed`, `duration_seconds` | STATUS.md | [IMPL] |
| **`sigil.trace`** | Standard library: `to_json`, `fired_rules`, `rule_count`, `duration_ms` | STATUS.md | [IMPL] |
| **`sigil.io`** | Standard library: `read_file`, `write_file`, `file_exists`, `parse_json`, `to_json` | STATUS.md | [IMPL] |
| **`sigil.rules`** | Planned stdlib: rule combinators, priority helpers, conflict resolution utilities | ARCHITECTURE.md | [PLANNED] |
| **`sigil.neural`** | Planned stdlib: neural backend configuration, model registry | ARCHITECTURE.md | [PLANNED] (Phase 3) |
| **`sigil.explain`** | Planned stdlib: explanation generation, NL output from traces | ARCHITECTURE.md | [PLANNED] |
| **Stdlib Function Signature** | All stdlib functions take `(args: list[Value], trace: ProgramTrace) -> Value` | STATUS.md (memory) | [IMPL] |

---

## Category 10: Interoperability / FFI

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Hosted Language** | A language that runs on top of another language's runtime, gaining its ecosystem; Clojure-on-JVM is the archetype; Sigil-on-Python follows the same pattern | INTEROP.md, LANGUAGE_INTEROP.md | [IMPL] (by design) |
| **Python FFI** | Sigil's ability to import and call Python libraries directly via `import python X`. Full bidirectional marshaling, error translation, and callable wrapping | INTEROP.md, ARCHITECTURE.md | [IMPL] (Phase 3) `src/sigil/ffi/` |
| **Rust FFI** | Sigil's Rust core (`sigil_core`) providing `ReteNetwork`, `ConstraintSolver`, and trace serialization via PyO3 | INTEROP.md, ARCHITECTURE.md | [IMPL] (Phase 3) |
| **FFI Boundary Layer** | The explicit layer in Sigil where type marshaling and error translation occur between Sigil and host languages | INTEROP.md | [IMPL] (Python: `marshal.py`; Rust: `values.rs`) |
| **Type Marshaling** | Converting values between Sigil types and Python/Rust types at the FFI boundary: `Number ↔ int/float`, `Text ↔ str`, `Symbol ↔ str`, `Record ↔ dict`, `Closure` → error | INTEROP.md, LANGUAGE_INTEROP.md | [IMPL] `ffi/marshal.py`, `sigil_core/src/values.rs` |
| **PyO3** | Rust library providing safe, high-performance bindings between Rust and Python via the CPython C API | INTEROP.md, LANGUAGE_INTEROP.md, STATUS.md | [IMPL] (PyO3 0.25) |
| **maturin** | Build tool for compiling Rust extensions and packaging them as Python wheels; `maturin develop` for dev, `maturin build --release` for production | INTEROP.md, LANGUAGE_INTEROP.md, STATUS.md | [IMPL] |
| **sigil_core** | The Rust crate providing performance-critical components: `ReteNetwork` (pattern matcher), `ConstraintSolver`, `serialize_trace_json`/`serialize_trace_compact`, `SigilValue` type. Future: bytecode VM | ARCHITECTURE.md, INTEROP.md, STATUS.md | [IMPL] (Phase 3) |
| **`#[pyfunction]`** | PyO3 attribute macro marking a Rust function as callable from Python. Used for `serialize_trace_json`, `serialize_trace_compact` | LANGUAGE_INTEROP.md | [IMPL] (Phase 3) |
| **`#[pyclass]`** | PyO3 attribute macro marking a Rust struct as a Python class. Used for `ReteNetwork`, `ConstraintSolver` | LANGUAGE_INTEROP.md | [IMPL] (Phase 3) |
| **`#[pymodule]`** | PyO3 attribute macro registering a Rust module for Python import | LANGUAGE_INTEROP.md, STATUS.md | [IMPL] |
| **Inline Python Block** | `define x as python: ...` escape hatch for complex Python operations not easily expressible in Sigil | INTEROP.md, SYNTAX.md | [PLANNED] (Phase 3) |
| **Error Translation** | Converting Python exceptions into Sigil error types with source context. `translate_python_error()` wraps exceptions preserving `__cause__` | INTEROP.md | [IMPL] (Phase 3) `ffi/errors.py` |
| **`using rust` Directive** | Optimization hint on a rule to delegate evaluation to the Rust core; same Sigil code, different execution backend | INTEROP.md, GRAMMAR.peg | [PLANNED] (Phase 3) |
| **Gradual Rust Migration** | Pattern: start with pure Sigil (Python interpreter), add `using rust` to hot rules later without changing rule code | INTEROP.md | [PLANNED] (Phase 3) |
| **`wrap_python_callable`** | Function in `ffi/marshal.py` that wraps a Python callable to accept Sigil values (list[Value], ProgramTrace) and return Sigil values. Handles arg marshaling and error translation automatically | ffi/marshal.py | [IMPL] (Phase 3) |
| **`import_python_module`** | Function that uses `importlib.import_module()` to import a Python module and marshal its public API into a dict of Sigil values. Missing modules fail gracefully (bind empty record) | ffi/python_interop.py | [IMPL] (Phase 3) |
| **`SigilValue` (Rust)** | Rust enum mirroring the Python `Value` union: `None`, `Bool`, `Int`, `Float`, `Text`, `Symbol`, `Record`, `List`. Implements `from_python()`/`to_python()` for PyO3 marshaling, and serde traits for serialization | sigil_core/src/values.rs | [IMPL] (Phase 3) |
| **Alpha Node** | In the Rete algorithm: a node testing a single condition on a single fact. Sigil's Rete-lite uses alpha nodes for each condition in a rule | RETE docs | [IMPL] (Phase 3, embedded in matcher.rs) |
| **Trace Serialization** | Rust-based fast JSON serialization of `ProgramTrace` data. `serialize_trace_json()` (pretty) and `serialize_trace_compact()` (no whitespace) exposed via PyO3 | sigil_core/src/trace.rs | [IMPL] (Phase 3) |
| **UniFFI** | Mozilla tool generating multi-language FFI bindings from a single Rust crate; future option for JavaScript/Swift/WASM bindings | LANGUAGE_INTEROP.md, BIBLIOGRAPHY.md | [PLANNED] (Phase 5+) |
| **Project Panama** | JDK 22 Foreign Function & Memory API (4-5x faster than JNI); reference model for managed FFI design | LANGUAGE_INTEROP.md, BIBLIOGRAPHY.md | [REF] |
| **C ABI** | The stable binary interface for calling C functions from other languages; Rust's `extern "C"` and Zig's `@cImport` both target this; gives Sigil indirect access to C/BLAS/LAPACK via Rust | LANGUAGE_INTEROP.md | [REF] |
| **WASM Target** | Compiling Sigil/sigil_core to WebAssembly for browser-based rule evaluation; no server round-trip | ARCHITECTURE.md, ROADMAP.md, INTEROP.md | [PLANNED] (Phase 5) |
| **Pyodide** | Python interpreter compiled to WebAssembly; potential path for running the Sigil interpreter in the browser | INTEROP.md | [PLANNED] (Phase 5) |

---

## Category 11: Functional Programming Concepts (Influences)

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Homoiconicity** | Property where code and data share the same representation; in LISP, programs are lists; in Sigil, the core AST layer enables program introspection and LLM-based generation | VISION.md, FOUNDATIONS.md, LISP_AND_FP.md | [REF] (Sigil's two-layer design is homoiconicity-inspired) |
| **S-Expression** | Nested list notation `(op arg1 arg2 ...)` originating in LISP; serves as the universal intermediate representation in compilers, SMT solvers (SMT-LIB), WASM text format | VISION.md, LISP_AND_FP.md, ARCHITECTURE.md | [REF] (Sigil's core AST layer is S-expression-inspired) |
| **Metaprogramming** | Programs that generate, inspect, or transform other programs; LISP macros are the canonical example; LLM→Sigil generation is Sigil's metaprogramming story | LISP_AND_FP.md, FOUNDATIONS.md | [REF] (Phase 4: NL→Sigil generator) |
| **Macro** | Compile-time code transformation; LISP macros; Julia's `@rule` macros; Sigil's surface→core desugaring is analogous | LISP_AND_FP.md | [REF] (future: user-defined syntax macros) |
| **Pure Function** | A function whose output depends only on its inputs with no side effects; Sigil compute blocks are pure by default | LISP_AND_FP.md, SEMANTICS.md | [IMPL] |
| **Immutability** | Data structures cannot be modified after creation; new values are created instead; Sigil's default for all bindings | SEMANTICS.md, LISP_AND_FP.md | [IMPL] |
| **Higher-Order Function** | A function that accepts or returns other functions; Sigil supports closures, lambdas, and the pipeline operator as HOF patterns | LISP_AND_FP.md, STATUS.md | [IMPL] |
| **Pattern Matching** | Destructuring data by shape with exhaustiveness checking; Sigil's `match` expression and rule conditions as pattern matches | LISP_AND_FP.md, SYNTAX.md | [IMPL] |
| **Algebraic Data Types** | Sum types (one of) + product types (record); the mathematical foundation of Sigil's type system | LISP_AND_FP.md, TYPE_SYSTEM.md | [IMPL] |
| **Curry-Howard Correspondence** | Equivalence between proofs and programs; types as propositions; referenced via Lean 4's dependent type system | LISP_AND_FP.md, BIBLIOGRAPHY.md | [REF] |
| **Lazy Evaluation** | Computing values only when needed; Haskell's default; future demand-driven backward chaining in Sigil | LISP_AND_FP.md, FOUNDATIONS.md | [PLANNED] (future) |
| **QuickCheck / Hypothesis** | Property-based test frameworks generating random inputs to verify invariants; Sigil uses Hypothesis for parser/type checker testing | FOUNDATIONS.md, COMPILER_DESIGN.md, ROADMAP.md | [IMPL] |
| **Monadic Effects** | Type-level tracking of effects (IO, state, failure); `neural` keyword as Sigil's explicit effect boundary, analogous to Haskell's `IO` monad | LISP_AND_FP.md | [REF] |
| **Referential Transparency** | Pure expressions can be replaced by their value without changing behavior; enables caching and memoization | LISP_AND_FP.md, SEMANTICS.md | [IMPL] |

---

## Category 12: Related Languages and Systems

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **Prolog** | 1972 logic programming language by Colmerauer; Horn clauses, unification, backtracking; declarative style inspired Sigil's rule syntax | VISION.md, EXISTING_DSLS.md, FOUNDATIONS.md | [REF] |
| **Datalog** | Restricted logic programming (no function symbols, guaranteed termination); foundation for Scallop; parallels Sigil's constrained NL for parsability | EXISTING_DSLS.md | [REF] |
| **LISP** | 1958 language by John McCarthy; introduced homoiconicity, symbolic computation, REPL, garbage collection; the first AI language | VISION.md, FOUNDATIONS.md, LISP_AND_FP.md | [REF] |
| **Haskell** | Pure functional language; influenced Sigil's type classes, guards, `where` clauses, `Maybe` type, monadic effects, QuickCheck | FOUNDATIONS.md, LISP_AND_FP.md | [REF] |
| **Lean 4** | Dependently-typed functional language + theorem prover; won 2025 ACM SIGPLAN PL Award; used by AlphaProof; shows language can serve as programming language + proof assistant + AI target simultaneously | FOUNDATIONS.md, LISP_AND_FP.md, BIBLIOGRAPHY.md | [REF] |
| **Clojure** | JVM-hosted LISP; pioneered the hosted language pattern Sigil follows; persistent immutable data structures; REPL-driven development | FOUNDATIONS.md, LANGUAGE_INTEROP.md, LISP_AND_FP.md | [REF] |
| **OCaml / ML Family** | Statically typed functional languages; algebraic data types, pattern matching, module system, Hindley-Milner inference all influenced Sigil | LISP_AND_FP.md | [REF] |
| **Julia** | High-performance language for scientific computing; multiple dispatch, metaprogramming, differentiable programming; complementary to Sigil (Julia builds engines, Sigil expresses rules) | JULIA_AND_NS.md | [REF] |
| **Zig** | Systems language with zero-cost C FFI via embedded Clang; influenced Sigil's FFI philosophy | FOUNDATIONS.md, LANGUAGE_INTEROP.md | [REF] |
| **Rust** | Systems language with memory safety; used for Sigil's performance core (sigil_core) via PyO3/maturin | ARCHITECTURE.md, INTEROP.md, STATUS.md | [IMPL] (Rust 1.94.0) |
| **Wolfram Language** | 1988+ symbolic computation language; key insight: NL works by translating to a well-defined computational language, not by being NL itself | VISION.md, FOUNDATIONS.md, EXISTING_DSLS.md | [REF] |
| **COBOL** | 1959 "English-like" business language; lesson: verbosity and NL appearance don't improve maintainability without clear semantics | FOUNDATIONS.md, EXISTING_DSLS.md | [REF] |
| **Stan** | Probabilistic programming language; shows that domain-specific constraints enable better tooling (same principle as Sigil's constrained NL) | EXISTING_DSLS.md | [REF] |
| **Pyro / NumPyro** | Universal PPLs (PyTorch / JAX backends); show how a DSL can be hosted within Python while providing domain-specific semantics | EXISTING_DSLS.md | [REF] |
| **Church / WebPPL** | Theoretical foundations of probabilistic programming; "generative models as programs" parallels Sigil's "rules as programs" | EXISTING_DSLS.md | [REF] |
| **Lox** | Teaching language from "Crafting Interpreters" (Nystrom 2021); tree-walking→bytecode VM implementation path that Sigil follows | FOUNDATIONS.md, COMPILER_DESIGN.md | [REF] |
| **Symbolics.jl** | Julia computer algebra system; symbolic expression manipulation | JULIA_AND_NS.md | [REF] |
| **Metatheory.jl** | Julia term rewriting and e-graphs library for symbolic rule application | JULIA_AND_NS.md | [REF] |
| **SymbolicRegression.jl** | Julia library discovering equations from data; output could be exported as Sigil rules | JULIA_AND_NS.md | [REF] |
| **Zygote.jl** | Julia automatic differentiation; enables gradient flow through hybrid pipelines | JULIA_AND_NS.md | [REF] |
| **Multiple Dispatch** | Julia's defining feature: runtime picks function based on types of ALL arguments; enables clean symbolic/neural type separation; potential future Sigil extension | JULIA_AND_NS.md | [REF] |
| **KBANN** | Knowledge-Based Artificial Neural Networks: symbolic rules compiled into neural network weights (Kautz Type 4) | FOUNDATIONS.md, NS_LANDSCAPE.md | [REF] |
| **DeepSeek-Prover-V2** | 2025 AI system targeting Lean 4 for formal mathematical proof; validates neural→formal language pipeline | NS_LANDSCAPE.md | [REF] |
| **Ruff** | Python linter written in Rust; demonstrates 10-100x speedup of Rust for Python tooling | COMPILER_DESIGN.md | [REF] |

---

## Category 13: Production / Regulated Domains

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **AML/KYC** | Anti-Money Laundering / Know Your Customer; financial compliance domain requiring auditable decision traces; primary real-world use case for Sigil | REAL_WORLD_BRIDGE.md, BIBLIOGRAPHY.md | [REF] |
| **BSA (Bank Secrecy Act)** | US federal law requiring financial institutions to report suspicious transactions; Sigil's trace system directly addresses BSA audit requirements | SYNTAX.md, BIBLIOGRAPHY.md | [REF] |
| **CFPB** | Consumer Financial Protection Bureau; lending regulations requiring adverse action notices with reasons; Sigil's explain clauses address this | SYNTAX.md, BIBLIOGRAPHY.md | [REF] |
| **ECOA** | Equal Credit Opportunity Act; anti-discrimination lending law; Sigil's deterministic rules ensure consistent, auditable decisions | SYNTAX.md | [REF] |
| **FCRA** | Fair Credit Reporting Act; credit bureau data usage regulations | SYNTAX.md | [REF] |
| **HIPAA** | Health Insurance Portability and Accountability Act; healthcare data privacy; Sigil's trace system supports compliance logging | BIBLIOGRAPHY.md, REAL_WORLD_BRIDGE.md | [REF] |
| **EMTALA** | Emergency Medical Treatment and Labor Act; emergency care requirements | BIBLIOGRAPHY.md | [REF] |
| **EU AI Act** | European Union regulation mandating decision traces for high-risk AI systems; Sigil's always-on trace system is designed for this | REAL_WORLD_BRIDGE.md | [REF] |
| **FATF** | Financial Action Task Force; international AML guidance | BIBLIOGRAPHY.md | [REF] |
| **ESI (Emergency Severity Index)** | 5-level triage protocol for emergency departments; used in the medical_triage.sigil example | STATUS.md, BIBLIOGRAPHY.md | [REF] |
| **OFAC SDN** | Office of Foreign Assets Control Specially Designated Nationals list; sanctions screening use case | BIBLIOGRAPHY.md | [REF] |
| **Zest AI** | Fintech company using ML + symbolic compliance rules for lending; represents the production neuro-symbolic pattern Sigil formalizes | BIBLIOGRAPHY.md, REAL_WORLD_BRIDGE.md | [REF] |
| **Featurespace ARIC** | Adaptive behavioral analytics platform for financial crime detection | BIBLIOGRAPHY.md, REAL_WORLD_BRIDGE.md | [REF] |
| **ComplyAdvantage** | AI-powered financial compliance and risk data company | BIBLIOGRAPHY.md | [REF] |
| **Isabel Healthcare** | Clinical decision support system using symbolic reasoning for diagnosis | BIBLIOGRAPHY.md, REAL_WORLD_BRIDGE.md | [REF] |
| **Confidence-to-Predicate Interface** | The key technical problem in regulated AI: converting a probabilistic model output (0.0-1.0) into a discrete, auditable symbolic fact; Sigil's `neural` + `confidence_threshold` + `fallback` is the solution | REAL_WORLD_BRIDGE.md | [IMPL] (stub) |
| **Ad-Hoc Glue Code** | The current industry approach to bridging neural and symbolic: JSON configs, YAML files, Python scripts, REST APIs with no standard interface, no type safety, no integrated trace; what Sigil replaces | VISION.md, REAL_WORLD_BRIDGE.md | [REF] |

---

## Category 14: Developer Tooling / Future Features

| Term | Description | Where It Appears | Status |
|------|-------------|-----------------|--------|
| **CLI (`sigil`)** | Command-line interface: `sigil run`, `sigil lex`, `sigil parse-ast`, `sigil check`, `sigil repl` | STATUS.md | [IMPL] `src/sigil/cli.py` |
| **`sigil run`** | Execute a `.sigil` file with optional `--input JSON` and `--trace` flags | STATUS.md | [IMPL] |
| **`sigil lex`** | Dump the token stream of a source file for debugging | STATUS.md | [IMPL] |
| **`sigil parse-ast`** | Dump the AST of a source file for debugging | STATUS.md | [IMPL] |
| **`sigil check`** | Run the type checker on a source file | STATUS.md | [IMPL] |
| **`sigil repl`** | Interactive REPL | STATUS.md | [IMPL] |
| **`sigil fmt`** | Auto-formatter for Sigil source code | ROADMAP.md | [PLANNED] (Phase 4) |
| **`sigil lint`** | Linter: unused rules, type warnings, unreachable conditions | ROADMAP.md | [PLANNED] (Phase 4) |
| **`sigil parse "..."`** | NL-to-Sigil generator CLI command | ROADMAP.md | [PLANNED] (Phase 4) |
| **LSP Server** | Language Server Protocol implementation for editor integration: syntax highlighting, autocomplete, diagnostics, go-to-definition | ARCHITECTURE.md, ROADMAP.md | [PLANNED] (Phase 5) |
| **VS Code Extension** | Editor extension powered by the LSP server | ROADMAP.md | [PLANNED] (Phase 5) |
| **Formatter** | `sigil fmt` — auto-formats Sigil source code to consistent style | ROADMAP.md | [PLANNED] (Phase 4) |
| **Visual Rule Builder** | Web-based drag-and-drop editor for Sigil rules with live trace visualization and collaborative editing | ROADMAP.md | [PLANNED] (Phase 5) |
| **Distributed Execution** | Rule evaluation across multiple nodes with shared fact space and consistency guarantees; millions of decisions/second | ARCHITECTURE.md, ROADMAP.md | [PLANNED] (Phase 5) |
| **Formal Verification** | Rule completeness checking, conflict detection, termination analysis; integration with SMT solver (Z3) | ROADMAP.md | [PLANNED] (Phase 5) |
| **LLVM IR** | LLVM's intermediate representation; potential future backend for native Sigil compilation | COMPILER_DESIGN.md | [PLANNED] (Phase 5+) |
| **NeSy (Neural-Symbolic) Workshop** | Annual research workshop on neural-symbolic learning and reasoning | NS_LANDSCAPE.md, BIBLIOGRAPHY.md | [REF] |
| **NSE 2026** | Neuro-Symbolic Software Engineering workshop at ICSE 2026 (April 12, 2026) | NS_LANDSCAPE.md, BIBLIOGRAPHY.md | [REF] |
| **pyproject.toml** | Python project configuration file; Sigil uses maturin as build backend | STATUS.md | [IMPL] |
| **ruff** | Fast Python linter (written in Rust); used for Sigil's own Python code linting | STATUS.md | [IMPL] |
| **mypy** | Python static type checker; Sigil passes with 0 errors across 25 source files | STATUS.md | [IMPL] |
| **Hypothesis** | Python property-based testing library; used for parser and type checker tests | ROADMAP.md, COMPILER_DESIGN.md | [IMPL] |
| **proptest** | Rust property-based testing library; future use in Rust core tests | COMPILER_DESIGN.md | [PLANNED] (Phase 3) |
| **Source Location** | `SourceLocation` dataclass recording file, line, and column of a token; used in all error messages | STATUS.md | [IMPL] `src/sigil/errors.py` |
| **Error Hierarchy** | `SigilError` → `LexError`, `ParseError`, `TypeError`, `RuntimeError` etc.; structured error types | STATUS.md | [IMPL] `src/sigil/errors.py` |

---

## Quick-Reference Summary by Status

**Fully Implemented [IMPL]:** Lexer, Parser (recursive descent), AST (40+ nodes), Type Checker (11 checks), Tree-Walking Interpreter (1260 lines), Forward Chaining Engine, Backward Chaining Engine, Proof Trees, REPL, Module System (resolver + loader + cycle detection), Standard Library (math/text/list/logic/time/trace/io), CLI, Python FFI (`import python X` with bidirectional marshaling), Neural Bridge (pluggable `ModelBackend` + `ModelRegistry` + HuggingFace backend), Rust Core (Rete-lite pattern matcher, constraint solver, trace serialization via PyO3), 764 tests passing, maturin/PyO3 build.

**Planned [PLANNED]:** NL-to-Sigil Generator (Phase 4), Inline Python Blocks (Phase 4), Formatter/Linter (Phase 4), Tree-sitter Grammar (Phase 4), LSP Server (Phase 5), Bytecode VM in Rust (Phase 5), WASM Target (Phase 5), Formal Verification / SMT (Phase 5), Distributed Execution (Phase 5).

**Reference Concepts [REF]:** Neuro-symbolic taxonomy (Kautz Types 1-6), DARPA Three Waves, AlphaGeometry/AlphaProof, Scallop, DeepProbLog, Homoiconicity (LISP), Multiple Dispatch (Julia), all related languages (Prolog, Haskell, Lean 4, Clojure, Inform 7), all regulatory/compliance acronyms, all production industry systems.

---

## Existing Deep-Dive Documents

Already-written research docs you can read for detailed understanding:

| Doc | Covers |
|-----|--------|
| `docs/research/PEG_GRAMMAR.md` | PEG, ordered choice, packrat, recursive descent, CFG comparison |
| `docs/research/FORWARD_BACKWARD_CHAINING.md` | Forward/backward chaining, proof trees, neuro-symbolic pipeline, rule engines |
| `docs/research/FOUNDATIONS.md` | Kautz taxonomy, AI waves, AlphaGeometry, language design principles |
| `docs/research/NEURO_SYMBOLIC_AI_LANDSCAPE.md` | Scallop, DeepProbLog, DomiKnowS, AlphaProof, provenance semirings |
| `docs/research/COMPILER_AND_LANGUAGE_DESIGN.md` | Lexer/parser design, error recovery, bytecode VMs, tree-sitter |
| `docs/research/EXISTING_DSLS_AND_LANGUAGES.md` | Inform 7, MoonBit, SimPy, LMQL, SudoLang, Prolog, Datalog |
| `docs/research/LANGUAGE_INTEROP_DEEP_DIVE.md` | PyO3, maturin, FFI patterns, Panama, UniFFI, WASM |
| `docs/research/LISP_AND_FUNCTIONAL_PROGRAMMING.md` | Homoiconicity, S-expressions, closures, ADTs, Curry-Howard |
| `docs/research/JULIA_AND_NEURO_SYMBOLIC.md` | Julia, multiple dispatch, Symbolics.jl, Metatheory.jl, Zygote |
| `docs/research/REAL_WORLD_NEURO_SYMBOLIC_BRIDGE.md` | AML/KYC, medical triage, confidence-to-predicate, production patterns |
| `docs/research/NEURO_SYMBOLIC_POSITIONING.md` | Sigil's position in the neuro-symbolic landscape |
| `docs/research/COMPARISONS.md` | Sigil vs Prolog, Drools, OPA, LangChain, DSPy |
| `docs/research/BIBLIOGRAPHY.md` | Full bibliography with citations |
| `docs/SPRINT3_FEATURES.md` | Backward chaining, temporal constraints, proof trees, type checker enhancements |

## Research Queue

Terms worth writing deep-dive docs for (like PEG_GRAMMAR.md):

- **Rete Algorithm** — The pattern-matching algorithm planned for Sigil's Rust core
- **Gradual Type Systems** — How optional types work, Siek & Taha's formalism
- **Tree-Walking vs Bytecode VM** — Why we'll switch, the Lox path
- **Algebraic Data Types** — Sum types, product types, pattern matching
- **Constraint Solving** — SMT solvers, Z3, formal verification of rules
- **Probabilistic Programming** — PPLs, inference engines, and how they relate to neural declarations
- **WASM Compilation** — Getting Sigil running in the browser
