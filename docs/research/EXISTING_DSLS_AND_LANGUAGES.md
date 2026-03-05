# Existing DSLs, Languages, and Systems in the AI Space

A comprehensive survey of languages and frameworks relevant to Sigil's design.

---

## 1. Probabilistic Programming Languages

Probabilistic programming languages (PPLs) represent uncertainty as a first-class concept — models are programs, inference is execution.

### Stan
- **Type**: First-order PPL (restricted but well-optimized)
- **Backend**: C++ code generation
- **Inference**: High-quality Hamiltonian Monte Carlo (HMC), NUTS sampler
- **Strengths**: Best-in-class inference quality; mature ecosystem; strong community
- **Limitations**: Not Turing-complete; restricted control flow; no neural integration
- **Relevance to Sigil**: Stan shows that a restricted DSL can outperform general-purpose solutions in its domain. Sigil's constrained NL syntax follows the same principle.

### Pyro / NumPyro
- **Type**: Universal PPL (Turing-complete)
- **Backend**: PyTorch (Pyro), JAX (NumPyro)
- **Inference**: Variational inference, MCMC, importance sampling
- **Strengths**: Deep learning integration; flexible model specification; GPU acceleration
- **Relevance to Sigil**: Pyro demonstrates how a DSL can be hosted within Python while providing domain-specific semantics. Sigil's Python FFI follows a similar pattern.

### Church / WebPPL
- **Type**: Universal PPL based on Scheme/JavaScript
- **Significance**: Theoretical foundation for probabilistic programming
- **Key concept**: "Generative models as programs" — a program defines a probability distribution by describing how to generate samples
- **Relevance to Sigil**: Church's LISP heritage connects to Sigil's S-expression core layer. Generative models as programs is analogous to rules as programs.

### PyMC
- **Type**: Universal PPL
- **Backend**: PyTensor (formerly Theano)
- **Strengths**: Mature ecosystem; excellent visualization; Bayesian workflow
- **Relevance**: Shows how Python-hosted DSLs can achieve wide adoption through good developer experience.

### Key Insight from PPLs
PPLs demonstrate that **domain-specific constraints enable better tooling**. Stan's restricted language enables automatic differentiation and efficient samplers. Sigil's constrained NL enables deterministic parsing, exhaustive type checking, and reliable LLM generation.

---

## 2. Logic Programming Languages

### Prolog (1972)
- **Paradigm**: Logic programming (Horn clauses, unification, backtracking)
- **Strengths**: Natural for knowledge representation; built-in search; pattern matching
- **Weaknesses**: Steep learning curve; limited ecosystem; performance issues at scale
- **Modern usage**: Expert systems, NLU, constraint solving, education
- **Relevance to Sigil**: Prolog's declarative style ("declare what is true, not how to compute it") directly influences Sigil's rule declarations. But Sigil replaces Prolog's formal logic syntax with constrained NL.

### Datalog
- **Paradigm**: Restricted logic programming (no function symbols, guaranteed termination)
- **Strengths**: Decidable; efficient evaluation; well-suited for databases and program analysis
- **Modern usage**: Foundation for Scallop; Datomic database; Soufflé (program analysis)
- **Relevance to Sigil**: Datalog's restriction for tractability parallels Sigil's constrained NL for parsability. Scallop proved Datalog works as a neuro-symbolic foundation.

### Answer Set Programming (ASP)
- **Paradigm**: Stable model semantics
- **Strengths**: Non-monotonic reasoning; constraint satisfaction; combinatorial optimization
- **Tools**: Clingo, DLV
- **Relevance**: ASP handles reasoning patterns (defaults, exceptions, preferences) that pure forward chaining cannot. Future Sigil extension opportunity.

---

## 3. Neuro-Symbolic DSLs and Frameworks

### Scallop (PLDI 2023, University of Pennsylvania)
The most significant purpose-built neuro-symbolic DSL to date.

**Three key features**:
1. **Relational data model**: Facts represented as relations (tables)
2. **Datalog with extensions**: Recursion, aggregation, negation
3. **Provenance semirings**: Different semirings enable different reasoning modes (probabilistic, top-k, differentiable)

**Example**:
```scallop
// Neural predicate (connected to PyTorch model)
rel digit(img, label) = neural_net(img, label)

// Symbolic reasoning over neural outputs
rel sum_result(a + b) = digit(img_a, a), digit(img_b, b)

// Query
query sum_result
```

**Performance**: Evaluated on 8 applications (MNIST addition, path finding, Pac-Man, knowledge graph completion) — achieved comparable or superior accuracy to pure neural baselines.

**Key difference from Sigil**: Scallop enables *differentiable* reasoning (training through symbolic layers). Sigil separates concerns: neural for perception, symbolic for deterministic execution. Scallop targets ML researchers; Sigil targets domain experts and engineers.

### DeepProbLog
- Extends ProbLog (probabilistic logic programming) with neural predicates
- Neural networks can serve as probability sources for logical rules
- Enables end-to-end training: gradients flow through logic to neural networks
- **Predecessor to Scallop** — Scallop generalized DeepProbLog's approach

### DomiKnowS
- **Origin**: University of Pennsylvania
- **Approach**: Declarative Python library encoding concepts, relations, and logical constraints as a conceptual graph
- **Key paper**: "Neurosymbolic Programming: Pitfalls and Opportunities" (NeSy 2025)
- **Finding**: "Authoring NeSy programs remains challenging, as existing frameworks impose a steep learning curve, requiring users to know the syntax and semantics of the target formalism"
- **Relevance to Sigil**: This finding directly motivates Sigil's constrained NL syntax — reducing the learning curve for neuro-symbolic programming.

### AgenticDomiKnowS (ADS, 2025-2026)
- Extends DomiKnowS with agentic LLM-powered program synthesis
- Users describe neuro-symbolic programs in natural language
- An LLM agent breaks development into stages and generates code
- **Validates Sigil's thesis**: Natural language → neuro-symbolic program is a viable and desired workflow

---

## 4. Natural Language Oriented Programming Languages

### Inform 7 (2006)
**The closest any language has come to natural language programming.**

```inform7
The Kitchen is a room. "A clean, well-lit kitchen."
The oven is in the Kitchen. The oven is a container. The oven is openable.
The cake is in the oven.

Instead of opening the oven when the cake is not in the oven:
    say "The oven is already empty."

After taking the cake:
    say "You carefully remove the cake. It smells wonderful."
```

This is **valid, compilable, executable code**.

**Key properties**:
- Top 100 TIOBE programming language
- Open-sourced in 2022
- Domain: Interactive fiction (text adventures)
- Compiles through Inform 6 to Z-machine/Glulx bytecode
- Demonstrates that NL programming works **within a constrained domain with clear ontology**

**Lessons for Sigil**:
1. Constrained NL succeeds when the domain has a clear vocabulary
2. A formal grammar can underlie natural-looking syntax
3. NL readability genuinely improves domain expert accessibility
4. Scaling beyond the constrained domain is the hard part

### AppleScript (1993)
```applescript
tell application "Finder"
    set the_files to every file of folder "Documents" of home
    repeat with a_file in the_files
        if name extension of a_file is "txt" then
            move a_file to trash
        end if
    end repeat
end tell
```

**What went wrong**: English-like syntax without formal semantics created confusion. Users expected natural language understanding but got rigid syntax that merely *looked* like English. Minor phrasing differences caused failures.

**Lesson for Sigil**: The grammar must be formally specified (PEG). The NL appearance is a surface feature; the underlying parsing must be deterministic and well-defined.

### Wolfram Language (1988+)
```wolfram
(* Natural language input translating to symbolic computation *)
Interpreter["City"]["the capital of France"]
(* → Entity["City", {"Paris", "IleDeFrance", "France"}] *)

(* Symbolic computation *)
Solve[x^2 + 2x + 1 == 0, x]
(* → {{x -> -1}} *)
```

**Key insight (Stephen Wolfram, 2010)**: NL programming works by **translating to a well-defined computational language**, not by making the language itself natural language.

**Relevance to Sigil**: This is exactly Sigil's architecture:
```
Natural Language (input) → Neural Parser → Sigil (formal language) → Execution
```

### COBOL (1959)
Often cited as "English-like programming." In practice, COBOL's verbosity didn't improve readability or maintainability. The lesson: English-like syntax alone doesn't make a language accessible. The **semantics** must be clear, and the **vocabulary** must be minimal and domain-appropriate.

---

## 5. AI-Friendly Language Design

### MoonBit (2024)
**The first programming language designed from inception for AI-friendliness.**

Presented at LLM4Code workshop at ICSE 2024.

**Design principles**:
- **Flat toplevel structure**: No nesting required for interface implementations
- **Mandatory type signatures**: All toplevel definitions require type annotations
- **KV-Cache optimization**: Flat structure is more KV-cache friendly at all levels (RAG, decoder correction, backtrack)
- **Structural interfaces**: Types implement interfaces by implementing methods (no nested blocks)
- **Smart sampling**: Local sampling ensures syntactic norms; global sampling verifies semantic correctness

**Performance results**:
- Compiles 626 packages in 1.06 seconds (9x faster than Rust compilation)
- Compute time 1/35 of Go
- Significant compilation rate improvement with LLM generation (~3% performance penalty)

**Targets**: WebAssembly and JavaScript backends, with planned native backend.

**Lesson for Sigil**: Grammar design directly impacts LLM code generation quality. Flat, explicit, regular syntax is not just a style preference — it's an engineering requirement for AI-native languages.

### SimPy (ICSE 2024)
Paper: "AI Coders Are Among Us: Rethinking Programming Language Grammar Towards Efficient Code Generation"

**Findings**:
- Introduced SimPy, an AI-friendly Python variant
- Reduced token usage by 13.5% (CodeLlama) and 10.4% (GPT-4)
- Maintained or improved task performance
- Demonstrated that **grammar design directly impacts LLM code generation efficiency**

**Specific optimizations**:
- Removed redundant keywords where context is sufficient
- Simplified block syntax
- Reduced nesting depth
- Made common patterns shorter

### LMQL (LLM Query Language)
```python
"Classify the sentiment of '{text}' as [LABEL]"
where LABEL in ["positive", "negative", "neutral"]
and len(LABEL) < 20
and STOPS_AT(LABEL, '.')
```

- Purpose: Constrained LLM generation with formal constraints
- Uses **grammar-constrained decoding** to ensure valid output
- **Relevance to Sigil**: LMQL's constrained decoding is analogous to using Sigil's PEG grammar to constrain LLM output when generating Sigil code

### SudoLang
A pseudocode language combining natural language expressions with programming constructs for LLM interaction. Demonstrates appetite for NL-style programming in AI contexts.

### Grammar-Constrained Decoding (ACL 2025)
Using formal grammars (including PEGs) to constrain LLM output to syntactically valid programs. Sigil's PEG grammar can be used directly as a decoding constraint — ensuring LLMs only generate valid Sigil code.

### Design Principles for AI-Friendly Languages (Synthesized)

| Principle | Rationale | Sigil Implementation |
|-----------|-----------|---------------------|
| Minimal nesting | Flatter = more predictable generation | Rules are top-level; max 2 levels of nesting |
| Explicit types at boundaries | Reduces hallucination | Required on module exports, neural returns |
| Regular syntax | Efficient tokenization | Consistent `when...then` patterns |
| Small keyword vocabulary | Fewer tokens per construct | ~30 keywords, all common English |
| Grammar-constrained generation | Formal grammar guides decoding | PEG grammar as decoding constraint |
| Deterministic parsing | Unambiguous = reliable generation | PEG (ordered choice) eliminates ambiguity |
| Semantic transparency | Keywords mean what they say | `exceeds`, `is between`, `contains` |

---

## 6. LLM-Interaction Languages vs Sigil

| Language | Purpose | LLM Role | Deterministic? |
|----------|---------|----------|---------------|
| LMQL | Constrain LLM output | Central (generates text) | No |
| DSPy | Optimize LLM pipelines | Central (reasoning) | No |
| Guidance | Template LLM generation | Central (fills templates) | No |
| LangChain | Orchestrate LLM agents | Central (decides actions) | No |
| **Sigil** | Bridge neural↔symbolic | Peripheral (parsing only) | **Yes** |

**The fundamental distinction**: These languages make LLMs *smarter at deciding*. Sigil makes LLMs *unnecessary for deciding* — they only parse.

---

## 7. Program Synthesis Systems

### DreamCoder (PLDI 2021)
- Learns to solve problems by writing programs
- Builds domain-specific languages incrementally through a wake-sleep algorithm
- Alternates: extend language with new symbolic abstractions ↔ train neural guide on imagined problems
- Starts with basic primitives (lambda calculus); learns domain-specific functions

### Active Learning for Neurosymbolic Synthesis (POPL 2025)
- Synthesizes programs with neural components through targeted questions
- Minimizes user interaction by asking only the most informative queries
- Shows that neurosymbolic programs can be learned semi-automatically

### Neurosymbolic Program Synthesis Handbook (2025)
Key approaches surveyed:
1. **Neural-guided search**: Neural networks guide symbolic program search
2. **Differentiable programming**: Programs with learnable neural components
3. **Abstraction learning**: Discovering reusable symbolic building blocks
4. **Interactive synthesis**: Human-in-the-loop program construction
