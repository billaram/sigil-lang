# PEG Grammar — What It Is and Why Sigil Uses It

> A practical guide for anyone wondering what "PEG-based parser" actually means.

---

## 1. The Problem: Turning Text into Structure

Every programming language needs a **parser** — something that reads raw text and turns it into a tree structure the computer can work with.

```
"when x exceeds 100"   →   Parser   →   Comparison(left=x, op=exceeds, right=100)
     (text)                                    (tree structure / AST)
```

But how does the parser know what's valid syntax and what isn't? It needs **rules**. Those rules are called a **grammar**.

A grammar is a formal description of what sequences of symbols are valid in a language. There are several families of grammars. PEG is one of them.

---

## 2. Grammar Families — The Landscape

| Family | Full Name | Era | Used By |
|--------|-----------|-----|---------|
| **Regular** | Regular Expressions | 1950s | grep, sed, lexers |
| **CFG** | Context-Free Grammar | 1960s | Most traditional compilers (C, Java, Python) |
| **PEG** | Parsing Expression Grammar | 2004 | Modern DSLs, Sigil, Lua, Python 3.9+ |
| **GLR** | Generalized LR | 1970s+ | C++, Rust (partial) |

### Context-Free Grammars (CFG) — The Old Standard

CFGs (used by yacc, bison, ANTLR) describe languages using **production rules**:

```
expression → expression "+" term | term
term       → NUMBER | "(" expression ")"
```

The problem: **ambiguity**. The rule `expression → expression "+" term | term` can match in multiple ways. CFGs need extra mechanisms (precedence tables, associativity rules) to resolve this.

### PEG — The Unambiguous Alternative

Bryan Ford introduced PEGs in 2004 to eliminate ambiguity entirely.

---

## 3. What Makes PEG Different

### The Core Idea: Ordered Choice

In a CFG, `A | B` means "A or B, and we'll figure out which one later (possibly both)."

In a PEG, `A / B` means "**try A first. If A succeeds, use it. Only try B if A fails.**"

This is called **ordered choice** and it changes everything:

```
-- CFG (ambiguous): both alternatives are equally valid
if_stmt → "if" expr "then" stmt "else" stmt
        | "if" expr "then" stmt

-- PEG (unambiguous): try the longer match first
if_stmt ← "if" expr "then" stmt "else" stmt
         / "if" expr "then" stmt
```

In the CFG, `if x then if y then a else b` is ambiguous — does `else` belong to the outer or inner `if`? The grammar doesn't say.

In the PEG, the first alternative (with `else`) is always tried first. No ambiguity. Ever.

### PEG Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `"text"` | Literal match | `"when"` matches the word `when` |
| `e1 e2` | Sequence | `"when" condition` matches `when` then a condition |
| `e1 / e2` | Ordered choice | Try `e1` first, then `e2` |
| `e*` | Zero or more | `condition*` matches 0+ conditions |
| `e+` | One or more | `digit+` matches 1+ digits |
| `e?` | Optional | `"else" block?` matches with or without else |
| `&e` | Lookahead (positive) | `&"when"` succeeds if `when` is next, doesn't consume |
| `!e` | Lookahead (negative) | `!"then"` succeeds if `then` is NOT next |

### A Real PEG Rule from Sigil

```peg
RuleDecl    ← "rule" Identifier ("with" "priority" Number)? ":"
               INDENT Conditions Action Explain? DEDENT

Conditions  ← "when" Condition ("and" Condition / "or" Condition)*

Condition   ← Expression "exceeds" Expression
             / Expression "is" "below" Expression
             / Expression "is" "between" Expression "and" Expression
             / Expression "is" Expression
```

Reading this: a `RuleDecl` is the keyword `rule`, then an identifier, optionally `with priority <number>`, then a colon, then an indented block of conditions + action + optional explanation.

---

## 4. Why PEG Matters for Sigil

### 4.1 Unambiguous by Construction

Sigil's constrained natural language has many keywords that could clash (`and`, `or`, `is`, `with`). PEG's ordered choice means there's always exactly one way to parse any valid Sigil program. No surprises.

```sigil
rule check with priority 10:
  when status is :active and score exceeds 80
  then approve
```

A CFG parser might be confused: is `and` part of the condition or a separate construct? A PEG parser isn't — it tries the "condition `and` condition" rule first.

### 4.2 Linear-Time Parsing

PEGs can be parsed in **O(n)** time using a technique called **packrat parsing** (memoization of intermediate results). This means parsing time is proportional to file size — no exponential blowup on pathological inputs.

Sigil's target: **< 10ms for 1000 lines**.

### 4.3 Natural Fit for Keyword-Heavy Languages

Sigil has ~30 keywords (`when`, `then`, `exceeds`, `is`, `between`, etc.). PEGs handle keyword-heavy grammars elegantly because ordered choice naturally disambiguates:

```peg
-- "is between" tried before "is" alone
Condition ← Expression "is" "between" Expression "and" Expression
          / Expression "is" "not" Expression
          / Expression "is" Expression
```

### 4.4 Maximum Control with Hand-Written Implementation

Sigil uses a **hand-written recursive descent parser** rather than a PEG library. Each grammar rule becomes a Python function:

```python
# The PEG rule:  Condition ← Expression "exceeds" Expression / ...
# Becomes this Python function:

def _parse_condition(self) -> ast.Condition:
    left = self._parse_expression()

    if self._match_value("exceeds"):
        right = self._parse_expression()
        return ast.Comparison(left=left, op="exceeds", right=right)

    if self._match_value("is"):
        if self._match_value("between"):
            low = self._parse_expression()
            self._expect_value("and")
            high = self._parse_expression()
            return ast.Between(expr=left, low=low, high=high)
        # ... more alternatives
```

This gives us:
- Full control over error messages
- Easy debugging (set a breakpoint in `_parse_condition`)
- No external dependencies
- Straightforward extension when adding new syntax

---

## 5. PEG vs Other Approaches — Trade-offs

| Property | PEG | CFG (LALR/LL) | Hand-written Ad-hoc |
|----------|-----|---------------|---------------------|
| Ambiguity | **Impossible** | Possible (needs resolution) | Depends on author |
| Time complexity | O(n) with packrat | O(n) for LALR | Depends |
| Error messages | Good (with effort) | Often cryptic | Best (full control) |
| Left recursion | Not directly supported | Supported | Supported |
| Composability | Excellent | Moderate | Poor |
| Tooling | Moderate | Excellent (yacc, ANTLR) | None needed |
| Learning curve | Low | High | Low |

### The One PEG Limitation: No Left Recursion

PEGs cannot directly handle left-recursive rules:

```peg
-- This INFINITE LOOPS in a PEG:
Expression ← Expression "+" Term / Term
```

The workaround is to rewrite as iteration:

```peg
-- This works:
Expression ← Term ("+" Term)*
```

Sigil's parser uses this pattern throughout for arithmetic and comparisons.

---

## 6. PEG in the Sigil Compilation Pipeline

```
Source (.sigil)
    │
    ▼
[Lexer] ─── characters → tokens
    │         (not PEG — simple state machine)
    │
    ▼
[Parser] ─── tokens → AST
    │         ★ THIS IS WHERE PEG RULES LIVE ★
    │         Hand-written recursive descent
    │         Each PEG rule = one Python method
    │
    ▼
[Type Checker] ─── AST → typed AST
    │
    ▼
[Interpreter] ─── typed AST → decision + trace
```

The PEG grammar is the **formal specification** of what valid Sigil looks like. It lives in `docs/spec/GRAMMAR.peg`. The parser in `src/sigil/parser/parser.py` is the **implementation** of that specification.

---

## 7. Key Takeaways

1. **PEG is a grammar formalism** — a way to describe what valid programs look like.
2. **Ordered choice** eliminates ambiguity — there's always exactly one parse.
3. **Linear time** — parsing is fast and predictable.
4. **Sigil uses PEG because** its keyword-heavy natural language syntax needs unambiguous parsing.
5. **The parser is hand-written** — PEG is the spec, recursive descent is the implementation.
6. **PEG is a parser/compiler concept** — it has nothing to do with rule evaluation, forward chaining, or runtime behavior.

---

## References

- Ford, B. (2004). *Parsing Expression Grammars: A Recognition-Based Syntactic Foundation*. POPL '04.
- `docs/spec/GRAMMAR.peg` — Sigil's formal PEG grammar
- `src/sigil/parser/parser.py` — Sigil's parser implementation
