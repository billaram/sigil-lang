# AI-Assisted Theorem Proving: A Comprehensive Guide

> From classical ATP to neural provers solving IMO problems -- the convergence of
> machine learning and formal mathematics, and why it matters for neuro-symbolic AI.

**Last updated**: March 2026

---

## Table of Contents

1. [What Is AI-Assisted Theorem Proving](#1-what-is-ai-assisted-theorem-proving)
2. [Formal Proof Assistants](#2-formal-proof-assistants)
3. [Key Systems and Tools](#3-key-systems-and-tools)
4. [Techniques](#4-techniques)
5. [Key Papers](#5-key-papers-chronological)
6. [Competitions and Benchmarks](#6-competitions-and-benchmarks)
7. [Industry vs Academia](#7-industry-vs-academia)
8. [Relevance to Neuro-Symbolic AI](#8-relevance-to-neuro-symbolic-ai)
9. [Relevance to Sigil](#9-relevance-to-sigil)
10. [Learning Path](#10-learning-path)
11. [Open Problems](#11-open-problems)

---

## 1. What Is AI-Assisted Theorem Proving

### Definition

AI-assisted theorem proving is the research area at the intersection of artificial intelligence and formal mathematics. It encompasses building systems that can automatically discover, construct, or assist humans in writing machine-checkable mathematical proofs. Unlike informal mathematical reasoning (writing proofs on paper), these systems operate within **formal proof assistants** -- software environments where every logical step is verified by a trusted kernel, guaranteeing absolute correctness.

The field sits at the confluence of three traditions:

- **Automated Theorem Proving (ATP)** -- fully automatic provers for first-order logic (E, Vampire, Z3)
- **Interactive Theorem Proving (ITP)** -- human-guided proof construction in systems like Lean, Coq, and Isabelle
- **Machine Learning for Mathematics** -- using neural networks to guide, accelerate, or automate proof search

### A Brief History

**1950s-1960s: The Dawn of ATP.**
The idea of mechanized proof goes back to Leibniz, but practical work began in the 1950s. The Logic Theorist (Newell, Shaw, Simon, 1956) proved 38 of the first 52 theorems in Whitehead and Russell's *Principia Mathematica*. In 1960, Davis and Putnam developed procedures for propositional satisfiability. The critical breakthrough came in 1965 when **J. Alan Robinson** introduced the **resolution principle** with syntactic unification, eliminating the combinatorial explosion of earlier Herbrand-based methods. This single inference rule became the foundation of automated deduction for decades.

**1970s-1990s: Interactive Proof Assistants Emerge.**
Recognizing that fully automatic provers hit walls on complex theorems, researchers built interactive systems where humans guide the proof while the computer checks each step. Mizar (1973), Nqthm/ACL2 (Boyer-Moore, 1970s), Coq (1984, based on the Calculus of Constructions), Isabelle (1986, Paulson), and HOL (1988, Gordon) all emerged in this era. The emphasis was on trustworthiness: a small, verified kernel checks all proofs.

**2000s-2010s: Hammers and Machine Learning.**
"Hammer" tools like Sledgehammer (Isabelle) and CoqHammer learned to select relevant premises from large libraries and dispatch proof obligations to external ATPs. Early machine learning work applied k-nearest neighbors and gradient-boosted trees to premise selection. The DeepMath project (Alemi et al., 2016) was among the first to apply deep learning to premise selection in formal mathematics.

**2019-2021: The Neural Prover Revolution Begins.**
GamePad (Huang et al., 2019) and HOList (Bansal et al., 2019) created environments for ML interaction with proof assistants. GPT-f (Polu & Sutskever, 2020) demonstrated that large language models could generate proofs in Metamath, contributing 23 shortened proofs accepted into the main library. TacticZero (Wu et al., 2021) showed reinforcement learning could learn theorem proving from scratch in HOL4.

**2022-2024: Scaling Up.**
HyperTree Proof Search (Lample et al., 2022) from Meta AI solved 5x more IMO problems than previous systems. Draft, Sketch, and Prove (Jiang et al., 2023) bridged informal and formal proofs. LeanDojo (Yang et al., 2023) opened Lean to ML research. AlphaProof (DeepMind, 2024) earned a silver medal at the International Mathematical Olympiad with formally verified proofs -- a watershed moment.

**2025-2026: The Current Frontier.**
Multiple systems now achieve gold-medal-level IMO performance. Goedel-Prover-V2 reaches 90.4% on miniF2F. AxiomProver solved 12/12 Putnam 2025 problems autonomously. The Gauss agent formalized the strong Prime Number Theorem in 3 weeks -- work that took human experts 18+ months. AI-assisted theorem proving has gone from a niche curiosity to a central research direction in AI.

### Why It Is Hard

Theorem proving is one of the hardest problems in computer science for several compounding reasons:

1. **Combinatorial explosion**: The search space of possible proof steps grows exponentially. A proof of 50 steps where each step has 100 possible tactics yields 100^50 candidate proofs.
2. **Creativity requirement**: Many proofs require introducing auxiliary constructions, lemmas, or definitions that do not appear in the problem statement. This is analogous to the "term generation" problem that motivated GPT-f.
3. **Long-horizon reasoning**: Unlike game-playing (where reward signals come every move), a proof attempt provides no intermediate reward until it either succeeds or fails.
4. **Sparse reward**: Most proof attempts fail completely, providing no gradient signal for learning.
5. **Domain breadth**: Mathematics spans algebra, analysis, topology, combinatorics, number theory, and more -- each with its own idioms, techniques, and libraries.
6. **Formalization gap**: Translating human mathematical intuition into the rigid syntax of a proof assistant (autoformalization) remains a major bottleneck.

---

## 2. Formal Proof Assistants

A **formal proof assistant** (also called an interactive theorem prover or ITP) is a software tool that provides a formal language for writing mathematical definitions, theorem statements, and proofs, along with a kernel that mechanically verifies each proof step. If the kernel accepts a proof, it is mathematically correct by construction -- no trust in the user or in AI is required.

### Lean

- **Origin**: Created by Leonardo de Moura at Microsoft Research (Lean 1: 2013, Lean 4: 2021)
- **Logic**: Dependent type theory (Calculus of Inductive Constructions)
- **Key Feature**: Lean 4 is a complete rewrite that doubles as a general-purpose programming language -- it compiles to C and runs fast. Its metaprogramming framework allows users to write custom tactics in Lean itself.
- **Library**: [Mathlib](https://github.com/leanprover-community/mathlib4) -- with nearly 2 million lines of formalized mathematics, over 250,000 theorems and 120,000 definitions, it is the largest coherent mathematical library ever created.
- **Why It Dominates AI Research**: Lean's clean API, active community, and excellent tooling (VS Code extension, `lake` build system) have made it the preferred target for AI theorem proving research. Nearly all major neural provers (AlphaProof, DeepSeek-Prover, Goedel-Prover, LeanDojo) target Lean.
- **Notable Uses**: Proof of the Liquid Tensor Experiment (Scholze, 2022), formalization of the strong PNT (Gauss agent, 2025), IMO 2024-2025 AI competitions.

### Coq (Rocq)

- **Origin**: Developed by Thierry Coquand and Gerard Huet at INRIA, France (1984). Recently renamed to **Rocq**.
- **Logic**: Calculus of Inductive Constructions with a powerful tactic language (Ltac, Ltac2)
- **Key Feature**: Program extraction -- Coq can extract certified executable programs from constructive proofs.
- **Library**: The Mathematical Components library (MathComp) and the Fiat Crypto library
- **Notable Uses**: CompCert (a fully verified C compiler), Fiat Cryptography (used in Chrome and Android for elliptic curve cryptography), the proof of the Four Color Theorem (Gonthier, 2005)
- **AI Research**: CoqHammer, Proverbot9001 (Sanchez-Stern et al., 2020), Tactician

### Isabelle

- **Origin**: Developed by Larry Paulson at Cambridge (1986), with major contributions from Tobias Nipkow (TU Munich)
- **Logic**: A generic proof framework; most commonly used with Higher-Order Logic (Isabelle/HOL)
- **Key Feature**: Sledgehammer -- the pioneering "hammer" tool that dispatches goals to external ATPs (E, Vampire, Z3, SPASS) and reconstructs their proofs within Isabelle's kernel
- **Library**: The Archive of Formal Proofs (AFP), containing 800+ entries
- **Notable Uses**: Verification of the seL4 microkernel (the world's most verified OS kernel), verification of distributed algorithms (Martin Kleppmann)
- **AI Research**: Thor (Jiang et al., 2022), Baldur (First et al., 2023), Magnushammer (Mikula et al., 2024), PISA benchmark

### Agda

- **Origin**: Developed by Ulf Norell at Chalmers University (2007, building on earlier Agda by Catarina Coquand)
- **Logic**: Dependent type theory with support for Homotopy Type Theory (HoTT) via Cubical Agda
- **Key Feature**: Full dependent types with no separate tactic language -- proofs are programs. Cubical Agda implements univalent foundations, enabling a fundamentally different approach to equality.
- **Library**: The Agda standard library and the 1Lab (cubical type theory library)
- **Notable Uses**: Research in homotopy type theory and higher-dimensional type theory
- **AI Research**: Minimal -- Agda's lack of built-in proof automation makes it less attractive for ML integration, but its clean type theory makes it valuable for foundational research.

### Mizar

- **Origin**: Created by Andrzej Trybulec in Poland (1973) -- the oldest active proof assistant project
- **Logic**: Classical first-order logic with Tarski-Grothendieck set theory
- **Key Feature**: The Mizar language was designed to read like standard mathematical prose. Its declarative proof style is the closest to how mathematicians actually write.
- **Library**: The Mizar Mathematical Library (MML) -- over 1,400 articles containing 65,000+ theorems. It was the largest coherent body of formalized mathematics until Mathlib surpassed it.
- **Notable Uses**: Foundational formalization across algebra, topology, analysis, and lattice theory
- **AI Research**: Metamath (a simpler system inspired by Mizar's goals) was used in early neural prover work (GPT-f, HyperTree Proof Search).

### Other Notable Systems

| System | Logic | Notable For |
|--------|-------|-------------|
| **HOL Light** | Higher-order logic | Flyspeck project (formal proof of Kepler conjecture) |
| **Metamath** | Set theory (ZFC) | Minimalist kernel; used in GPT-f and HTPS research |
| **HOL4** | Higher-order logic | TacticZero RL research; hardware verification |
| **ACL2** | First-order logic | Industrial use at AMD, Intel for hardware verification |
| **Dafny** | First-order logic | Program verification; miniF2F-Dafny variant |

### Why Proof Assistants Matter for AI

Proof assistants provide something uniquely valuable for AI research: **a perfect verifier**. In most AI domains (natural language, code generation, image synthesis), evaluating output quality requires human judgment or imperfect heuristics. In formal mathematics, the kernel provides a binary, absolute ground truth: the proof either checks or it does not. This makes theorem proving an ideal testbed for developing AI reasoning capabilities, because:

- There is no ambiguity about correctness
- Progress is precisely measurable
- The task requires genuine multi-step reasoning, not pattern matching
- Success cannot be achieved by memorization alone

---

## 3. Key Systems and Tools

### AlphaProof (Google DeepMind, 2024)

AlphaProof is DeepMind's reinforcement-learning-based theorem prover, inspired by AlphaZero. It was published in Nature in 2025 and represents one of the most significant milestones in AI-assisted theorem proving.

**How it works:**
1. A pre-trained language model translates natural language problem statements into formal Lean specifications (autoformalization)
2. AlphaZero-style reinforcement learning trains the prover on millions of auto-formalized problems
3. At inference time, **Test-Time RL** generates and learns from millions of related problem variants, enabling deep problem-specific adaptation
4. All proofs are verified by the Lean kernel, guaranteeing 100% correctness

**IMO 2024 performance:**
- Combined with AlphaGeometry 2 (for geometry), solved 4 out of 6 IMO 2024 problems
- Earned 28 out of 42 points -- silver medal level
- Solved the hardest problem in the competition (Problem 6), which only 5 human contestants solved
- AlphaProof alone solved 2 algebra problems and 1 number theory problem

**Key insight**: Unlike LLM-only approaches, AlphaProof guarantees correctness because every proof is formally verified. The RL training loop enables the system to develop deep mathematical intuition through self-play, similar to how AlphaZero mastered chess.

**Paper**: "Olympiad-level formal mathematical reasoning with reinforcement learning" (Nature, 2025)

### AlphaGeometry / AlphaGeometry 2 (Google DeepMind, 2024-2025)

A companion system to AlphaProof, specialized for Euclidean geometry. It exemplifies the neuro-symbolic paradigm: a neural language model suggests auxiliary constructions (creative, intuitive), and a symbolic deduction engine (DDAR -- Deductive Database with Arithmetic Reasoning) performs the rigorous proof search (deterministic, exhaustive).

**Key results:**
- AlphaGeometry solved 25 out of 30 Olympiad geometry problems (Nature, January 2024), matching the average human gold medalist (25.9)
- Trained on 100 million synthetic examples -- no human demonstrations required
- AlphaGeometry 2 (February 2025) solved 42 out of 50 IMO geometry problems from 2000-2024 (84%)

**Paper**: "Solving olympiad geometry without human demonstrations" (Nature, 2024)

### LeanDojo (Yang et al., 2023)

LeanDojo is the foundational infrastructure that bridges the Python-based world of machine learning and the Lean proof environment. It solves two critical problems: data extraction and programmatic interaction.

**What it provides:**
- Extracts rich datasets from Lean repositories: ASTs, file dependencies, proof states, tactics, and fine-grained premise annotations
- Transforms Lean into a gym-like environment where AI agents can observe proof states, submit tactics, and receive feedback
- A benchmark of 98,734 theorems extracted from Lean's math library with a challenging data split requiring generalization to novel premises

**Why it matters**: Before LeanDojo, training ML models on Lean data required heroic engineering effort. LeanDojo democratized access, enabling dozens of follow-up papers.

**Paper**: "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models" (NeurIPS 2023, Datasets and Benchmarks)

### ReProver (Yang et al., 2023)

ReProver (Retrieval-Augmented Prover) is the neural prover built on top of LeanDojo. It is an LLM-based prover that retrieves relevant premises from Lean's math library before generating tactics.

**How it works:**
1. Given the current proof state, retrieves a handful of potentially useful premises from the full library
2. Generates tactic candidates conditioned on the concatenation of state and retrieved premises
3. Uses best-first search to find complete proofs

**Key results:**
- Outperformed non-retrieval baselines and GPT-4
- Discovered 33 previously unknown proofs in miniF2F and 39 in ProofNet

**Significance**: ReProver demonstrated that retrieval-augmented generation (RAG), already proven in NLP, is equally powerful for theorem proving. Premise selection -- finding the right lemma from a library of hundreds of thousands -- is the key bottleneck, and retrieval directly addresses it.

### LEGO-Prover (Wang et al., 2023)

LEGO-Prover introduces the idea of a **growing skill library** for neural theorem proving. Instead of proving each theorem from scratch, it builds and reuses a library of verified lemmas.

**How it works:**
1. LLM attempts to prove a theorem, possibly generating auxiliary lemmas
2. Successfully verified lemmas are added to a growing library
3. When proving future theorems, relevant skills (lemmas) are retrieved from the library
4. The library grows organically as more theorems are proved

**Key results:**
- Generated over 20,000 verified lemmas during proof search
- Advanced state-of-the-art on miniF2F-valid from 48.0% to 57.0% and miniF2F-test from 45.5% to 50.0%
- The learned library bridged the gap between human proofs and formal proofs by filling in missing intermediate steps

**Paper**: ICLR 2024 (Oral presentation)

### GPT-f (Polu & Sutskever, OpenAI, 2020)

GPT-f was the pioneering work that demonstrated large language models could generate formal mathematical proofs. It applied GPT-style transformers to the Metamath formalization language.

**How it works:**
- Decoder-only transformer (774M parameters, similar to GPT-2 architecture)
- Trained on Metamath proof data
- Generates statement-step pairs that are assembled into proof trees
- Outputs are verified by the Metamath proof checker

**Key results:**
- Closed 56.22% of proofs from a held-out Metamath test set (previous SOTA: 21.16% by MetaGen-IL)
- **23 shortened proofs were accepted into the main Metamath library** -- the first time a deep learning system contributed proofs adopted by a formal mathematics community

**Historical significance**: GPT-f proved that the same transformer architectures excelling at natural language could also handle formal mathematical reasoning. It launched the current era of LLM-based theorem proving.

**Paper**: "Generative Language Modeling for Automated Theorem Proving" (arXiv:2009.03393, 2020)

### HyperTree Proof Search (Lample et al., Meta AI, 2022)

HTPS is a search algorithm inspired by AlphaZero, developed by Meta AI, that combines a neural policy with a novel tree search for theorem proving.

**How it works:**
- A transformer model is trained on annotated proofs to predict useful tactics
- HTPS uses an online training procedure: the model learns from its own proof search attempts, allowing it to generalize far beyond the training distribution
- The search algorithm balances exploration (trying new tactics) and exploitation (pursuing promising proof paths)

**Key results:**
- Proved 65.4% of held-out Metamath theorems (previous SOTA: 56.5% by GPT-f)
- Online training boosted accuracy to 82.6%
- Improved miniF2F-curriculum from 31% to 42%
- Solved 10 IMO problems -- 5x more than any previous AI system at the time

**Paper**: "HyperTree Proof Search for Neural Theorem Proving" (NeurIPS 2022)

### Draft, Sketch, and Prove (Jiang et al., 2023)

DSP introduces a three-stage pipeline that leverages informal mathematical proofs to guide formal proof search.

**The three stages:**
1. **Draft**: An LLM generates an informal proof in natural language
2. **Sketch**: The informal proof is mapped to a formal proof sketch (a partial proof with gaps)
3. **Prove**: An automated prover fills in the gaps, guided by the sketch structure

**Key insight**: Rather than trying to generate a complete formal proof in one shot, DSP breaks the problem into translation (which LLMs are good at) and gap-filling (which automated provers are good at). The informal proof provides the high-level strategy; the prover handles the low-level details.

**Key results:**
- Improved success rate from 20.9% to 39.3% on mathematical competition problems
- Works with both human-written and LLM-generated informal proofs

**Paper**: ICLR 2023 (Oral presentation)

### Baldur (First et al., 2023)

Baldur demonstrated that LLMs can generate entire proofs at once (rather than step by step), and that failed proof attempts can be repaired using error messages.

**How it works:**
1. Given a theorem statement, the LLM generates a complete proof in one forward pass
2. If the proof fails verification, the error message is fed back to the LLM
3. The LLM generates a repaired proof conditioned on the original attempt and the error

**Key results:**
- Evaluated on 6,336 Isabelle/HOL theorems
- Improved over the state-of-the-art Thor system by 8.7%
- Combined with Thor, proved 65.7% of theorems fully automatically

**Significance**: Baldur showed that whole-proof generation is competitive with search-based approaches, with far lower computational cost. The proof repair mechanism (using compiler feedback) prefigured the self-correction techniques now central to systems like Goedel-Prover-V2.

**Paper**: ESEC/FSE 2023

### DeepSeek-Prover Series (DeepSeek AI, 2024-2025)

A family of open-source models purpose-built for formal theorem proving in Lean 4.

**DeepSeek-Prover-V1.5 (2024):**
- Integrated reinforcement learning with Monte Carlo Tree Search (MCTS) for proof search
- Established itself as the leading open Lean ATP as of late 2024

**DeepSeek-Prover-V2 (2025):**
- Built on DeepSeek-V3 foundation model (671B parameters)
- Key innovation: **subgoal decomposition via RL** -- DeepSeek-V3 decomposes theorems into high-level proof sketches and formalizes them as Lean 4 subgoals
- Chain-of-thought reasoning combined with formal step-by-step proofs
- **Results**: 88.9% pass ratio on miniF2F-test; solved 49/658 PutnamBench problems
- Available in 7B and 671B parameter sizes

**Paper**: "DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition" (arXiv:2504.21801, 2025)

### Goedel-Prover (Goedel-LM, 2025)

The current state-of-the-art open-source theorem prover, setting records across multiple benchmarks.

**Goedel-Prover-V2 (August 2025) key innovations:**
1. **Scaffolded data synthesis**: Generates synthetic training tasks of increasing difficulty
2. **Verifier-guided self-correction**: Uses Lean compiler feedback to iteratively fix proof attempts
3. **Model averaging**: Mitigates diversity loss during training

**Results:**
- Goedel-Prover-V2-8B: 84.6% pass@32 on miniF2F -- outperforms DeepSeek-Prover-V2-671B despite being 80x smaller
- Goedel-Prover-V2-32B: 88.1% standard, **90.4% with self-correction** on miniF2F
- Solved 86 PutnamBench problems (pass@184), surpassing DeepSeek-Prover-V2-671B's record of 47

### Thor (Jiang et al., 2022)

Thor integrates language models with traditional "hammer" tools (Sledgehammer) for Isabelle theorem proving.

**Key idea**: Hammers are excellent at premise selection but poor at creative proof steps. Language models are creative but poor at selecting from large libraries. Thor combines both: hammers handle premise selection while the language model handles everything else.

**Results**: Increased success rate on the PISA dataset from 39% to 57%, with 8.2% of problems solved by neither approach alone.

**Paper**: "Thor: Wielding Hammers to Integrate Language Models and Automated Theorem Provers" (NeurIPS 2022)

### Lean Copilot (Song, Yang, Anandkumar, 2024)

A framework for running LLM inference natively within Lean, enabling AI-assisted proof writing in the user's IDE.

**Key feature**: Unlike standalone provers, Lean Copilot integrates directly into the mathematician's workflow in VS Code, suggesting tactics, completing proof steps, and searching for proofs interactively. This human-AI collaboration model is likely how most mathematicians will interact with AI provers in practice.

### Other Notable Systems

| System | Year | Key Contribution |
|--------|------|-----------------|
| **Aristotle** (Harmonic) | 2025 | First formally verified gold-medal IMO performance; all solutions checked in Lean 4 |
| **AxiomProver** (Axiom Math) | 2025 | Solved 12/12 Putnam 2025 problems autonomously; multi-agent ensemble for Lean 4 |
| **Gauss** (Math Inc.) | 2025 | Formalized strong PNT in 3 weeks (25K LOC, 1000+ theorems); human-AI collaboration |
| **Llemma** (EleutherAI) | 2023 | Open math LLM; first open model to do in-context theorem proving (ICLR 2024) |
| **TacticZero** (Wu et al.) | 2021 | RL from scratch in HOL4; no example proofs needed (NeurIPS 2021) |
| **Magnushammer** (Mikula et al.) | 2024 | Transformer-based premise selection; outperformed Sledgehammer (ICLR 2024) |
| **Proverbot9001** (Sanchez-Stern et al.) | 2020 | Neural tactic prediction for Coq; CompCert dataset |
| **BFS-Prover-V2** | 2025 | Planner + parallel prover agents with shared subgoal cache |

---

## 4. Techniques

### Proof Search

The fundamental problem in automated theorem proving is **proof search**: given a goal (theorem to prove), find a sequence of valid steps that transforms it into known truths.

**Best-first search**: The most common approach. Maintain a priority queue of proof states. At each step, expand the most promising state by generating candidate tactics, verify each against the proof assistant, and add resulting states to the queue. ReProver, LeanDojo, and most neural provers use this.

**Monte Carlo Tree Search (MCTS)**: Borrowed from game-playing AI. Balances exploration of new proof paths with exploitation of promising ones. Used by DeepSeek-Prover-V1.5 and AlphaProof.

**HyperTree Proof Search (HTPS)**: Meta AI's AlphaZero-inspired search that learns a value function estimating proof probability from any state, enabling more informed exploration.

### Tactic Prediction

In interactive theorem provers, proofs are constructed by applying **tactics** -- commands that transform proof goals. Tactic prediction is the task of predicting which tactic to apply given the current proof state.

**Classification approach**: Treat it as a classification problem over a fixed vocabulary of tactic templates (GamePad, Proverbot9001). Simple but limited by the fixed vocabulary.

**Generation approach**: Treat it as a sequence-to-sequence problem -- encode the proof state, decode a tactic string. This handles novel tactic arguments and is the dominant approach in modern systems (ReProver, DeepSeek-Prover, Goedel-Prover).

**Hybrid approach**: Generate the tactic name, then separately predict its arguments (e.g., which premises to apply). Thor and Magnushammer use this split.

### Premise Selection

Given a goal, which of the tens of thousands of available lemmas might be useful? This is **premise selection** -- often the key bottleneck in theorem proving.

**Classical methods**: k-NN based on hand-crafted features of goal and premise (used in early Sledgehammer)

**Neural retrieval**: Encode goals and premises into a shared embedding space; retrieve by similarity. ReProver uses dense retrieval. Magnushammer uses a two-stage SELECT + RERANK pipeline with contrastive training, achieving 59.5% on PISA vs. Sledgehammer's 38.3%.

**Retrieval-augmented generation (RAG)**: Retrieve premises, concatenate with the proof state, and feed to a generative model. This is the dominant paradigm as of 2025.

### Reinforcement Learning for Proofs

RL treats theorem proving as a sequential decision problem: the agent takes actions (tactics), observes states (proof goals), and receives reward (proof completed or failed).

**Expert Iteration (ExIt)**: Train a model on proofs, use it to find new proofs, add those to training data, repeat. Used by HTPS and early systems.

**GRPO (Group Relative Policy Optimization)**: Used by modern systems like DeepSeek-Prover-V2 for training on proof outcomes without needing a separate value model.

**Test-Time RL**: AlphaProof's innovation -- at inference time, generate millions of problem variants and train on them, achieving deep adaptation to a specific problem.

**Self-play**: Generate conjectures, attempt proofs, learn from successes. Creates a virtuous cycle of improving both conjecture quality and proof capability.

### LLM-Guided Search

The current dominant paradigm combines large language models with formal verification:

1. LLM proposes proof steps (creative, fast, imprecise)
2. Proof assistant verifies each step (deterministic, exact, binary)
3. Failed attempts provide error signals for refinement
4. Search algorithm orchestrates the process

This is fundamentally a **neuro-symbolic** architecture: neural for generation, symbolic for verification.

### Subgoal Decomposition and Proof Planning

Complex theorems benefit from hierarchical decomposition:

1. A **planner** (typically a large LLM like DeepSeek-V3) breaks the theorem into a sequence of subgoals
2. A **prover** (typically a smaller, specialized model) attempts each subgoal independently
3. Subgoal proofs are composed into a complete proof
4. Failed subgoals can be further decomposed

DeepSeek-Prover-V2 and BFS-Prover-V2 use this approach to dramatic effect. It mirrors how human mathematicians work: first sketch the high-level argument, then fill in the details.

### Chain-of-Thought for Proofs

LLMs generate natural language reasoning interleaved with formal proof steps. The informal reasoning serves as a "scratchpad" that helps the model plan ahead, while the formal steps are verified by the proof assistant. DeepSeek-Prover-V2's cold-start training combines chain-of-thought with formal Lean code to initialize RL.

### Autoformalization

Translating informal mathematics (natural language, LaTeX) into formal proof assistant code. This is essential for applying AI provers to real mathematical problems, which are typically stated informally.

**Key work**: Wu et al. (2022) showed that large language models (PaLM 540B, Codex) can autoformalize with 25-30% success rate. The Draft-Sketch-Prove pipeline uses autoformalization as its first step. AlphaProof uses autoformalization to translate IMO problems into Lean.

### Synthetic Data Generation

A critical enabler: generating large-scale training data for neural provers.

- **AlphaGeometry**: Generated 100 million synthetic geometry examples
- **Goedel-Prover-V2**: Scaffolded data synthesis creates tasks of increasing difficulty
- **DeepSeek-Prover**: Recursive pipeline uses existing proofs to generate new training problems
- **State-transition graph exploration**: Systematic enumeration of proof states to generate millions of theorems with proofs

---

## 5. Key Papers (Chronological)

### Foundational Work (Pre-2019)

| Year | Paper | Authors | Venue | Summary |
|------|-------|---------|-------|---------|
| 1965 | "A Machine-Oriented Logic Based on the Resolution Principle" | J. A. Robinson | JACM | Introduced resolution with unification -- the foundation of automated deduction |
| 2016 | "DeepMath - Deep Sequence Models for Premise Selection" | Alemi et al. | NeurIPS | First deep learning for premise selection in formal mathematics |
| 2017 | "Learning to Prove Theorems via Interacting with Proof Assistants" | Yang & Deng | ICML 2019 | CoqGym environment for ML interaction with Coq |

### The Neural Prover Era (2019-2021)

| Year | Paper | Authors | Venue | Summary |
|------|-------|---------|-------|---------|
| 2019 | "HOList: An Environment for Machine Learning of Higher-Order Logic Theorem Proving" | Bansal et al. | ICML | Google's benchmark for ML-based theorem proving in HOL Light |
| 2019 | "GamePad: A Learning Environment for Theorem Proving" | Huang et al. | ICLR | ML environment for Coq with tactic prediction as classification |
| 2020 | "Generative Language Modeling for Automated Theorem Proving" (GPT-f) | Polu & Sutskever | arXiv | First GPT-based prover; proofs accepted into Metamath library |
| 2020 | "Proverbot9001: A Per-Proof Adaptive Proof-Search System for Coq" | Sanchez-Stern et al. | -- | Neural tactic prediction for Coq using CompCert dataset |
| 2021 | "TacticZero: Learning to Prove Theorems from Scratch with Deep RL" | Wu et al. | NeurIPS | RL from scratch in HOL4; no example proofs needed |
| 2021 | "Proof Artifact Co-Training for Theorem Proving with Language Models" | Han et al. | ICLR | Co-training on proof artifacts improves tactic prediction |

### Scaling and Sophistication (2022-2023)

| Year | Paper | Authors | Venue | Summary |
|------|-------|---------|-------|---------|
| 2022 | "HyperTree Proof Search for Neural Theorem Proving" | Lample et al. (Meta AI) | NeurIPS | AlphaZero-inspired search; online training; 10 IMO problems |
| 2022 | "Thor: Wielding Hammers to Integrate Language Models and Automated Theorem Provers" | Jiang et al. | NeurIPS | Combined LMs with Sledgehammer for Isabelle |
| 2022 | "Autoformalization with Large Language Models" | Wu et al. | NeurIPS | LLMs for translating informal math to formal (PaLM, Codex) |
| 2023 | "Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs" | Jiang et al. | ICLR (Oral) | Three-stage informal-to-formal pipeline |
| 2023 | "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models" | Yang et al. | NeurIPS | Open-source infrastructure for ML + Lean; ReProver |
| 2023 | "Baldur: Whole-Proof Generation and Repair with Large Language Models" | First et al. | ESEC/FSE | Whole-proof generation + error-guided repair for Isabelle |
| 2023 | "LEGO-Prover: Neural Theorem Proving with Growing Libraries" | Wang et al. | ICLR 2024 (Oral) | Growing skill library of verified lemmas |
| 2023 | "Llemma: An Open Language Model for Mathematics" | Azerbayev et al. (EleutherAI) | ICLR 2024 | Open math LLM trained on Proof-Pile-2; in-context theorem proving |

### The Current Frontier (2024-2026)

| Year | Paper | Authors | Venue | Summary |
|------|-------|---------|-------|---------|
| 2024 | "Solving Olympiad Geometry without Human Demonstrations" (AlphaGeometry) | Trinh et al. (DeepMind) | Nature | Neuro-symbolic geometry prover; 25/30 Olympiad problems |
| 2024 | "Magnushammer: A Transformer-Based Approach to Premise Selection" | Mikula et al. | ICLR | Contrastive transformer for premise selection; beat Sledgehammer |
| 2024 | "A Survey on Deep Learning for Theorem Proving" | Li et al. | COLM | Comprehensive survey covering autoformalization, premise selection, proof search |
| 2024 | "MiniF2F-Dafny: LLM-Guided Mathematical Theorem Proving via Auto-Active Verification" | -- | arXiv | Extended miniF2F to Dafny verification language |
| 2025 | "Olympiad-level Formal Mathematical Reasoning with Reinforcement Learning" (AlphaProof) | Silver, Huang et al. (DeepMind) | Nature | RL-based prover; IMO 2024 silver medal; test-time RL |
| 2025 | "AlphaGeometry 2: Gold-Medalist Performance in Solving Olympiad Geometry" | Trinh et al. (DeepMind) | arXiv | 42/50 IMO geometry problems (2000-2024) |
| 2025 | "DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via RL for Subgoal Decomposition" | DeepSeek AI | arXiv | 88.9% miniF2F; subgoal decomposition via RL |
| 2025 | "Goedel-Prover: A Frontier Model for Open-Source Automated Theorem Proving" | Goedel-LM | arXiv | 57.6% miniF2F with SFT; scaffolded data synthesis |
| 2025 | "Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction" | Goedel-LM | arXiv | 90.4% miniF2F; 86 PutnamBench problems; open-source SOTA |
| 2025 | "Lean Copilot: Large Language Models as Copilots for Theorem Proving in Lean" | Song et al. | ICML | LLM inference natively in Lean; human-AI collaboration |

---

## 6. Competitions and Benchmarks

### The IMO Grand Challenge

The most prestigious AI-mathematics challenge. Proposed by a consortium including Fields Medalist Timothy Gowers, the goal is to build an AI that earns a gold medal in the formal-to-formal (F2F) version of the International Mathematical Olympiad.

**Rules:**
- Input: formal representation of the problem in Lean
- Output: machine-checkable proof in Lean
- Each proof must verify in the Lean kernel within 10 minutes
- No internet access during the exam

**Status (as of early 2026):**
- 2024: AlphaProof + AlphaGeometry 2 achieved silver medal (28/42 points)
- 2025: Both DeepMind (Gemini + Deep Think) and Harmonic (Aristotle) achieved gold-medal level
- 2025: OpenAI also claimed gold-medal level performance
- The formal-to-formal challenge with Lean verification remains the gold standard

### AIMO Prize

A $5 million prize fund created by XTX Markets founder Alex Gerko for AI mathematical reasoning. The first Progress Prize ($131,072) was won by Team Numina (NuminaMath 7B TIR) in July 2024, solving 29/50 problems. Presentation by Terence Tao at IMO 2024 in Bath.

### miniF2F

The most widely used benchmark for neural theorem proving, created by OpenAI.

- **Size**: 488 problems (244 test, 244 validation)
- **Source**: AMC, AIME, IMO competition problems + high school/undergraduate math
- **Languages**: Lean, Metamath, Isabelle, HOL Light
- **Difficulty**: Competition-level; ranges from routine to very challenging
- **Current SOTA**: Goedel-Prover-V2-32B at 90.4% (pass@32 with self-correction)

**Leaderboard progression (miniF2F-test, pass@32):**

| Year | System | Score |
|------|--------|-------|
| 2022 | HTPS | ~42% |
| 2023 | LEGO-Prover | 50.0% |
| 2024 | DeepSeek-Prover-V1.5-RL | 50.0% |
| 2025 (Feb) | Goedel-Prover-SFT | 57.6% |
| 2025 (Apr) | DeepSeek-Prover-V2-671B | 88.9% |
| 2025 (Aug) | Goedel-Prover-V2-32B | 90.4% |

### PutnamBench

A multilingual benchmark of problems from the William Lowell Putnam Mathematical Competition (the premier North American undergraduate competition).

- **Size**: 1,724 formalizations across Lean 4, Isabelle, and Coq (658 in Lean 4)
- **Source**: Putnam competition problems, 1962-2025
- **Difficulty**: Harder than miniF2F; undergraduate competition level
- **Current SOTA**: Goedel-Prover-V2 solved 86 problems; AxiomProver solved 12/12 of the 2025 exam

### ProofNet

A benchmark for autoformalization and theorem proving at the undergraduate level.

- **Size**: 186 problems
- **Source**: Undergraduate analysis and algebra courses
- **Focus**: Tests both autoformalization (natural language to formal) and proof generation

### FIMO

- **Size**: 149 formalizations of IMO shortlist problems in Lean 3
- **Source**: IMO shortlists, formalized using GPT-4 back-translation + human verification
- **Focus**: Olympiad-level difficulty

### FormalMATH (2025)

A newer benchmark aiming for broader coverage.

- **Size**: 5,560 problems
- **Source**: High-school through graduate-level mathematics
- **Focus**: Diversity of mathematical domains

### PISA

- **Source**: Isabelle's Archive of Formal Proofs (AFP)
- **Focus**: Real-world Isabelle theorems, not competition problems
- **Used by**: Thor, Magnushammer, Baldur

---

## 7. Industry vs Academia

### Google DeepMind

The undisputed leader. AlphaProof, AlphaGeometry, and Gemini Deep Think represent the highest-profile results. Their approach emphasizes reinforcement learning (AlphaZero heritage), synthetic data, and massive compute. The AlphaProof Nature paper and IMO results have defined the field's aspirations.

### DeepSeek AI

The leading open-source contributor. DeepSeek-Prover-V1 through V2 are freely available and have pushed the open-source frontier to within striking distance of closed systems. Their subgoal decomposition approach (building on DeepSeek-V3's reasoning capabilities) has been highly influential.

### Meta AI (FAIR)

Pioneered the modern era with HyperTree Proof Search (2022). Guillaume Lample, a co-author of HTPS, co-founded Project Numina and later joined the field's commercial efforts. Meta's work on online training and search algorithms remains foundational.

### OpenAI

Started the neural prover era with GPT-f (2020). Created the miniF2F benchmark. Claimed gold-medal IMO 2025 performance. Their emphasis has been on scaling language models and applying them to math, rather than building specialized provers.

### Microsoft Research

Contributed to Lean development (Leonardo de Moura created Lean at MSR). Active in autoformalization research. Supports the LeanDojo/Lean Copilot ecosystem.

### Harmonic

A startup focused on "Mathematical Superintelligence" (MSI). Their Aristotle system achieved the first formally verified gold-medal IMO performance (2025). Raised $120M Series C. Founded by former Google and Facebook researchers.

### Axiom Math

Founded by Carina Hong (24 years old in 2025). AxiomProver solved all 12 Putnam 2025 problems autonomously. $64M in financing. Their multi-agent ensemble approach to Lean 4 theorem proving represents a new architectural direction.

### Math Inc.

Created the Gauss autoformalization agent. Demonstrated human-AI collaboration on research-level mathematics (strong PNT formalization). Jesse Michael Han (co-founder) previously formalized the independence of the continuum hypothesis.

### Goedel-LM

Open-source research group behind Goedel-Prover-V1 and V2. Currently holds the open-source SOTA across miniF2F and PutnamBench. Their scaffolded data synthesis and self-correction techniques have been widely adopted.

### Academic Groups

| Group | Institution | Contributions |
|-------|-------------|---------------|
| Kaiyu Yang's group | Caltech/Princeton | LeanDojo, ReProver, Lean Copilot |
| Albert Jiang | Cambridge | Draft-Sketch-Prove, Thor, AlphaGeometry co-author |
| Sean Welleck | CMU | LEGO-Prover, natural language proof generation |
| Jesse Michael Han | Math Inc. | Gauss agent, IMO formalization |
| Zhangir Azerbayev | CMU/EleutherAI | Llemma, Proof-Pile-2 dataset |
| Stanislas Polu | (ex-OpenAI) | GPT-f, co-founded Numina |

---

## 8. Relevance to Neuro-Symbolic AI

AI-assisted theorem proving is arguably **the purest and most demanding neuro-symbolic task in existence**. Here is why:

### The Architecture Is Inherently Neuro-Symbolic

Every modern AI theorem prover follows the same pattern:

```
Neural component (LLM) → generates proof candidates → Symbolic component (proof kernel) → verifies
```

This is precisely the **Type 2: Symbolic[Neural]** pattern in the Kautz taxonomy -- a symbolic system (the proof assistant) orchestrates neural components (the language model). The symbolic component is the authority; the neural component is the advisor.

Compare this to Sigil's architecture:

```
Neural component (LLM) → parses natural language → Symbolic component (rule engine) → decides
```

The structural parallel is exact. In both cases:
- Neural handles perception/generation (language understanding, proof step suggestion)
- Symbolic handles reasoning/verification (proof checking, rule evaluation)
- The boundary is explicit and auditable
- The symbolic side guarantees correctness; the neural side provides flexibility

### Why Neural Alone Fails

LLMs can generate plausible-looking proofs, but they hallucinate mathematical claims, confuse similar-sounding lemmas, and cannot reliably track logical dependencies across many steps. A proof that "looks right" to a language model may contain subtle errors. Only formal verification eliminates this failure mode.

This directly mirrors Sigil's core philosophy: **"LLMs never make decisions."** In theorem proving, the LLM suggests; the kernel decides. In Sigil, the LLM parses; the rule engine decides.

### Traces as First-Class Output

In formal theorem proving, the proof itself is a trace -- a complete, auditable record of every logical step from axioms to conclusion. This is exactly Sigil's philosophy that "traces are fundamental output, not debugging." A Sigil execution trace serves the same purpose as a formal proof: it explains *why* a decision was reached, in a way that can be mechanically verified.

### The Confidence/Fallback Pattern

AlphaProof uses reinforcement learning to estimate proof probability, with fallback strategies when confidence is low. Sigil's `neural` keyword requires a confidence threshold and mandatory fallback. Both systems acknowledge that neural components are unreliable and build explicit mechanisms to handle failure.

### Determinism by Default

Proof assistants are perfectly deterministic: the same proof script always produces the same verification result. Sigil is "deterministic by default" with the `neural` keyword as the only source of non-determinism. Both architectures default to symbolic certainty and carefully quarantine neural uncertainty.

---

## 9. Relevance to Sigil

### Formal Verification Concepts for Rule Engines

Theorem proving research offers several ideas directly applicable to Sigil:

**Proof search as rule evaluation**: Sigil's forward and backward chaining are structurally similar to proof search in ITPs. Forward chaining (apply rules until fixed point) resembles forward reasoning in Isabelle. Backward chaining (query-driven goal decomposition) is directly analogous to tactic-based proving in Lean/Coq, where each tactic transforms a goal into subgoals.

**Premise selection for rule activation**: In a Sigil program with hundreds of rules, determining which rules are relevant to a given input is analogous to premise selection in theorem proving. The Rete algorithm in Sigil's Rust core serves a similar function to Sledgehammer -- efficiently selecting relevant rules from a large library.

**Subgoal decomposition for complex decisions**: DeepSeek-Prover-V2's approach of breaking theorems into subgoals maps to Sigil's rule chaining. A complex business decision can be decomposed into sub-decisions, each resolved by different rules, then composed into a final answer.

### Trace Verification

Theorem proving's emphasis on machine-checkable proofs suggests a direction for Sigil: **machine-verifiable traces**. Currently, Sigil traces explain decisions in human-readable form. A more formal approach would make traces independently verifiable -- a third party could check that the trace is consistent with the rules and input, without re-executing the program.

### The LEGO-Prover Pattern for Sigil Libraries

LEGO-Prover's growing library of verified lemmas maps directly to Sigil's module system. As organizations build Sigil rule libraries, common decision patterns (risk assessment, compliance checks, escalation logic) could be extracted as verified, reusable modules -- growing a "decision library" analogous to Mathlib.

### Neural Bridge Design

Sigil's neural bridge (Phase 3) can learn from how theorem provers integrate neural and symbolic components:

- **AlphaProof pattern**: Use RL to train neural components that work well with the symbolic engine, not just in isolation
- **DSP pattern**: Use informal reasoning (LLM output) to guide formal execution (rule evaluation), not replace it
- **Baldur pattern**: Use symbolic error feedback (type errors, rule conflicts) to improve neural component outputs

### Potential Future Direction: Verified Sigil Programs

Long-term, insights from theorem proving could enable **verified Sigil programs** -- programs where certain properties (termination, absence of conflicting rule firings, coverage of all input cases) are formally proven. This would bring the trustworthiness of formal mathematics to business decision systems.

---

## 10. Learning Path

### Tier 1: Foundations (Start Here)

**Understanding proof assistants:**
1. [Natural Number Game](https://adam.math.hhu.de/#/g/leanprover-community/NNG4) -- Interactive Lean 4 tutorial. Prove properties of natural numbers in your browser. No installation required. The single best starting point.
2. [Theorem Proving in Lean 4](https://leanprover.github.io/theorem_proving_in_lean4/) -- Official textbook covering dependent type theory, tactics, and Lean-specific features.
3. [Mathematics in Lean](https://leanprover-community.github.io/mathematics_in_lean/) -- Learn to do mathematics in Lean 4, from basic logic through analysis and algebra.

**Understanding the AI side:**
4. [NeurIPS Tutorial on Machine Learning for Theorem Proving](https://machine-learning-for-theorem-proving.github.io/) -- Bridges ML and theorem proving for researchers with a general ML background.
5. [A Survey on Deep Learning for Theorem Proving](https://arxiv.org/abs/2404.09939) (Li et al., COLM 2024) -- The most comprehensive survey. Read this to understand the landscape.

### Tier 2: Core Papers (Read in Order)

6. Polu & Sutskever, ["Generative Language Modeling for Automated Theorem Proving"](https://arxiv.org/abs/2009.03393) (GPT-f, 2020) -- The paper that started the neural prover era.
7. Lample et al., ["HyperTree Proof Search for Neural Theorem Proving"](https://arxiv.org/abs/2205.11491) (NeurIPS 2022) -- Introduced modern proof search with online training.
8. Yang et al., ["LeanDojo: Theorem Proving with Retrieval-Augmented Language Models"](https://arxiv.org/abs/2306.15626) (NeurIPS 2023) -- Essential infrastructure paper; understand how ML interacts with Lean.
9. Jiang et al., ["Draft, Sketch, and Prove"](https://arxiv.org/abs/2210.12283) (ICLR 2023) -- The informal-to-formal pipeline.
10. Trinh et al., ["Solving olympiad geometry without human demonstrations"](https://www.nature.com/articles/s41586-023-06747-5) (AlphaGeometry, Nature 2024) -- The neuro-symbolic masterpiece.
11. DeepMind, ["Olympiad-level formal mathematical reasoning with reinforcement learning"](https://www.nature.com/articles/s41586-025-09833-y) (AlphaProof, Nature 2025) -- The current pinnacle.

### Tier 3: Advanced Topics

12. [DeepSeek-Prover-V2 paper](https://arxiv.org/abs/2504.21801) -- Subgoal decomposition, chain-of-thought for proofs.
13. [Goedel-Prover-V2 paper](https://arxiv.org/abs/2508.03613) -- Scaffolded data synthesis, self-correction, current open-source SOTA.
14. [Magnushammer paper](https://arxiv.org/abs/2303.04488) -- Deep dive into neural premise selection.
15. [LEGO-Prover paper](https://arxiv.org/abs/2310.00656) -- Growing libraries of lemmas.

### Tier 4: Hands-On Practice

16. Install [Lean 4](https://lean-lang.org/lean4/doc/setup.html) and work through the exercises in Mathematics in Lean.
17. Clone [LeanDojo](https://github.com/lean-dojo/LeanDojo) and run ReProver on the benchmark.
18. Try [Lean Copilot](https://github.com/lean-dojo/LeanCopilot) in VS Code -- experience human-AI proof collaboration firsthand.
19. Explore [Mathlib](https://leanprover-community.github.io/mathlib4_docs/) -- browse real formalized mathematics.

### Tier 5: Video Resources

20. [Harvard CMSA: Machine Learning and Theorem Proving in Formal Languages](https://www.classcentral.com/course/youtube-amaury-hayat-melanie-wood-alex-davies-jeremy-avigad-machine-learning-and-theorem-proving-407429) -- Panel with experts from DeepMind, CMU, Harvard.
21. [AITP Conference talks](https://aitp-conference.org/) -- Annual conference on AI and Theorem Proving; talks available online.
22. Kevin Buzzard's talks on Lean and formalized mathematics (search YouTube for "Kevin Buzzard Lean") -- Accessible introduction from a practicing mathematician.

### Curated Paper Lists

23. [DL4TP: Deep Learning for Theorem Proving](https://github.com/zhaoyu-li/DL4TP) -- Curated and categorized list of all papers in the field, maintained by the survey authors.

---

## 11. Open Problems

### The Autoformalization Bottleneck

Current autoformalization (translating informal math to formal code) succeeds only 25-30% of the time, even with the best LLMs. Models hallucinate non-existent imports, mix syntax from different proof assistants, and fail to connect informal concepts to their formal library counterparts. Until autoformalization is solved, AI provers will be limited to problems that have already been formalized -- a tiny fraction of mathematics.

### The "Last Mile" Problem

Current systems excel at routine lemmas and competition-level problems but struggle with the kind of creative, multi-step reasoning required for research-level mathematics. The gap between "solving 90% of miniF2F" and "proving new theorems that advance mathematics" remains vast. Research mathematics requires introducing novel definitions, conjecturing intermediate results, and developing new proof techniques -- capabilities that current systems largely lack.

### Long Proofs and Deep Reasoning

The longest proofs generated by current systems are tens to hundreds of steps. Research-level proofs can be thousands of steps long, spanning multiple files and leveraging deep structural understanding of entire mathematical theories. Scaling proof search to this depth while maintaining coherence is an unsolved challenge.

### Library Fragility

Neural provers are typically trained on fixed versions of mathematical libraries (e.g., a specific Mathlib commit). When the library evolves -- definitions are refactored, lemmas are renamed, APIs change -- trained models break. Making provers robust to library evolution is an open problem with practical implications.

### Generalization Beyond Mathematics

Specialized prover models are trained and evaluated almost exclusively on mathematical theorems. Their ability to generalize to other formal verification domains -- software verification, hardware verification, protocol verification -- remains largely unexplored. Can a model trained on Mathlib prove properties about distributed systems? About compiler correctness?

### Computational Cost

AlphaProof reportedly used enormous computational resources (millions of proof attempts per problem). DeepSeek-Prover-V2-671B requires substantial inference infrastructure. Making powerful provers accessible -- both computationally and financially -- is a practical challenge.

### Evaluation and Benchmark Saturation

miniF2F, the most popular benchmark, is approaching saturation (90.4% as of August 2025). New, harder benchmarks (PutnamBench, FormalMATH) are being created, but the field needs benchmarks that test qualitatively different capabilities: creative proof construction, theory development, and conjecture generation.

### Human-AI Collaboration

Most research focuses on fully autonomous proving. But the most impactful near-term applications involve human-AI collaboration (as demonstrated by Gauss and Lean Copilot). Understanding how to optimally divide work between humans and AI provers -- what each is good at, how to communicate proof strategies, how to build trust -- is an underexplored research direction.

### The Conjecture Problem

Current systems prove stated theorems. They do not conjecture new theorems. Generating interesting, non-trivial, provable conjectures is arguably harder than proving them. Some early work exists (e.g., Ramanujan Machine, AI-guided conjectures in knot theory by DeepMind/Davies et al., 2021), but systematic conjecture generation remains wide open.

### Interpretability of Learned Proofs

When a neural prover finds a proof, the proof itself is interpretable (it is formal mathematics). But the process by which the neural model decided on each step is opaque. Understanding *why* a model chose a particular lemma or tactic could yield mathematical insights and improve human understanding, but current neural provers are black boxes at the decision level.

### Unifying Informal and Formal Reasoning

Humans reason informally (intuition, diagrams, analogies) and formalize only when needed. Current AI systems either reason informally (LLMs generating natural language math) or formally (neural provers generating Lean code), but seamlessly integrating both -- as human mathematicians do -- remains a fundamental challenge. The Draft-Sketch-Prove approach is a step in this direction, but a true synthesis is far off.

---

## References and Further Reading

- [LeanDojo ecosystem](https://leandojo.org/) -- Infrastructure, models, and benchmarks for ML + Lean
- [Lean community](https://leanprover-community.github.io/) -- Learning resources, Mathlib documentation, community forums
- [DL4TP paper list](https://github.com/zhaoyu-li/DL4TP) -- Comprehensive curated bibliography
- [AITP Conference](https://aitp-conference.org/) -- Annual conference proceedings
- [IMO Grand Challenge](https://imo-grand-challenge.github.io/) -- Official challenge specification
- [AIMO Prize](https://aimoprize.com/) -- Competition details and results
- [Goedel-Prover](https://goedel-lm.github.io/) -- Open-source SOTA prover
- [DeepSeek-Prover-V2](https://github.com/deepseek-ai/DeepSeek-Prover-V2) -- Open-source prover with subgoal decomposition
- [Harmonic Aristotle IMO 2025 proofs](https://github.com/harmonic-ai/IMO2025) -- Formally verified IMO solutions
- [AxiomProver Putnam 2025 proofs](https://github.com/AxiomMath/putnam2025) -- Formally verified Putnam solutions
- [Gauss strong PNT formalization](https://github.com/math-inc/strongpnt) -- Human-AI collaboration on research mathematics

---

*This guide is part of the Sigil language research library. For context on Sigil's neuro-symbolic architecture and how these concepts relate to the project, see [NEURO_SYMBOLIC_AI_LANDSCAPE.md](../NEURO_SYMBOLIC_AI_LANDSCAPE.md) and [REAL_WORLD_NEURO_SYMBOLIC_BRIDGE.md](../REAL_WORLD_NEURO_SYMBOLIC_BRIDGE.md).*
