# Lean 4: The Language of Formal Mathematics and AI-Assisted Theorem Proving

A comprehensive research guide for the Sigil project team.

---

## Table of Contents

1. [What is Lean](#1-what-is-lean)
2. [Why Lean Matters Now](#2-why-lean-matters-now)
3. [Core Concepts](#3-core-concepts)
4. [The Lean Ecosystem](#4-the-lean-ecosystem)
5. [Lean vs Other Proof Assistants](#5-lean-vs-other-proof-assistants)
6. [How to Get Started](#6-how-to-get-started)
7. [Community and Resources](#7-community-and-resources)
8. [Lean for AI Researchers](#8-lean-for-ai-researchers)
9. [Relevance to Sigil](#9-relevance-to-sigil)
10. [Learning Roadmap](#10-learning-roadmap)

---

## 1. What is Lean

### Overview

Lean is simultaneously a **functional programming language** and an **interactive theorem prover** (proof assistant). It enables users to write programs, state mathematical theorems, and construct machine-checked proofs -- all within a single unified system. Unlike most programming languages where the compiler checks syntax and types, Lean's kernel checks the *logical correctness* of proofs against the rules of dependent type theory.

Lean is open-source and hosted on GitHub: [leanprover/lean4](https://github.com/leanprover/lean4).

### History

**Origins at Microsoft Research (2013--2023)**

Leonardo de Moura, a Senior Principal Researcher in the RiSE group at Microsoft Research, launched the Lean project in 2013. Before Lean, de Moura was known for creating **Z3**, the world's most widely-used SMT (Satisfiability Modulo Theories) solver. The first release, Lean 0.1, was announced on June 16, 2014.

**Version Timeline:**

| Version | Release | Key Characteristics |
|---------|---------|---------------------|
| Lean 1 & 2 | 2014--2016 | Experimental. Included HoTT (Homotopy Type Theory) foundations, later dropped. |
| Lean 3 | Jan 2017 | First stable version. Community-written tactic framework in C++. Mathlib started here. |
| Lean 4 | 2021 (stable ~2023) | Complete rewrite. Self-hosting (Lean written in Lean). New compiler producing C code. |

**Lean 4: The Complete Rewrite**

Lean 4 is not an incremental update -- it is a ground-up reimplementation. De Moura and Sebastian Ullrich began the rewrite in 2018 with several radical goals:

- **Self-hosting**: Lean 4 is written in Lean 4 itself, bootstrapping from pre-compiled C code
- **Full extensibility**: Users can modify the parser, elaborator, tactics, decision procedures, pretty printer, and code generator
- **Efficient compilation**: Lean 4 compiles to C code, producing executables that compete with OCaml and GHC in performance
- **Hygienic macro system**: Custom-built for interactive theorem provers (ITPs), replacing the ad-hoc metaprogramming of Lean 3

Lean 4 is **not backwards-compatible** with Lean 3. The entire Mathlib library had to be ported (a massive community effort completed in 2023).

**The Lean FRO (2023--present)**

In July 2023, de Moura and Ullrich launched the **Lean Focused Research Organization (FRO)**, a nonprofit within Convergent Research, with philanthropic support from the Simons Foundation International, the Alfred P. Sloan Foundation, and Richard Merkin. De Moura also joined Amazon Web Services as a Senior Principal Applied Scientist in the Automated Reasoning Group, while continuing to lead Lean development.

The Lean FRO's mission is to make Lean a great **general-purpose programming language** for developing formally verified, production-ready software -- not just a theorem prover.

- Website: [lean-lang.org/fro/about](https://lean-lang.org/fro/about/)
- Roadmap: [lean-lang.org/fro/roadmap](https://lean-lang.org/fro/roadmap/)

### Recognition

In 2025, the **ACM SIGPLAN Programming Languages Software Award** was given to Gabriel Ebner, Soonho Kong, Leonardo de Moura, and Sebastian Ullrich for Lean, cited for its *"significant impact on mathematics, hardware and software verification, and AI."*

---

## 2. Why Lean Matters Now

### Mathlib: The Largest Coherent Mathematical Library Ever Created

As of May 2025, **Mathlib** contains:

- Over **210,000 formalized theorems** and **100,000 definitions**
- **1.9 million lines** of formally verified mathematics
- Written by over **500 contributors**
- Covers undergraduate and graduate-level material across algebra, analysis, topology, number theory, measure theory, category theory, and more

No other formal mathematics library in any proof assistant comes close to Mathlib's scope.

- Repository: [leanprover-community/mathlib4](https://github.com/leanprover-community/mathlib4)
- Documentation: [leanprover-community.github.io/mathlib4_docs](https://leanprover-community.github.io/mathlib4_docs/)
- Overview of mathematics covered: [leanprover-community.github.io/mathlib-overview.html](https://leanprover-community.github.io/mathlib-overview.html)

### Fields Medal-Level Verification

Lean has been used to verify results at the frontier of mathematics:

**Peter Scholze's Liquid Tensor Experiment (2021)**: Fields Medalist Peter Scholze challenged the formalization community to verify a key result in condensed mathematics. A team completed the verification in Lean, confirming the theorem's correctness and demonstrating that proof assistants can handle cutting-edge research mathematics.

**Polynomial Freiman-Ruzsa Conjecture (2023)**: Fields Medalist Terence Tao, together with Yael Dillies and Bhavik Mehta, formalized the proof of the PFR conjecture in Lean 4. The project succeeded in just three weeks, using the Blueprint tool to coordinate the effort. Tao wrote about the experience on his blog: [Formalizing the proof of PFR in Lean4 using Blueprint](https://terrytao.wordpress.com/2023/11/18/formalizing-the-proof-of-pfr-in-lean4-using-blueprint-a-short-tour/).

### AI/ML Community Adoption

Lean has become the **de facto target language** for AI-based mathematical reasoning:

**AlphaProof (Google DeepMind, 2024)**: Couples a pre-trained language model with AlphaZero reinforcement learning. AlphaProof trains itself to prove mathematical statements in Lean. At the 2024 IMO, AlphaProof and AlphaGeometry 2 solved 4 out of 6 problems, achieving silver-medal level. The methodology was published in *Nature* in November 2025.

**Gemini Deep Think (Google DeepMind, 2025)**: An advanced version of Gemini achieved **gold-medal level** at the 2025 IMO, solving 5 out of 6 problems for 35 total points, working end-to-end in natural language within the 4.5-hour competition time limit.

**DeepSeek-Prover-V2 (April 2025)**: An open-source LLM specifically designed for formal theorem proving in Lean 4. The 671B-parameter model achieves 88.9% pass ratio on MiniF2F-test and solved 49 out of 658 PutnamBench problems. Available on HuggingFace:
- [deepseek-ai/DeepSeek-Prover-V2-671B](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V2-671B)
- [deepseek-ai/DeepSeek-Prover-V2-7B](https://huggingface.co/deepseek-ai/DeepSeek-Prover-V2-7B)

**Harmonic AI (2025)**: A startup co-founded by Vlad Tenev (Robinhood co-founder), raised $120M Series C at $1.45B valuation. Their system **Aristotle** generates Lean 4 proofs for its answers and formally verifies them before responding. Achieved gold-medal level on 2025 IMO with **formally verified** solutions.
- Website: [harmonic.fun](https://harmonic.fun/)

### Production Use: Amazon Cedar

AWS uses Lean as the core verification technology behind **Cedar**, the open-source authorization language powering Amazon Verified Permissions and AWS Verified Access:

- Executable formal models are written in Lean alongside production Rust code
- Lean models are approximately **10x smaller** than corresponding Rust production code
- Lean's execution time of 5 microseconds per test case enables millions of differential tests
- The process found and fixed **25 bugs** in Cedar (4 via proofs, 21 via differential testing)
- The Cedar Symbolic Compiler is implemented and **mathematically proven correct** in Lean

Blog post: [Lean Powers Secure Software at AWS](https://lean-lang.org/use-cases/cedar/)

---

## 3. Core Concepts

### 3.1 Dependent Type Theory

Lean's logical foundation is a version of the **Calculus of Inductive Constructions (CIC)**, extended with:

- **Cumulative universes**: An infinite hierarchy `Sort 0 : Sort 1 : Sort 2 : ...` where `Prop := Sort 0` and `Type u := Sort (u + 1)`
- **Inductive families**: Parameterized and indexed inductive types
- **Quotient types**: `Quot(alpha, r)` for set-quotients, from which function extensionality is derived
- **Classical axioms** (optional): Propositional extensionality, axiom of choice (marked `noncomputable`)

In dependent type theory, **types can depend on values**. For example, `Vector n` is a type that depends on the natural number `n` -- a vector of length 3 and a vector of length 5 are different types. This enables the type system to express far richer invariants than conventional type systems (like those in Python, Rust, or Haskell).

```lean
-- A vector of length n
inductive Vector (α : Type) : Nat → Type where
  | nil  : Vector α 0
  | cons : α → Vector α n → Vector α (n + 1)

-- append preserves lengths (the type encodes the proof!)
def append : Vector α m → Vector α n → Vector α (m + n)
  | .nil,       ys => ys
  | .cons x xs, ys => .cons x (append xs ys)
```

Reference: [Dependent Type Theory -- Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/Dependent-Type-Theory/)

### 3.2 Curry-Howard Correspondence: Types as Propositions, Programs as Proofs

The Curry-Howard isomorphism is the deep insight that underlies Lean:

| Logic | Programming |
|-------|-------------|
| Proposition | Type |
| Proof | Term (value) of that type |
| Implication `A -> B` | Function type `A -> B` |
| Conjunction `A /\ B` | Product type `A x B` |
| Disjunction `A \/ B` | Sum type `A + B` |
| Universal `forall x, P x` | Dependent function `(x : A) -> P x` |
| Existential `exists x, P x` | Dependent pair `Sigma (x : A), P x` |

This means **proving a theorem** is literally **writing a program** whose type is the theorem statement. If the program type-checks, the theorem is proved. Lean's kernel (a small, trusted core of ~5,000 lines of C++ code) is the final arbiter.

```lean
-- The proposition: for all natural numbers n, n + 0 = n
theorem add_zero (n : Nat) : n + 0 = n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [Nat.add_succ, ih]

-- "by" enters tactic mode; the proof is a program that constructs
-- a term of type "n + 0 = n"
```

Reference: [Propositions and Proofs -- Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/Propositions-and-Proofs/)

### 3.3 Tactics and Proof Terms

There are two ways to construct proofs in Lean:

**Proof terms** (term-mode): Write the proof expression directly. Explicit, but can be verbose.

```lean
-- Direct proof term
theorem and_comm (p q : Prop) (h : p ∧ q) : q ∧ p :=
  ⟨h.right, h.left⟩
```

**Tactics** (tactic-mode): Interactively transform the proof goal step by step. The `by` keyword enters tactic mode. Tactics are essentially programs that construct proof terms.

```lean
-- Same theorem, proven with tactics
theorem and_comm' (p q : Prop) (h : p ∧ q) : q ∧ p := by
  obtain ⟨hp, hq⟩ := h     -- destruct the conjunction
  exact ⟨hq, hp⟩           -- provide the proof term
```

Common tactics include:
- `intro` -- introduce hypotheses
- `apply` -- apply a lemma to the goal
- `exact` -- provide the exact proof term
- `simp` -- simplification using a database of lemmas
- `ring` -- prove equalities in commutative (semi)rings
- `omega` -- decide linear arithmetic over integers/naturals
- `rfl` -- prove goals of the form `a = a`
- `induction` -- structural induction
- `cases` -- case analysis
- `rw` / `rewrite` -- rewrite using an equality

In Lean 4, **tactics are just Lean programs**. You can write custom tactics in Lean itself, without learning a separate metalanguage.

### 3.4 Inductive Types

Inductive types are the fundamental way to define new data types in Lean. They generalize enums, algebraic data types (ADTs), and recursive types into a single mechanism:

```lean
-- Simple enum
inductive Color where
  | red | green | blue

-- Recursive type (natural numbers)
inductive Nat where
  | zero : Nat
  | succ : Nat → Nat

-- Parameterized type (linked list)
inductive List (α : Type) where
  | nil : List α
  | cons : α → List α → List α

-- Indexed type (length-indexed vectors)
inductive Vector (α : Type) : Nat → Type where
  | nil  : Vector α 0
  | cons : α → Vector α n → Vector α (n + 1)

-- Propositions as inductive types
inductive And (p q : Prop) : Prop where
  | intro : p → q → And p q
```

Lean automatically generates a **recursor** for each inductive type, which serves as both the elimination/pattern matching principle and the induction principle for proofs.

Reference: [Inductive Types -- Lean Reference](https://lean-lang.org/doc/reference/latest/The-Type-System/Inductive-Types/)

### 3.5 Type Classes and Structures

**Structures** are single-constructor inductive types with named fields (analogous to records or structs):

```lean
structure Point where
  x : Float
  y : Float

structure Person where
  name : String
  age : Nat
  deriving Repr    -- auto-derive string representation
```

**Type classes** are structures marked with the `class` keyword. They enable ad-hoc polymorphism (similar to Rust traits or Haskell type classes):

```lean
class Add (α : Type) where
  add : α → α → α

instance : Add Nat where
  add := Nat.add

-- Square brackets request type class inference
def double [Add α] (x : α) : α := Add.add x x
```

Lean 4 uses a **tabled resolution** procedure for type class inference, addressing significant performance problems that existed in Lean 3.

### 3.6 Monadic Programming

Lean 4 is a practical functional programming language with full support for monadic effects:

```lean
-- IO monad for side effects
def main : IO Unit := do
  let name ← IO.getLine
  IO.println s!"Hello, {name.trim}!"

-- Option monad for fallible computation
def safeDivide (x y : Float) : Option Float := do
  if y == 0 then none
  else some (x / y)

-- StateM monad for mutable state
def counter : StateM Nat Nat := do
  let n ← get
  set (n + 1)
  return n
```

Key monadic types in Lean:
- `IO` -- real-world side effects (files, network, console)
- `Option` / `Except` -- failure and error handling
- `StateM` -- mutable state
- `ReaderM` -- read-only environment
- `CoreM`, `MetaM`, `TermElabM`, `TacticM` -- the metaprogramming monad stack

The `do` notation provides imperative-looking syntax for monadic code, including `let ... ←` for binding, `if`/`for`/`while` control flow, and mutable variables (`let mut`).

Reference: [Monads -- Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/Monads/)

### 3.7 Metaprogramming in Lean 4

Lean 4's metaprogramming system is one of its most distinctive features. Unlike Lean 3 (where metaprogramming required C++), or Coq (which uses a separate language called Ltac/Ltac2), Lean 4 metaprogramming is written in Lean 4 itself.

**The Monad Stack:**

| Monad | Access |
|-------|--------|
| `CoreM` | Environment (definitions, theorems, notations) |
| `MetaM` | Metavariable context (unification, type inference) |
| `TermElabM` | Elaboration state (expected types, pending goals) |
| `TacticM` | Current proof goals |

**What you can do with metaprogramming:**
- Define new syntax (notation, custom DSLs)
- Write custom tactics
- Build elaboration rules
- Create code generators
- Implement decision procedures
- Modify the pretty printer

```lean
-- Define custom notation
notation "⟪" a ", " b "⟫" => (a, b)

-- Define a custom tactic using macro
macro "trivial_and" : tactic =>
  `(tactic| constructor <;> assumption)

-- Elaborate-time computation
elab "#check_type " t:term : command => do
  let e ← Lean.Elab.Term.elabTerm t none
  let ty ← Lean.Meta.inferType e
  Lean.logInfo m!"Type: {ty}"
```

Reference: [Metaprogramming in Lean 4 (book)](https://leanprover-community.github.io/lean4-metaprogramming-book/)

---

## 4. The Lean Ecosystem

### 4.1 Mathlib4

Mathlib is the community-maintained mathematical library for Lean 4.

**Scope**: Covers a vast range of mathematics including:
- Abstract algebra (groups, rings, fields, modules, Galois theory)
- Analysis (real, complex, functional, measure theory)
- Topology (general, algebraic)
- Number theory (algebraic, analytic)
- Category theory
- Combinatorics
- Order theory and lattices
- Linear algebra
- Probability theory

**Contribution model**: Open-source with a maintainer/reviewer structure. As of 2025, the review queue has ~300 pending pull requests with median wait times of two weeks. The newly-formed **Mathlib Initiative** (October 2025) is establishing a professional editorial team to achieve <1 week review response times by September 2026.

- Repository: [github.com/leanprover-community/mathlib4](https://github.com/leanprover-community/mathlib4)
- Roadmap: [mathlib-initiative.org/roadmap](https://mathlib-initiative.org/roadmap/)

### 4.2 Lake (Build System)

**Lake** (Lean + Make) is Lean 4's build system and package manager, analogous to Cargo (Rust) or Stack (Haskell).

```bash
# Create a new project
lake init MyProject

# Build the project
lake build

# Run the project executable
lake exe MyProject

# Add a dependency (in lakefile.lean)
require mathlib from git
  "https://github.com/leanprover-community/mathlib4"
```

Lake configuration is written in Lean itself (`lakefile.lean`), so your build configuration is a type-checked Lean program.

### 4.3 VS Code Extension

The **Lean 4 VS Code extension** ([marketplace link](https://marketplace.visualstudio.com/items?itemName=leanprover.lean4)) is the primary development interface:

- Real-time type checking and error reporting
- **Infoview panel**: Shows the current proof state (goals, hypotheses, types) as you write
- Go-to-definition, hover info, autocomplete
- Lake integration (project creation, building, dependency management)
- Widgets for interactive exploration

Installation: The recommended way to install Lean is through VS Code. The extension manages Lean versions via `elan` (Lean's toolchain manager, analogous to `rustup`).

Source: [github.com/leanprover/vscode-lean4](https://github.com/leanprover/vscode-lean4)

### 4.4 Lean REPL

The community REPL allows interactive evaluation of Lean code:

```bash
lake exe repl
```

The REPL communicates via JSON on stdin/stdout, supporting both "command" mode (definitions, theorems) and "tactic" mode (interactive proofs). This JSON interface makes it particularly useful as a backend for AI systems.

Source: [github.com/leanprover-community/repl](https://github.com/leanprover-community/repl)

### 4.5 LeanDojo

LeanDojo is an open-source framework that provides a **machine learning interface** to Lean:

- **Repository tracing**: Extracts training data from Lean repositories (theorems, proofs, tactic steps, premise usage)
- **Benchmark**: LeanDojo Benchmark 4 contains 122,517 theorems/proofs, 259,580 tactics, and 167,779 premises from Mathlib4
- **ReProver**: A retrieval-augmented LLM prover that retrieves relevant premises from Mathlib and generates tactics
- **Lifelong learning**: LeanAgent (ICLR 2025) enables AI provers to learn continually from new theorems

LeanDojo discovered novel proofs: 33 new proofs in miniF2F and 39 in ProofNet for theorems that previously had no Lean proof.

- Website: [leandojo.org](https://leandojo.org/)
- Paper: [LeanDojo: Theorem Proving with Retrieval-Augmented Language Models (NeurIPS 2023)](https://arxiv.org/abs/2306.15626)
- GitHub: [github.com/lean-dojo](https://github.com/lean-dojo)
- Documentation: [leandojo.readthedocs.io](https://leandojo.readthedocs.io/)

### 4.6 Blueprint

**leanblueprint** is a tool that generates dependency graphs and progress tracking for Lean formalization projects:

- Write a LaTeX blueprint describing the mathematical structure of a proof
- Mark dependencies between definitions, lemmas, and theorems
- Track which parts have been formalized in Lean
- Automatically generate HTML with an interactive dependency graph
- Used by Terence Tao's PFR project and many other large formalization efforts

```bash
pip install leanblueprint
leanblueprint serve    # Local preview
leanblueprint pdf      # Build PDF
leanblueprint checkdecls  # Verify declarations exist in Lean project
```

Source: [github.com/PatrickMassot/leanblueprint](https://github.com/PatrickMassot/leanblueprint)

### 4.7 Reservoir

**Reservoir** is the Lean 4 package registry, analogous to crates.io (Rust) or PyPI (Python):
- [reservoir.lean-lang.org](https://reservoir.lean-lang.org/)

---

## 5. Lean vs Other Proof Assistants

### Comparison Matrix

| Feature | Lean 4 | Coq | Isabelle/HOL | Agda |
|---------|--------|-----|--------------|------|
| **Foundation** | CIC + quotients | CIC | Simple type theory (HOL) | Martin-Lof type theory |
| **Dependent types** | Yes | Yes | No | Yes |
| **Proof automation** | Good (simp, omega, aesop) | Good (auto, omega, Ltac) | Excellent (Sledgehammer) | Minimal |
| **Math library** | Mathlib (1.9M lines) | MathComp (~500K lines) | AFP (large, diverse) | Small standard library |
| **Programming language** | Yes (compiles to C) | Limited (extraction to OCaml/Haskell) | Code generation available | Yes (compiles to Haskell) |
| **Performance** | Fast (native C output) | Moderate | Moderate | Moderate |
| **Metaprogramming** | In Lean itself | Ltac/Ltac2 (separate languages) | Eisbach, ML plugins | Reflection |
| **IDE support** | VS Code (excellent) | VS Code, CoqIDE | Isabelle/jEdit (excellent) | VS Code, Emacs |
| **Industry use** | AWS (Cedar), Harmonic | CompCert (verified C compiler) | seL4 (verified microkernel) | Rare |
| **AI integration** | Strong (LeanDojo, AlphaProof) | Growing (CoqGPT) | Limited | Minimal |
| **Self-hosting** | Yes | No | No | Partially |

### Strengths by System

**Lean 4 is best for:**
- Mathematics formalization (Mathlib is unmatched)
- AI-assisted theorem proving (de facto standard target)
- Writing verified programs that need to be fast
- Projects where extensibility and custom tactics matter
- People who want one language for both programming and proving

**Coq is best for:**
- Industrial software verification (CompCert, CertiKOS)
- Program extraction (generate certified OCaml/Haskell code)
- Mature ecosystem with decades of libraries
- Teams already invested in Coq infrastructure

**Isabelle/HOL is best for:**
- Systems and hardware verification (seL4, CakeML)
- Proofs requiring heavy automation (Sledgehammer is unmatched for calling external ATPs)
- Simple type theory (easier foundation, no universe management)
- Large Archive of Formal Proofs (AFP)

**Agda is best for:**
- Research in type theory and constructive mathematics
- Cubical type theory and homotopy type theory
- People who prefer term-mode proofs (no tactic system)
- Programming language research

### Key Differentiator for Lean

Lean 4 compiles to C and runs fast -- not "fast for a theorem prover" but actually fast. You can write command-line tools, build systems, even games. No other proof assistant offers this combination of proving power and practical programming performance.

Reference: [From Zero to QED: An informal introduction to formality](https://sdiehl.github.io/zero-to-qed/03_theorem_provers.html)

---

## 6. How to Get Started

### Installation

The recommended approach uses the **VS Code extension**, which manages everything:

1. Install [VS Code](https://code.visualstudio.com/)
2. Install the [Lean 4 extension](https://marketplace.visualstudio.com/items?itemName=leanprover.lean4)
3. The extension prompts to install `elan` (the Lean toolchain manager) and the latest stable Lean
4. Create a project: `lake init MyFirstProject` or use VS Code's project creation

Manual installation (for terminal users):

```bash
# Install elan (Lean's rustup equivalent)
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh

# Verify installation
lean --version
lake --version

# Create a new project
lake init MyProject
cd MyProject
lake build
```

Full instructions: [lean-lang.org/install](https://lean-lang.org/install/)

### First Proofs

After installation, try this in a `.lean` file with VS Code:

```lean
-- Your first theorem
theorem my_first_proof : 1 + 1 = 2 := by
  rfl   -- "reflexivity" -- both sides evaluate to 2

-- A slightly harder one
theorem add_comm_example : ∀ (a b : Nat), a + b = b + a := by
  intro a b
  omega   -- omega decides linear arithmetic

-- Define a function and prove something about it
def double (n : Nat) : Nat := 2 * n

theorem double_is_add_self (n : Nat) : double n = n + n := by
  unfold double
  omega
```

The VS Code Infoview panel (on the right) shows the current proof state as you type each tactic.

### Recommended Learning Path

#### For Complete Beginners (No Lean or Proof Background)

**1. Natural Number Game** -- [adam.math.hhu.de/~game/nng4](https://adam.math.hhu.de/#/g/leanprover-community/NNG4)
- Browser-based, no installation needed
- Gamified introduction to proofs through building natural number theory
- Start here: prove that `2 + 2 = 4`, then prove `x + y = y + x`
- Takes 5--15 hours depending on background
- Source: [github.com/leanprover-community/NNG4](https://github.com/leanprover-community/NNG4)

**2. The Mechanics of Proof** by Heather Macbeth
- Gentlest introduction for those with less math background
- Originally a companion text for Math2001 at Fordham University
- Teaches mathematical reasoning through Lean with exercises

#### For Programmers (Know Python/Rust, New to Theorem Proving)

**3. Functional Programming in Lean** by David Thrane Christiansen
- [lean-lang.org/functional_programming_in_lean](https://lean-lang.org/functional_programming_in_lean/)
- Assumes programming background but no FP knowledge
- Covers: types, pattern matching, type classes, monads, monad transformers, do-notation
- Free (Creative Commons), by the former Lean FRO executive director
- This is the main resource if you want to use Lean **as a programming language**

**4. Theorem Proving in Lean 4** by Jeremy Avigad, Leonardo de Moura, Soonho Kong, Sebastian Ullrich
- [lean-lang.org/theorem_proving_in_lean4](https://lean-lang.org/theorem_proving_in_lean4/)
- The definitive reference for Lean's type theory
- Covers dependent type theory, propositions and proofs, tactics, inductive types, type classes, axioms
- More theoretical than FPIL -- read this to understand the foundations

#### For Mathematicians

**5. Mathematics in Lean** by Jeremy Avigad and Patrick Massot
- [leanprover-community.github.io/mathematics_in_lean](https://leanprover-community.github.io/mathematics_in_lean/C01_Introduction.html)
- Tactic-based theorem proving using Mathlib
- Covers: logic, sets, functions, topology, algebra, analysis
- Interactive with exercises in VS Code
- The main resource for learning to formalize mathematics

#### For Computer Scientists

**6. The Hitchhiker's Guide to Logical Verification** by Baanen, Bentkamp, Blanchette, Holzl, Limperg
- [browncs1951x.github.io/static/files/hitchhikersguide.pdf](https://browncs1951x.github.io/static/files/hitchhikersguide.pdf)
- Programming and verification oriented
- Covers Lean's type theory, operational semantics, Hoare logic, denotational semantics
- Includes associated VS Code exercises

#### All Resources in One Place

- [lean-lang.org/learn](https://lean-lang.org/learn/) -- Official learning page
- [leanprover-community.github.io/learn.html](https://leanprover-community.github.io/learn.html) -- Community learning page
- [All Lean Books and Where to Find Them](https://lakesare.brick.do/all-lean-books-and-where-to-find-them-x2nYwjM3AwBQ) -- Comprehensive list

---

## 7. Community and Resources

### Lean Zulip Chat

The **Lean Zulip** is the central community hub:
- [leanprover.zulipchat.com](https://leanprover.zulipchat.com/)
- Key streams: `#new members` (beginner questions), `#general`, `#mathlib4`, `#lean4`
- Extremely welcoming to beginners
- Searchable archive: [leanprover-community.github.io/archive](https://leanprover-community.github.io/archive/)

Case study on why Lean chose Zulip: [zulip.com/case-studies/lean](https://zulip.com/case-studies/lean/)

### GitHub Repositories

| Repository | Purpose |
|------------|---------|
| [leanprover/lean4](https://github.com/leanprover/lean4) | Lean 4 compiler and standard library (~7,500 stars) |
| [leanprover-community/mathlib4](https://github.com/leanprover-community/mathlib4) | The math library |
| [leanprover/vscode-lean4](https://github.com/leanprover/vscode-lean4) | VS Code extension |
| [leanprover/theorem_proving_in_lean4](https://github.com/leanprover/theorem_proving_in_lean4) | TPIL textbook source |
| [leanprover/fp-lean](https://github.com/leanprover/fp-lean) | FPIL textbook source |
| [lean-dojo/ReProver](https://github.com/lean-dojo/ReProver) | AI theorem prover |
| [deepseek-ai/DeepSeek-Prover-V2](https://github.com/deepseek-ai/DeepSeek-Prover-V2) | DeepSeek's theorem prover |

### Conferences and Events

**Lean Together** -- Annual community conference:
- [Lean Together 2025](https://leanprover-community.github.io/lt2025/) -- Virtual, January 2025
- [Lean Together 2026](https://leanprover-community.github.io/lt2026/) -- Virtual via Zoom, January 19--23, 2026

**Leaning In! 2026** -- Berlin, March 12, 2026

**Summer Schools (2026)**:
- Summer School on Formalization in Lean -- Pittsburgh, July 7--18, 2026
- Lean for the Curious Mathematician 2026 -- Cortona, Italy, September 7--11, 2026

Full events list: [leanprover-community.github.io/events.html](https://leanprover-community.github.io/events.html)

### Key Papers

| Paper | Venue | Topic |
|-------|-------|-------|
| [The Lean 4 Theorem Prover and Programming Language](https://lean-lang.org/papers/lean4.pdf) | CADE 2021 | System description |
| [LeanDojo: Theorem Proving with Retrieval-Augmented LMs](https://arxiv.org/abs/2306.15626) | NeurIPS 2023 | ML-based proving |
| [AlphaProof: Olympiad-level formal mathematical reasoning with RL](https://www.nature.com/articles/s41586-025-09833-y) | Nature 2025 | RL for theorem proving |
| [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801) | arXiv 2025 | LLM-based proving |
| [Lean4Lean: Verifying a Typechecker for Lean, in Lean](https://arxiv.org/pdf/2403.14064) | 2024 | Self-verification |

---

## 8. Lean for AI Researchers

### The AI-Theorem Proving Pipeline

The typical pipeline for AI-assisted theorem proving in Lean:

```
Training Data (Mathlib proofs)
    ↓
Extract tactic-level data (LeanDojo tracing)
    ↓
Fine-tune language model (ReProver, DeepSeek-Prover)
    ↓
Proof search at inference time:
    ├── Model generates candidate tactic
    ├── Lean kernel checks the tactic
    ├── If valid: advance to next goal
    └── If invalid: backtrack and try another tactic
    ↓
Complete proof (all goals closed)
```

### LeanDojo / ReProver Pipeline

**Data extraction**: LeanDojo traces Lean repositories, extracting:
- Theorem statements and their proofs
- Individual tactic steps with before/after proof states
- Premise usage (which lemmas/definitions are cited)

**Training**: ReProver is an encoder-decoder Transformer trained on this data. Given a proof state, it:
1. Retrieves relevant premises from Mathlib (using a learned retrieval model)
2. Concatenates the state with retrieved premises
3. Generates the next tactic

**Search**: At inference time, ReProver uses best-first search over the tactic tree, with the Lean kernel providing ground-truth verification at each step.

### Why Lean (Not Coq or Isabelle) for AI

1. **Mathlib's scale**: 210K+ theorems provide far more training data than any other formal library
2. **Tactic-mode proofs**: Most Mathlib proofs use tactics, which decompose into small, learnable steps
3. **JSON REPL**: The Lean REPL's JSON interface makes programmatic interaction straightforward
4. **Self-contained verification**: Lean's kernel provides a definitive true/false signal for each proof step
5. **Community investment**: LeanDojo, AlphaProof, DeepSeek-Prover, Harmonic all target Lean
6. **Active development**: The Lean FRO is actively improving the language for AI use cases

### Key AI Systems Targeting Lean

| System | Organization | Approach | Key Result |
|--------|-------------|----------|------------|
| AlphaProof | Google DeepMind | RL + AlphaZero | IMO 2024 silver medal |
| Gemini Deep Think | Google DeepMind | End-to-end LLM | IMO 2025 gold medal |
| DeepSeek-Prover-V2 | DeepSeek | Subgoal decomposition + RL | 88.9% on MiniF2F |
| Aristotle | Harmonic | Formal verification of answers | IMO 2025 gold (verified) |
| ReProver | LeanDojo team | Retrieval-augmented LM | 33 new proofs in MiniF2F |
| LeanAgent | LeanDojo team | Lifelong learning | ICLR 2025 |
| Safe | Research framework | CoT step verification | Verifies each reasoning step |

### Benchmarks

- **MiniF2F**: 488 math competition problems formalized in Lean (and other provers). The standard benchmark.
- **ProofNet**: Undergraduate math problems formalized in Lean.
- **PutnamBench**: 658 Putnam competition problems. Very challenging.
- **ProverBench**: 325 problems introduced by DeepSeek (includes 15 AIME problems).

---

## 9. Relevance to Sigil

### What Sigil Can Learn from Lean's Design

Lean and Sigil operate in different domains -- Lean is a theorem prover for mathematics, Sigil is a neuro-symbolic language for decision systems -- but several of Lean's architectural ideas are deeply relevant.

### 9.1 Lean's Tactic System as Inspiration for Sigil's Rule Evaluation

**Lean's approach**: Tactics are small, composable programs that transform proof states. Each tactic takes a goal (what needs to be proved) and produces zero or more subgoals. The system chains tactics until all goals are closed.

**Sigil parallel**: Sigil's rule evaluation engine works similarly -- rules have conditions (goals) and actions (transformations). Forward chaining iterates until a fixed point; backward chaining decomposes goals into subgoals.

**What to borrow**:
- Lean's tactic combinators (`<;>`, `repeat`, `try`, `first`) could inspire Sigil rule composition operators
- Lean's "proof state" display (showing current goals and hypotheses) is analogous to Sigil's execution traces showing which conditions are met/unmet
- Lean's tactic timeout and depth limits mirror Sigil's max iteration (100) and max depth (50) limits
- The idea that tactics are *programs* (not just declarations) suggests that Sigil rules could eventually be first-class values that can be composed, stored, and passed around

### 9.2 Dependent Types as a Model for Sigil's Gradual Type System Evolution

**Lean's approach**: Types can express arbitrary invariants. `Vector Nat 5` is not just "a list of numbers" but "a list of exactly 5 numbers." The type checker enforces these at compile time.

**Sigil's current state**: Gradual typing with optional annotations. Types are checked but do not block execution.

**What to borrow**:
- Lean's universe hierarchy (`Type 0 : Type 1 : Type 2`) is a clean way to handle types-of-types, which Sigil might need as its type system matures
- Lean's `Prop` universe (propositions that are erased at runtime) could inspire Sigil's "constraint types" -- types that exist for checking but have no runtime cost
- The progression from simple types to dependent types could guide Sigil's type system roadmap: start with `Number`, `Text`, `Symbol`, then add refinement types (`Number where > 0`), then dependent record types (`Record where age > 18`)
- Lean's approach to optional classical axioms (marked `noncomputable`) is analogous to how Sigil marks neural computations with the `neural` keyword -- both flag non-deterministic/non-computational elements

### 9.3 Lean's Proof Terms as Inspiration for Sigil's Execution Traces

**Lean's approach**: Every tactic proof is elaborated into a **proof term** -- a complete, machine-checkable witness of the proof. The proof term is the fundamental object; tactics are just a convenient way to construct it.

**Sigil parallel**: Sigil's execution traces record every rule evaluation, condition check, and action taken. The trace is a fundamental output, not debugging.

**What to borrow**:
- Lean's proof terms are *replayable* -- given the term, you can re-verify the proof without re-running tactics. Sigil traces should similarly be replayable: given the trace and input data, you should be able to re-derive the decision
- Lean's structured proof terms (with explicit references to which lemmas were used) map to Sigil traces recording which rules fired and why
- Lean's "sorry" (an axiom that marks an incomplete proof) could inspire a Sigil trace marker for "decision made with incomplete information" or "neural confidence below threshold"
- Lean's Lean4Lean project (verifying the type checker in Lean itself) suggests the ultimate goal: Sigil could eventually verify its own rule engine's correctness

### 9.4 Formal Verification Concepts for Sigil's Symbolic Engine

**Lean's approach**: The kernel is a small, trusted core (~5,000 lines of C++) that checks everything. All the complex machinery (tactics, elaboration, metaprogramming) ultimately produces terms that must pass through this tiny trusted core.

**Sigil parallel**: Sigil's symbolic engine should have a similar "trusted core" property -- a small, well-tested kernel that all decisions pass through.

**What to borrow**:
- The **small trusted kernel** principle: Sigil's rule evaluator should be the smallest possible trusted core, with everything else (parsing, type checking, FFI) being untrusted elaboration
- **Verification-guided development** (AWS Cedar model): Write a formal specification alongside the implementation, then test that they agree. Sigil could use property-based testing to approximate this
- **Proof irrelevance**: In Lean, `Prop` values are erased at runtime because only their existence matters, not their content. Sigil traces could adopt a similar idea -- some trace details are for auditing only and can be dropped for performance
- Lean's **quotient types** (identifying values by an equivalence relation) could inspire Sigil's handling of record equality and pattern matching -- when are two records "the same" for rule evaluation purposes?

### 9.5 Summary Table

| Lean Concept | Sigil Analog | Inspiration |
|-------------|-------------|-------------|
| Tactic | Rule action | Composable, chainable transformations |
| Proof state | Rule evaluation state | Goals, hypotheses, environment |
| Proof term | Execution trace | Complete, replayable witness |
| Kernel | Symbolic engine core | Small trusted base |
| `sorry` | Neural fallback | Explicitly marked incompleteness |
| `Prop` (erased) | Trace metadata | Exists for auditing, erased for performance |
| `noncomputable` | `neural` keyword | Marks non-deterministic elements |
| Type class | Rule priority/dispatch | Ad-hoc behavior selection |
| Dependent type | Refinement type (future) | Types that depend on values |

---

## 10. Learning Roadmap

A week-by-week plan for learning Lean 4, designed for someone who knows Python and Rust but is new to dependent type theory and theorem proving.

### Prerequisites

- Comfortable reading Python and Rust code
- Basic discrete math (sets, functions, induction) helpful but not required
- VS Code installed

### Phase 1: Foundations (Weeks 1--3)

**Week 1: First Contact**
- Install Lean via VS Code extension ([lean-lang.org/install](https://lean-lang.org/install/))
- Play the **Natural Number Game** ([adam.math.hhu.de/#/g/leanprover-community/NNG4](https://adam.math.hhu.de/#/g/leanprover-community/NNG4))
  - Complete at least the first 4 worlds (Tutorial, Addition, Multiplication, Power)
  - Goal: internalize `rfl`, `rw`, `induction`, `apply`
- Read: FPIL Chapter 1 (Getting to Know Lean) -- [lean-lang.org/functional_programming_in_lean](https://lean-lang.org/functional_programming_in_lean/)
- Time: ~8 hours

**Week 2: Lean as a Programming Language**
- Read FPIL Chapters 2--4 (Hello World, Interlude, Overloading and Type Classes)
- Exercises: Implement basic data structures (stack, queue, binary tree) in Lean
- Get comfortable with: pattern matching, recursive functions, `do` notation, type classes
- Create a small project with `lake init` and build it
- Time: ~10 hours

**Week 3: The Type System**
- Read TPIL Chapters 1--4 (Introduction, Dependent Type Theory, Propositions and Proofs, Quantifiers and Equality)
- [lean-lang.org/theorem_proving_in_lean4](https://lean-lang.org/theorem_proving_in_lean4/)
- Key concepts: `Prop` vs `Type`, `Eq`, universal/existential quantification
- Try proving simple theorems in term mode and tactic mode
- Time: ~10 hours

### Phase 2: Building Fluency (Weeks 4--6)

**Week 4: Tactics Deep Dive**
- Read TPIL Chapters 5--7 (Tactics, Interacting with Lean, Inductive Types)
- Practice: Prove 10 simple theorems using only tactics (`intro`, `apply`, `exact`, `cases`, `induction`, `simp`, `omega`, `rfl`, `rw`)
- Understand the Infoview panel workflow: read the goal, choose a tactic, see the goal change
- Time: ~10 hours

**Week 5: Inductive Types and Structures**
- Read TPIL Chapters 7--8 (Inductive Types, Structures and Records) in depth
- Implement an arithmetic expression evaluator in Lean (a familiar exercise for language designers)
- Define `Expr` as an inductive type, write an `eval` function, prove properties about it
- Time: ~10 hours

**Week 6: Monads and Effects**
- Read FPIL Chapters 5--8 (Monads, Functors and Friends, Monad Transformers, IO)
- Build a small CLI tool in Lean (file reader, calculator, or similar)
- Understand `IO`, `Option`, `Except`, `StateM`, and `do` notation
- Time: ~10 hours

### Phase 3: Mathematics (Weeks 7--9)

**Week 7: Mathematics in Lean -- Basics**
- Start MIL Chapters 1--3 (Basics, Proving Identities, Logic)
- [leanprover-community.github.io/mathematics_in_lean](https://leanprover-community.github.io/mathematics_in_lean/C01_Introduction.html)
- Set up a project with Mathlib as a dependency
- Get comfortable using `simp`, `ring`, `linarith`, `norm_num`
- Time: ~10 hours

**Week 8: Mathematics in Lean -- Algebra and Analysis**
- MIL Chapters 4--6 (Sets and Functions, Topology, Structures)
- Focus on whichever area interests you most
- Try formalizing a simple result you know from math classes
- Time: ~10 hours

**Week 9: Contributing to Mathlib (Optional)**
- Read the Mathlib contribution guide
- Find a "good first issue" on the Mathlib4 GitHub
- Or: formalize a small result that interests you and submit a PR
- Time: ~10 hours

### Phase 4: Advanced Topics (Weeks 10--12)

**Week 10: Metaprogramming**
- Read the [Metaprogramming in Lean 4 book](https://leanprover-community.github.io/lean4-metaprogramming-book/)
- Write a custom tactic (even a simple one like "apply commutativity")
- Write a custom notation or syntax extension
- Understand `Syntax`, `Expr`, `MetaM`, `TacticM`
- Time: ~12 hours

**Week 11: Verification and Formal Methods**
- Study the [Hitchhiker's Guide to Logical Verification](https://browncs1951x.github.io/static/files/hitchhikersguide.pdf) Chapters 1--5
- Topics: operational semantics, Hoare logic, program verification
- Verify a simple program (sorting, search, or similar)
- Time: ~12 hours

**Week 12: AI + Lean**
- Set up [LeanDojo](https://leandojo.readthedocs.io/) and run ReProver on a few theorems
- Study how LeanDojo extracts training data from Lean repositories
- Read the LeanDojo paper ([arxiv.org/abs/2306.15626](https://arxiv.org/abs/2306.15626))
- Experiment with using an LLM to generate Lean proofs via the REPL
- Time: ~12 hours

### Ongoing Practice

- **Daily**: Solve one problem on the Natural Number Game or a Lean exercise
- **Weekly**: Formalize one small theorem or implement one small program
- **Monthly**: Read one Lean-related paper from the key papers list
- **Community**: Join the Lean Zulip, ask questions, help others

### Total Time Estimate

- Phase 1 (Weeks 1--3): ~28 hours
- Phase 2 (Weeks 4--6): ~30 hours
- Phase 3 (Weeks 7--9): ~30 hours
- Phase 4 (Weeks 10--12): ~36 hours
- **Total: ~124 hours over 12 weeks (~10 hours/week)**

---

## References and Links

### Official Resources
- Lean Language: [lean-lang.org](https://lean-lang.org/)
- Lean FRO: [lean-lang.org/fro/about](https://lean-lang.org/fro/about/)
- Lean GitHub: [github.com/leanprover/lean4](https://github.com/leanprover/lean4)
- Lean Reference Manual: [lean-lang.org/doc/reference/latest](https://lean-lang.org/doc/reference/latest/Introduction/)

### Textbooks (Free)
- Functional Programming in Lean: [lean-lang.org/functional_programming_in_lean](https://lean-lang.org/functional_programming_in_lean/)
- Theorem Proving in Lean 4: [lean-lang.org/theorem_proving_in_lean4](https://lean-lang.org/theorem_proving_in_lean4/)
- Mathematics in Lean: [leanprover-community.github.io/mathematics_in_lean](https://leanprover-community.github.io/mathematics_in_lean/C01_Introduction.html)
- Metaprogramming in Lean 4: [leanprover-community.github.io/lean4-metaprogramming-book](https://leanprover-community.github.io/lean4-metaprogramming-book/)
- The Hitchhiker's Guide to Logical Verification: [browncs1951x.github.io](https://browncs1951x.github.io/static/files/hitchhikersguide.pdf)

### Community
- Lean Zulip: [leanprover.zulipchat.com](https://leanprover.zulipchat.com/)
- Lean Community: [leanprover-community.github.io](https://leanprover-community.github.io/)
- Lean Events: [leanprover-community.github.io/events.html](https://leanprover-community.github.io/events.html)

### AI / ML Integration
- LeanDojo: [leandojo.org](https://leandojo.org/)
- ReProver: [github.com/lean-dojo/ReProver](https://github.com/lean-dojo/ReProver)
- DeepSeek-Prover-V2: [github.com/deepseek-ai/DeepSeek-Prover-V2](https://github.com/deepseek-ai/DeepSeek-Prover-V2)
- AlphaProof (Nature): [nature.com/articles/s41586-025-09833-y](https://www.nature.com/articles/s41586-025-09833-y)

### Tools
- VS Code Extension: [marketplace.visualstudio.com/items?itemName=leanprover.lean4](https://marketplace.visualstudio.com/items?itemName=leanprover.lean4)
- Lean REPL: [github.com/leanprover-community/repl](https://github.com/leanprover-community/repl)
- leanblueprint: [github.com/PatrickMassot/leanblueprint](https://github.com/PatrickMassot/leanblueprint)
- Reservoir (package registry): [reservoir.lean-lang.org](https://reservoir.lean-lang.org/)

---

*Research compiled March 2026 for the Sigil language project.*
