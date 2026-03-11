# Autoformalization: A Comprehensive Learning Guide

> Automatically translating informal mathematical proofs and statements into formal, machine-verifiable representations.

---

## Table of Contents

1. [What is Autoformalization](#1-what-is-autoformalization)
2. [Key Research Papers](#2-key-research-papers)
3. [Key Research Groups and Labs](#3-key-research-groups-and-labs)
4. [Approaches and Techniques](#4-approaches-and-techniques)
5. [Benchmarks and Datasets](#5-benchmarks-and-datasets)
6. [Current State of the Art](#6-current-state-of-the-art)
7. [Connection to Neuro-Symbolic AI](#7-connection-to-neuro-symbolic-ai)
8. [Relevance to Sigil](#8-relevance-to-sigil)
9. [Learning Path](#9-learning-path)
10. [Open Problems](#10-open-problems)

---

## 1. What is Autoformalization

### Definition

Autoformalization is the process of automatically translating informal mathematical content -- natural language theorems, proofs, and reasoning written by humans -- into formal, machine-verifiable representations in proof assistants such as Lean, Isabelle/HOL, or Coq. It can be understood as a specialized form of neural machine translation where the source language is informal mathematics (natural language mixed with LaTeX notation) and the target language is a formal proof language.

Christian Szegedy, who coined the modern usage of the term, defines an autoformalization system as:

> "An AI that learns to read natural language content and to turn it into an abstract, machine-verifiable formalization, ideally by bootstrapping from unlabeled training data with minimum human interaction."

### Why It Matters

The gap between informal and formal mathematics is one of the deepest problems in mathematical practice and artificial intelligence:

- **Scale of informal mathematics.** Humanity has produced millions of theorems, proofs, and mathematical arguments written in natural language across centuries. Only a tiny fraction has been formalized. As of 2025, the Lean mathematical library (mathlib) contains over 210,000 formalized theorems -- impressive, but a drop in the ocean compared to the body of informal mathematical knowledge.

- **Verification crisis.** Informal proofs can contain errors that go undetected for years or decades. Formal proofs are machine-checkable: if the proof assistant accepts them, they are correct by construction. Autoformalization could make verification routine rather than heroic.

- **Training data bottleneck.** Modern AI theorem provers (like DeepSeek-Prover or AlphaProof) need formal training data. The Proof Pile dataset, one of the largest collections of formal proofs, contains only about 500MB. Autoformalization is the most promising path to scaling this data.

- **Path to general reasoning.** Szegedy argues that autoformalization is "a promising path towards general artificial intelligence" because mathematical reasoning is the purest form of rigorous thought. A system that masters the translation from informal to formal reasoning has learned something deep about the structure of arguments themselves.

### The Gap Between Informal and Formal

Consider a simple example. An informal statement:

> "For every prime number p greater than 2, p is odd."

In Lean 4, this becomes:

```lean
theorem prime_gt_two_odd (p : Nat) (hp : Nat.Prime p) (h : p > 2) : Odd p
```

The formal version requires:
- Resolving implicit definitions (what does "prime" mean formally?)
- Choosing the right types (`Nat`, not `Int` or `Real`)
- Structuring quantification explicitly
- Connecting to the correct library definitions (`Nat.Prime`, `Odd`)
- Providing a machine-checkable proof

For competition-level or research-level mathematics, this gap becomes enormous. An informal proof might say "by a standard compactness argument" where the formal version requires hundreds of lines of Lean code invoking specific library lemmas.

---

## 2. Key Research Papers

### Foundational Papers

**"A Promising Path Towards Autoformalization and General Artificial Intelligence"**
- **Authors:** Christian Szegedy
- **Venue:** CICM 2020 (Intelligent Computer Mathematics)
- **Link:** [Springer](https://link.springer.com/chapter/10.1007/978-3-030-53518-6_1) | [Google Research](https://research.google/pubs/a-promising-path-towards-autoformalization-and-general-artificial-intelligence/)
- **Significance:** The seminal position paper that laid out the vision for autoformalization as a research program. Szegedy argued that autoformalization -- not end-to-end neural reasoning -- is the most promising path to building systems capable of general mathematical reasoning. He envisioned LLMs translating informal math into formal representations, with proof assistants providing the verification backbone.

**"Autoformalization with Large Language Models"**
- **Authors:** Yuhuai Wu, Albert Q. Jiang, Wenda Li, Markus Rabe, Charles Staats, Mateja Jamnik, Christian Szegedy
- **Venue:** NeurIPS 2022
- **Link:** [NeurIPS Proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/d0c6bc641a56bebee9d985b937307367-Abstract-Conference.html) | [arXiv](https://arxiv.org/abs/2205.12615)
- **Significance:** The first large-scale demonstration that LLMs (specifically Codex) can perform autoformalization. Showed that few-shot prompting alone could correctly translate 25.3% of mathematical competition problems into formal Isabelle/HOL specifications. Using these autoformalized theorems as training data improved the MiniF2F benchmark proof rate from 29.6% to 35.2%. Established the paradigm of using LLMs as the translation engine.

### Landmark Papers (2022-2023)

**"Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs"**
- **Authors:** Albert Q. Jiang, Sean Welleck, Jin Peng Zhou, Wenda Li, Jiacheng Liu, Mateja Jamnik, Timothee Lacroix, Guillaume Lample, Yuhuai Wu
- **Venue:** ICLR 2023 (Oral)
- **Link:** [OpenReview](https://openreview.net/forum?id=SMa9EAovKMC) | [arXiv](https://arxiv.org/abs/2210.12283)
- **Significance:** Introduced the Draft-Sketch-Prove (DSP) pipeline: (1) an LLM "drafts" an informal proof, (2) it maps the informal proof to a formal proof sketch, (3) an automated prover fills in the gaps. Enhanced the automated prover from 20.9% to 39.3% on competition problems. Demonstrated the power of using informal reasoning as a scaffold for formal proofs.

**"Baldur: Whole-Proof Generation and Repair with Large Language Models"**
- **Authors:** Emily First, Markus N. Rabe, Talia Ringer, Yuriy Brun
- **Venue:** ESEC/FSE 2023
- **Link:** [arXiv](https://arxiv.org/abs/2303.04910) | [ACM](https://dl.acm.org/doi/10.1145/3611643.3616243)
- **Significance:** Demonstrated for the first time that whole-proof generation (producing an entire proof at once rather than step-by-step search) is viable. Fine-tuned LLMs on Isabelle/HOL proofs and combined generation with a repair model that fixes failed proofs using error messages. Proved 65.7% of theorems when combined with the Thor prover.

**"Formal Mathematics Statement Curriculum Learning"**
- **Authors:** Stanislas Polu, Jesse Michael Han, Kunhao Zheng, Mantas Baksys, Igor Babuschkin, Ilya Sutskever
- **Venue:** ICLR 2023
- **Significance:** Proposed expert iteration for neural theorem proving in Lean, where the model trains on its own successful proofs. Established curriculum learning as an effective strategy for scaling formal mathematics.

**"ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics"**
- **Authors:** Zhangir Azerbayev, Bartosz Piotrowski, Hailey Schoelkopf, Edward W. Ayers, Dragomir Radev, Jeremy Avigad
- **Venue:** arXiv 2023
- **Link:** [arXiv](https://arxiv.org/abs/2302.12433)
- **Significance:** Introduced the ProofNet benchmark (371 parallel theorem statements in natural language and Lean 3) drawn from undergraduate textbooks. Provided a systematic evaluation framework for autoformalization beyond competition math.

### Recent Papers (2024-2025)

**"LEGO-Prover: Neural Theorem Proving with Growing Libraries"**
- **Authors:** Haiming Wang, Huajian Xin, Chuanyang Zheng, Lin Li, Zhengying Liu, Qingxing Cao, Yinya Huang, Jing Xiong, Han Shi, Enze Xie, Jian Yin, Zhenguo Li, Xiaodan Liang
- **Venue:** ICLR 2024 (Oral)
- **Link:** [OpenReview](https://openreview.net/forum?id=3f5PALef5B)
- **Significance:** Introduced a skill library approach where verified lemmas are stored and reused. Advanced miniF2F pass rates from 48.0% to 57.0% (valid) and 45.5% to 50.0% (test).

**"Process-Driven Autoformalization in Lean 4"**
- **Authors:** Jianqiao Lu, Yingjia Wan, Zhengying Liu, Yinya Huang, Haiming Wang, Zhicheng Yang, Jing Tang, Zhijiang Guo
- **Venue:** arXiv 2024
- **Link:** [arXiv](https://arxiv.org/abs/2406.01940) | [GitHub](https://github.com/rookie-joe/PDA)
- **Significance:** Introduced the FormL4 benchmark and a process-driven autoformalization (PDA) framework that leverages Lean 4 compiler feedback (type errors, tactic failures) to iteratively improve formalization. Showed that process-supervised verification significantly enhances autoformalization quality.

**"Multilingual Mathematical Autoformalization"**
- **Authors:** Albert Q. Jiang, Wenda Li, Mateja Jamnik
- **Venue:** arXiv 2023 / Under review ICLR 2024
- **Link:** [arXiv](https://arxiv.org/abs/2311.03755)
- **Significance:** Demonstrated that fine-tuning on multiple formal languages (Isabelle + Lean) simultaneously improves autoformalization performance in each language. Showed significant cross-lingual transfer between formal languages, with token accuracies exceeding 90%.

**"Lean-ing on Quality: How High-Quality Data Beats Diverse Multilingual Data in AutoFormalization"**
- **Authors:** Danielle Robinson et al.
- **Venue:** arXiv 2025
- **Link:** [arXiv](https://arxiv.org/abs/2502.15795)
- **Significance:** Demonstrated that quality-first data generation through distilled backtranslation yields substantially better accuracy than training on large, diverse datasets. A key finding for the data engineering of autoformalization systems.

**"AlphaProof: Olympiad-level Formal Mathematical Reasoning with Reinforcement Learning"**
- **Authors:** Google DeepMind
- **Venue:** Nature 2025
- **Link:** [Nature](https://www.nature.com/articles/s41586-025-09833-y) | [DeepMind Blog](https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/)
- **Significance:** AlphaProof solved 4 of 6 problems at IMO 2024, achieving silver-medal level performance. It uses reinforcement learning (inspired by AlphaZero) to learn formal proving in Lean, bootstrapping from millions of autoformalized problems. Guarantees 100% correctness through formal verification.

**"DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning"**
- **Authors:** DeepSeek AI
- **Venue:** arXiv 2025
- **Link:** [arXiv](https://arxiv.org/abs/2504.21801) | [GitHub](https://github.com/deepseek-ai/DeepSeek-Prover-V2)
- **Significance:** Achieved 88.9% pass ratio on MiniF2F-test and solved 49/658 PutnamBench problems. Uses a recursive theorem proving pipeline that decomposes problems into informal reasoning (chain-of-thought) and formal subgoals before proving. Released in 7B and 671B parameter versions.

**"Kimina-Prover Preview: Towards Large Formal Reasoning Models"**
- **Authors:** Moonshot AI (Kimi)
- **Venue:** arXiv 2025
- **Link:** [arXiv](https://arxiv.org/abs/2504.11354)
- **Significance:** Pioneered a reasoning-driven exploration paradigm for formal theorem proving, achieving 80.7% on miniF2F with pass@8192. Built on the Kimi k1.5 reinforcement learning pipeline.

**"HERALD: A Natural Language Annotated Lean 4 Dataset"**
- **Venue:** ICLR 2025
- **Link:** [ICLR Proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/file/8c2bb821410066459be64d03a4dc5719-Paper-Conference.pdf)
- **Significance:** Created 580K NL-FL statement pairs and 45K NL-FL proof pairs, one of the largest resources for training autoformalization models.

**"ProofBridge: Auto-Formalization of Natural Language Proofs in Lean via Joint Embeddings"**
- **Venue:** arXiv 2025
- **Link:** [arXiv](https://arxiv.org/abs/2510.15681)
- **Significance:** Introduced joint embeddings for cross-modal retrieval between natural language and formal proofs, improving semantic correctness by +31.14% over strong baselines (GPT-5, Gemini-2.5, Kimina-Prover).

**"Autoformalization in the Era of Large Language Models: A Survey"**
- **Venue:** arXiv 2025
- **Link:** [arXiv](https://arxiv.org/abs/2505.23486)
- **Significance:** The most comprehensive survey of the field as of 2025. Covers approaches, benchmarks, datasets, and open problems. An essential reference for anyone entering the field.

---

## 3. Key Research Groups and Labs

### Google DeepMind (formerly Google Brain / Google Research)

- **Key people:** Christian Szegedy (former; now at Mathematics Inc.), Markus Rabe, Yuhuai Wu (former), Charles Staats
- **Key contributions:** The original autoformalization vision paper (Szegedy 2020), the seminal LLM autoformalization paper (Wu et al. 2022), AlphaProof (IMO 2024 silver medal), AlphaGeometry
- **Focus:** Reinforcement learning for formal proving, autoformalization at scale, competition mathematics
- **Link:** [DeepMind Research](https://deepmind.google/research/)

### Meta FAIR (Fundamental AI Research)

- **Key people:** Kaiyu Yang, Guillaume Lample, Timothee Lacroix
- **Key contributions:** LeanDojo and ReProver (retrieval-augmented theorem proving), COPRA (in-context learning for provers), autoformalizing Euclidean geometry
- **Focus:** Open-source tools for neural theorem proving, retrieval-augmented approaches
- **Link:** [LeanDojo](https://leandojo.org/)

### Microsoft Research

- **Key contributions:** IndiMathBench (autoformalization benchmark for Indian mathematics competitions), research on evaluation methodology
- **Focus:** Robust evaluation of autoformalization, multilingual and multicultural mathematical reasoning
- **Link:** [Microsoft Research](https://www.microsoft.com/en-us/research/)

### University of Cambridge (Cambridge Automated Reasoning Group)

- **Key people:** Albert Q. Jiang (now at Mistral AI), Wenda Li, Mateja Jamnik
- **Key contributions:** Autoformalization with LLMs (NeurIPS 2022), Draft-Sketch-Prove (ICLR 2023), Multilingual Mathematical Autoformalization, MMA dataset
- **Focus:** LLM-based translation between informal and formal mathematics, multilingual autoformalization
- **Link:** [Albert Jiang's page](https://albertqjiang.github.io/)

### Carnegie Mellon University

- **Key people:** Sean Welleck, Jeremy Avigad
- **Key contributions:** ProofNet benchmark, Draft-Sketch-Prove (collaboration), Mathematics in Lean textbook, neural theorem proving tutorials
- **Focus:** Bridging informal and formal reasoning, educational resources for formal mathematics
- **Link:** [Sean Welleck](https://wellecks.com/)

### UT Austin + Google DeepMind

- **Key people:** Swarat Chaudhuri (dual appointment)
- **Key contributions:** "Formal Mathematical Reasoning: A New Frontier in AI" survey, neurosymbolic programming
- **Focus:** Programming languages meets formal methods meets machine learning

### DeepSeek AI

- **Key contributions:** DeepSeek-Prover (v1 and v2), large-scale synthetic data generation for formal proofs
- **Focus:** Open-source theorem proving models, curriculum learning with synthetic data
- **Link:** [GitHub](https://github.com/deepseek-ai/DeepSeek-Prover-V2)

### Moonshot AI (Kimi)

- **Key contributions:** Kimina-Prover, reasoning-driven exploration for formal theorem proving
- **Focus:** Reinforcement learning for formal reasoning

### Morph Labs / Mathematics Inc.

- **Key people:** Christian Szegedy (Chief Scientist / Founder)
- **Key contributions:** Formalization of the strong prime number theorem via autoformalization agent "Gauss"
- **Focus:** "Verified superintelligence" via autoformalization -- the thesis that autoformalization is the path to safe, verifiable AI
- **Link:** [Morph Labs](https://www.morph.so/blog/verified-superintelligence)

### Harmonic AI

- **Key contributions:** Aristotle prover (2025 IMO, formally verified solutions to 5 of 6 problems)
- **Focus:** Industrial-strength formal theorem proving

---

## 4. Approaches and Techniques

### 4.1 Few-Shot Prompting

The simplest approach: provide an LLM with a few examples of (informal statement, formal statement) pairs in the prompt, then ask it to translate a new informal statement.

**How it works:**
1. Construct a prompt with 3-10 examples of informal-to-formal translations
2. Append the target informal statement
3. Sample the LLM's output
4. (Optionally) verify with the proof assistant's type checker

**Strengths:** No training required, works with any capable LLM, easy to iterate on prompt design.
**Weaknesses:** Limited by context window, sensitive to example selection, no learning from failures.

**Key result:** Wu et al. (2022) achieved 25.3% accuracy on competition problems with few-shot Codex.

### 4.2 Fine-Tuning on Formal Corpora

Train or fine-tune LLMs on parallel informal-formal datasets or on formal proof corpora directly.

**Data sources:**
- Mathlib (Lean 4): 210K+ theorems and definitions
- Archive of Formal Proofs (Isabelle): large collection of formalized theories
- HERALD: 580K NL-FL pairs
- Synthetic data from backtranslation (see below)

**Key result:** Fine-tuning on multilingual formal data (Isabelle + Lean simultaneously) yields token accuracies above 90% (Jiang et al. 2023).

### 4.3 Backtranslation (Informalization + Re-formalization)

A technique borrowed from machine translation: generate synthetic training data by translating in the reverse direction.

**Pipeline:**
1. Take a large corpus of formal statements (e.g., from mathlib)
2. Use an LLM to "informalize" them -- translate formal statements into natural language
3. Use these (informal, formal) pairs to train an autoformalization model
4. The trained model translates new informal statements into formal ones

**Why it works:** Formal-to-informal translation is easier than the reverse direction (the formal statement is unambiguous), so the informalization step produces high-quality synthetic data.

**Key finding:** Robinson et al. (2025) showed that high-quality, curated backtranslation data outperforms large diverse datasets. Quality beats quantity.

### 4.4 Draft-Sketch-Prove Pipeline

A three-stage approach that uses informal proofs as scaffolding:

1. **Draft:** An LLM generates an informal proof of the theorem
2. **Sketch:** The informal proof is mapped to a formal proof sketch (a partial proof with gaps marked by `sorry` or `_`)
3. **Prove:** An automated tactic prover (like `aesop`, `omega`, or a learned prover) fills in the gaps

**Significance:** This mirrors how human mathematicians work -- first understand the high-level argument, then fill in the details. By decomposing the problem, each stage becomes more tractable.

### 4.5 Iterative Repair with Compiler Feedback

Use the proof assistant's error messages as feedback to iteratively refine the formalization.

**Pipeline:**
1. Generate an initial formalization attempt
2. Submit to the Lean/Isabelle compiler
3. If it fails, feed the error message back to the LLM
4. Generate a corrected version
5. Repeat until compilation succeeds or a budget is exhausted

**Key insight:** Formal languages have exact compilers that produce precise error messages. Unlike natural language tasks where feedback is fuzzy, autoformalization has a hard oracle: the proof assistant either accepts or rejects.

**Variants:**
- **Process-Driven Autoformalization (PDA):** Uses Lean 4 compiler feedback at every step, not just the final result (Lu et al. 2024)
- **Baldur's repair model:** A separate LLM trained specifically to fix failed proofs given error messages (First et al. 2023)

### 4.6 Retrieval-Augmented Formalization

Retrieve relevant formal definitions, lemmas, and proof patterns from a library before generating the formalization.

**Why it matters:** Autoformalization requires knowing which library definitions to use. A statement about "continuous functions" needs to resolve to the specific `Continuous` definition in mathlib, not a generic notion.

**Tools:**
- **LeanDojo / ReProver:** Retrieves relevant premises from mathlib using learned embeddings (Yang et al.)
- **ProofBridge:** Uses joint embeddings for cross-modal retrieval between NL and FL (2025)
- **LEGO-Prover:** Maintains a growing skill library of verified lemmas (Wang et al. 2024)

### 4.7 Reinforcement Learning from Proof Verification

Train the model using the proof assistant's accept/reject signal as a reward.

**Approach:**
1. Generate candidate formalizations/proofs
2. Submit to proof assistant
3. Use acceptance as reward signal
4. Train via RL (PPO, expert iteration, or AlphaZero-style MCTS)

**Key systems:**
- **AlphaProof:** AlphaZero-style RL trained on millions of autoformalized problems, achieves IMO silver-medal level
- **DeepSeek-Prover:** Expert iteration where the model trains on its own successful proofs
- **Kimina-Prover:** Reasoning-driven exploration via Kimi k1.5 RL pipeline

---

## 5. Benchmarks and Datasets

### Evaluation Benchmarks

| Benchmark | Source | Size | Formal Languages | Difficulty Level |
|-----------|--------|------|-------------------|-----------------|
| **miniF2F** | AMC, AIME, IMO competitions | 244 statements | Lean, Isabelle, Metamath | High school / competition |
| **ProofNet** | Undergraduate textbooks | 371 statements | Lean 3 | Undergraduate |
| **PutnamBench** | Putnam Competition | 1724 formalizations | Lean 4 (672), Isabelle (640), Coq (412) | Undergraduate competition |
| **FormL4** | Process-driven autoformalization | Varies | Lean 4 | Mixed |
| **FIMO** | IMO problems | Varies | Multiple | Olympiad |
| **IndiMathBench** | Indian math competitions | Varies | Lean 4 | Competition |
| **FormalMATH** | Diverse mathematical domains | Large | Lean 4 | Mixed |

**miniF2F** ([GitHub](https://github.com/openai/miniF2F)): The most widely used benchmark. Created by OpenAI, it contains 244 formalized competition problems (AMC, AIME, IMO). Version 1 was frozen in August 2021. Two corrected versions exist: simplified and competition-level. Limitation: restricted to high school algebra and number theory.

**ProofNet** ([Paper](https://arxiv.org/abs/2302.12433)): 371 problems from popular undergraduate pure mathematics textbooks. Bridges undergraduate-level mathematics with formal proofs. Focuses on analysis and algebra.

**PutnamBench** ([Website](https://trishullab.github.io/PutnamBench/)): The largest multilingual formalization benchmark, covering problems from the William Lowell Putnam Mathematical Competition. Requires broad mathematical knowledge (analysis, abstract algebra, topology). Current neural provers can only solve a handful of problems, making it a difficult open challenge.

### Training Datasets

| Dataset | Size | Content |
|---------|------|---------|
| **mathlib** | 210K+ theorems | Lean 4 mathematical library |
| **HERALD** | 580K NL-FL statement pairs, 45K proof pairs | Natural language annotated Lean 4 |
| **Goedel-Pset-v1** | 1.64M formalized statements | LLM-generated Lean 4 formalizations |
| **Archive of Formal Proofs** | Large | Isabelle/HOL formalized theories |
| **MMA** | Large | Multilingual (Isabelle + Lean) informal-formal pairs |
| **Proof Pile** | ~500MB | Aggregated formal proofs (multiple languages) |
| **LeanDojo Benchmark** | Derived from mathlib | Lean 4 premises and proofs |

---

## 6. Current State of the Art

### What Works (as of early 2026)

**Statement autoformalization (informal theorem -> formal theorem):**
- Best models achieve ~97% syntactic correctness on structured inputs (miniF2F)
- Semantic accuracy varies: 81-88% depending on domain and evaluation protocol
- GPT-5 and DeepSeek-Prover-V2 lead on most benchmarks
- Fine-tuned models on quality data can exceed 90% token accuracy

**Proof generation and autoformalization combined:**
- DeepSeek-Prover-V2 (671B): 88.9% on MiniF2F-test
- AlphaProof: Solved 4/6 IMO 2024 problems (silver medal level)
- Aristotle (Harmonic): Solved 5/6 IMO 2025 problems
- Kimina-Prover: 80.7% on miniF2F (pass@8192)

**Formal verification as quality guarantee:**
- Unlike informal reasoning, formal proofs are 100% correct when accepted
- This provides an absolute ground truth for evaluation

### What Does Not Work

**Reported vs. actual accuracy is misleading:**
- While models report ~97% autoformalization accuracy, human evaluation reveals much lower semantic fidelity
- When combining autoformalization with theorem proving, combined accuracy drops to ~34.8% after checking final proofs against original problem statements
- LLM-based evaluation of autoformalization quality is unreliable; human expert evaluation remains necessary

**Semantic preservation:**
- Models struggle to preserve precise semantic details in advanced mathematical domains
- Non-standard or ambiguous natural language inputs produce misaligned definitions, missing premises, or payoff misorderings
- Paraphrasing sensitivity: semantically equivalent inputs yield substantially different outputs

**Scaling challenges:**
- Research-level mathematics remains largely out of reach (45.1% accuracy on undergraduate content, much lower on research content)
- Long, compositionally complex proofs are difficult
- Underrepresented mathematical subdisciplines (topology, category theory, PDEs) perform poorly
- The formal proof corpus is small (~500MB Proof Pile) compared to code corpora (terabytes)

**Evaluation challenges:**
- Automatic evaluation metrics (compilation success, token accuracy) do not capture semantic correctness
- The most reliable evaluation remains manual checking by experts familiar with the proof assistant
- There is no consensus on standardized evaluation protocols

### Accuracy Trajectory

| Year | System | Benchmark | Result |
|------|--------|-----------|--------|
| 2022 | Codex (few-shot) | miniF2F | 25.3% autoformalization, 35.2% proving |
| 2023 | DSP | miniF2F | 39.3% proving |
| 2023 | Baldur + Thor | Isabelle theorems | 65.7% proving |
| 2024 | LEGO-Prover | miniF2F-test | 50.0% proving |
| 2024 | AlphaProof | IMO 2024 | 4/6 problems (silver) |
| 2025 | DeepSeek-Prover-V2 | miniF2F-test | 88.9% proving |
| 2025 | Kimina-Prover | miniF2F | 80.7% (pass@8192) |
| 2025 | Aristotle | IMO 2025 | 5/6 problems |
| 2025 | GPT-5 | PutnamBench | 7% (42/660) |

---

## 7. Connection to Neuro-Symbolic AI

Autoformalization is, at its core, a neuro-symbolic task. It is perhaps the purest example of the neuro-symbolic paradigm in practice:

### The Neural Component

The **neural** side handles perception and translation:
- Reading and understanding informal mathematical text (natural language understanding)
- Recognizing mathematical patterns and structures in prose
- Generating candidate formal representations
- Handling ambiguity, implicit assumptions, and contextual references

LLMs excel at this because they have been trained on vast corpora of mathematical text, code, and natural language. They can parse the *meaning* of "for every prime greater than 2" and recognize it as universal quantification over a specific set.

### The Symbolic Component

The **symbolic** side handles verification and reasoning:
- Proof assistants (Lean, Isabelle, Coq) provide exact verification
- Type checkers enforce logical consistency
- Tactic engines perform automated deduction
- Library search resolves definitions against formalized mathematical knowledge

The symbolic side provides what neural systems cannot: certainty. When Lean accepts a proof, it is correct. Period. No hallucination, no approximation, no confidence score -- binary correctness.

### The Neuro-Symbolic Bridge

The autoformalization pipeline is a textbook neuro-symbolic architecture:

```
Informal math (NL) --> [Neural: LLM translation] --> Formal candidate --> [Symbolic: Proof assistant] --> Verified/Rejected
                                ^                                                      |
                                |______________________ feedback loop _________________|
```

This architecture combines:
1. **Neural perception** of informal content (what the math "means")
2. **Symbolic verification** of the formal output (whether it is logically valid)
3. **Feedback loops** from symbolic to neural (compiler errors guide refinement)

### Broader Neuro-Symbolic Connections

The autoformalization paradigm has been extended beyond mathematics:

- **Policy formalization:** Translating natural language regulations and laws into formal logic for compliance verification (neurosymbolic approaches achieving 99%+ soundness)
- **Program synthesis:** Translating natural language specifications into formally verified code
- **Robotics:** Formalizing natural language instructions into verifiable action plans

A recent paper, "A Neurosymbolic Approach to Natural Language Formalization and Verification" (2025), describes a two-stage framework that uses LLMs to formalize natural language policies, then uses symbolic inference to validate logical correctness -- achieving near-zero false positive rates.

---

## 8. Relevance to Sigil

Sigil and autoformalization share a deep structural affinity. Both are instances of the same fundamental pattern: **neural perception of natural language into symbolic, verifiable representations.**

### Parallel Architecture

| Autoformalization | Sigil |
|-------------------|-------|
| Informal math (NL) | Domain expert's rules (constrained NL) |
| LLM translation | Neural parser |
| Formal proof language (Lean) | .sigil AST |
| Proof assistant verification | Type checker + symbolic interpreter |
| Execution trace | Execution trace |
| Verified proof | Auditable decision + trace |

### Shared Design Principles

1. **Neural for perception, symbolic for reasoning.** Autoformalization uses LLMs to *understand* informal math but relies on proof assistants for *verification*. Sigil uses LLMs to *parse* natural language intent but relies on the symbolic engine for *decisions*. In both cases, LLMs never make the final judgment.

2. **Deterministic verification.** A proof assistant's accept/reject is deterministic. Sigil's symbolic execution is deterministic. The neural component introduces interpretation, but the symbolic component provides guarantees.

3. **Constrained natural language as the interface.** Autoformalization works best on *structured* informal math (textbook style, competition problems) rather than free-form mathematical prose. Sigil is designed as constrained NL -- readable like English, but parseable as a PEG grammar. Both occupy the sweet spot between full natural language and pure formal syntax.

4. **Traces as first-class output.** In formal proving, the proof itself is the trace of reasoning. In Sigil, every rule evaluation produces an auditable execution trace. Both systems treat the reasoning process as a primary artifact, not debugging metadata.

5. **Feedback loops.** Autoformalization systems use compiler errors to iteratively refine formalizations. Sigil's type checker produces diagnostics that guide correction. Both architectures benefit from tight symbolic-to-neural feedback.

### What Sigil Can Learn from Autoformalization

- **Iterative refinement via symbolic feedback:** The PDA framework's use of compiler feedback to improve LLM output is directly applicable to Sigil's neural parser. When the parser fails on an LLM-generated .sigil file, the error messages could be fed back to the LLM for correction.

- **Retrieval-augmented generation:** Just as autoformalization benefits from retrieving relevant library definitions, Sigil's neural parser could retrieve relevant rule templates, type definitions, and examples to improve generation quality.

- **Quality-controlled synthetic data:** The backtranslation paradigm (formalize -> informalize -> re-formalize) could be used to generate training data for Sigil's neural parser: take existing .sigil programs, have an LLM describe them in natural language, then train the parser to reconstruct them.

- **Benchmarking methodology:** Autoformalization's careful distinction between syntactic correctness and semantic fidelity is important for evaluating Sigil's neural parser. A .sigil program that compiles is not necessarily the one the user intended.

### What Autoformalization Can Learn from Sigil

- **Constrained NL design:** Sigil demonstrates that you can design a formal language that *reads* like natural language while maintaining deterministic parseability. Formal proof languages like Lean are powerful but alien to non-experts. A "Sigil-like" proof language could lower the barrier to formal mathematics.

- **Domain-specific neuro-symbolic architecture:** Sigil's architecture (lexer -> parser -> AST -> type checker -> interpreter -> trace) is a clean, modular pipeline. Autoformalization systems tend to be more ad hoc. A Sigil-style pipeline for autoformalization could improve modularity and debuggability.

---

## 9. Learning Path

### Stage 1: Foundations (Weeks 1-2)

**Understand formal proof assistants:**

1. Work through **"Mathematics in Lean"** by Jeremy Avigad and Patrick Massot
   - [Online textbook](https://leanprover-community.github.io/mathematics_in_lean/)
   - Hands-on introduction to Lean 4 and formal proving
   - Free, interactive, well-structured

2. Read **"Theorem Proving in Lean 4"** (the official documentation)
   - [Online book](https://lean-lang.org/theorem_proving_in_lean4/)
   - More comprehensive, covers the type theory underlying Lean

**Understand the problem:**

3. Read Szegedy's position paper: **"A Promising Path Towards Autoformalization and General Artificial Intelligence"** (2020)
   - [Springer](https://link.springer.com/chapter/10.1007/978-3-030-53518-6_1)
   - 15 pages, accessible, sets the vision

### Stage 2: Core Research (Weeks 3-4)

4. Read the seminal paper: **"Autoformalization with Large Language Models"** (Wu et al., NeurIPS 2022)
   - [arXiv](https://arxiv.org/abs/2205.12615)
   - Establishes the paradigm

5. Read **"Draft, Sketch, and Prove"** (Jiang et al., ICLR 2023)
   - [arXiv](https://arxiv.org/abs/2210.12283)
   - The most influential pipeline paper

6. Watch Tony Wu's talk: **"Autoformalization with Large Language Models"** at IPAM/UCLA
   - [Class Central](https://www.classcentral.com/course/youtube-tony-wu-autoformalization-with-large-language-models-ipam-at-ucla-169266)
   - 55 minutes, accessible overview

### Stage 3: Modern Systems (Weeks 5-6)

7. Read **"DeepSeek-Prover-V2"** (2025) for the current state of the art
   - [arXiv](https://arxiv.org/abs/2504.21801)
   - Covers recursive decomposition, chain-of-thought + formal subgoals

8. Read the **AlphaProof paper** in Nature (2025)
   - [Nature](https://www.nature.com/articles/s41586-025-09833-y)
   - RL-based formal proving at competition level

9. Read **"Process-Driven Autoformalization in Lean 4"** (2024)
   - [arXiv](https://arxiv.org/abs/2406.01940)
   - Compiler feedback as training signal

### Stage 4: Survey and Breadth (Weeks 7-8)

10. Read the comprehensive survey: **"Autoformalization in the Era of Large Language Models"** (2025)
    - [arXiv](https://arxiv.org/abs/2505.23486)
    - Covers the entire field systematically

11. Read **"Formal Mathematical Reasoning: A New Frontier in AI"** (2024)
    - [arXiv](https://arxiv.org/abs/2412.16075)
    - Broader context of AI for mathematics

12. Read **"A Survey on Deep Learning for Theorem Proving"** (COLM 2024)
    - [GitHub](https://github.com/zhaoyu-li/DL4TP)
    - Comprehensive paper list and taxonomy

### Stage 5: Hands-On (Ongoing)

13. Explore **LeanDojo** -- open-source toolkit for neural theorem proving
    - [LeanDojo](https://leandojo.org/)
    - Interact with Lean programmatically, train your own provers

14. Try **autoformalization yourself** -- take a textbook theorem, use GPT-4/Claude to translate it to Lean 4, then try to fix the result using Lean's error messages

15. Follow the **CMU Neural Theorem Proving Tutorial**
    - [GitHub](https://github.com/cmu-l3/ntptutorial-II)
    - Practical implementation of DSP and related methods

### Stage 6: Advanced Topics

16. Listen to the podcast: **"Autoformalization and Verifiable Superintelligence with Christian Szegedy"** (TWIML #745)
    - [Spotify](https://open.spotify.com/episode/5eWM77NhUjABDKkMw5elmO)
    - Szegedy's current vision and Mathematics Inc.

17. Read **"Improving Autoformalization using Type Checking"** (EMNLP 2025)
    - [arXiv](https://arxiv.org/abs/2406.07222)
    - Careful analysis of evaluation methodology

18. Read about the **Polynomial Freiman-Ruzsa conjecture formalization**
    - [Terence Tao's blog post](https://terrytao.wordpress.com/2023/11/18/formalizing-the-proof-of-pfr-in-lean4-using-blueprint-a-short-tour/)
    - Real-world example of collaborative formalization

---

## 10. Open Problems

### Fundamental Challenges

**1. Semantic fidelity at scale.**
Current systems can produce syntactically correct formalizations that are semantically wrong -- they compile but do not mean what the original informal statement said. Bridging this gap requires deeper understanding of mathematical meaning, not just syntactic translation. The discrepancy between reported accuracy (~97%) and actual semantic correctness (~35% end-to-end) is the field's most pressing problem.

**2. Implicit knowledge and assumptions.**
Informal mathematics is full of unstated assumptions: "let f be a nice function" (meaning smooth, or continuous, or measurable, depending on context). Resolving these requires understanding the mathematical context at a deep level. Current systems have no reliable way to detect and fill in implicit assumptions.

**3. Research-level mathematics.**
Almost all current benchmarks focus on competition math or undergraduate textbooks. Autoformalization of research papers -- with novel definitions, ad hoc notation, and proofs that rely on intuition -- remains largely unsolved. The difficulty spans diverse domains (algebra, analysis, topology, PDEs, program synthesis) with vastly different formal vocabulary.

**4. Data scarcity.**
High-quality parallel informal-formal datasets are rare. The formal proof corpus is tiny compared to code or natural language corpora. While synthetic data (backtranslation) helps, it does not capture the full diversity of mathematical writing.

### Technical Open Problems

**5. Evaluation methodology.**
There is no consensus on how to evaluate autoformalization quality. Compilation success is necessary but not sufficient. Human evaluation is reliable but does not scale. LLM-based evaluation has been shown to be unreliable. Developing automated semantic evaluation metrics is an open problem.

**6. Entity linking and library grounding.**
When an informal statement mentions "the fundamental theorem of calculus," which of the dozens of formal versions in mathlib should be used? This entity linking problem -- grounding informal mathematical concepts to specific formal library entries -- is unsolved at scale.

**7. Long and compositional proofs.**
Current systems struggle with proofs that span many pages or require combining techniques from multiple areas of mathematics. The attention window of LLMs, even at 128K+ tokens, is insufficient for the longest mathematical arguments.

**8. Robustness to paraphrasing.**
Semantically equivalent informal statements (e.g., "p is prime" vs. "p has no divisors other than 1 and itself") can yield vastly different formal outputs. A robust autoformalization system should be invariant to meaning-preserving rephrasing.

### Frontier Directions

**9. Interactive and modular autoformalization.**
Rather than end-to-end translation, build systems where humans and AI collaborate: the AI proposes formalizations, humans correct them, and the system learns from corrections. The Blueprint tool used in the PFR conjecture formalization hints at this future.

**10. Creative mathematical reasoning.**
The long-term vision: AI systems that do not just formalize existing mathematics but propose new conjectures, explore novel proof strategies, and assist human mathematicians in discovering new results. This requires autoformalization as a foundation (to state and verify conjectures formally) but goes far beyond translation.

**11. Cross-domain formalization.**
Extending autoformalization beyond pure mathematics to physics, economics, law, and software engineering. Each domain has its own informal-to-formal gap, and the techniques developed for mathematical autoformalization may transfer -- but the challenge is adapting to domains without the clean formal foundations of mathematics.

**12. Verified superintelligence.**
Szegedy's thesis: autoformalization is the path to building AI systems whose reasoning can be formally verified. If an AI can express its arguments in Lean and have them machine-checked, we have a fundamentally new kind of AI safety guarantee. This is speculative but represents the most ambitious vision for where the field is heading.

---

## Appendix: Formal Proof Assistants at a Glance

| System | Foundation | Language | Key Strengths | Used By |
|--------|-----------|----------|---------------|---------|
| **Lean 4** | Dependent type theory (CIC) | Functional | Modern, fast, growing mathlib (210K+ theorems), strong community | DeepMind, DeepSeek, most new research |
| **Isabelle/HOL** | Higher-order logic | Declarative (Isar) | Mature, human-readable proofs, powerful automation (Sledgehammer) | Cambridge, early autoformalization work |
| **Coq** | Calculus of Inductive Constructions | Tactic-based (Ltac) | Mature, strong extraction to code, used in verified software (CompCert) | Program verification, PutnamBench |
| **Metamath** | Set theory (ZFC) | Minimal | Extremely simple kernel, all proofs machine-checkable | miniF2F (partial) |

Lean 4 has emerged as the dominant platform for autoformalization research due to its modern design, fast compiler, growing mathematical library, and strong community tooling. Most new systems (DeepSeek-Prover, AlphaProof, Kimina-Prover) target Lean 4.

---

*Last updated: March 2026*
*Part of the Sigil Language Project research documentation*
