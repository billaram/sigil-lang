# Key Papers Reading List: Neuro-Symbolic AI, Autoformalization, and AI Theorem Proving

An annotated, curated reading list of the most important papers at the intersection of neuro-symbolic AI, autoformalization, AI-assisted theorem proving, and formal verification. Organized by topic and difficulty level.

**How to use this list:** Start with Beginner papers to build intuition, then progress to Intermediate for technical depth, and Advanced for cutting-edge research. Papers within each section are roughly ordered by foundational importance.

---

## 1. Foundational Neuro-Symbolic AI

These papers establish the theoretical frameworks and taxonomies that define the field.

### 1.1 Kautz, H. "The Third AI Summer." AI Magazine, 43(1), 105--125, 2022.
- **Originally presented:** AAAI 2020 Robert S. Engelmore Memorial Lecture
- **Summary:** Kautz introduced the influential six-type taxonomy of neuro-symbolic integration, ranging from loose coupling (Type 1: symbolic inputs/outputs to neural nets) to tight coupling (Type 6: neural networks with internal symbolic reasoning). This taxonomy provides the standard vocabulary for classifying any neuro-symbolic system, including Sigil, which sits at the Type 3 (Neuro;Symbolic -- pipeline) boundary with aspirations toward Type 5 (truly integrated neurosymbolic). Essential reading for anyone entering the field.
- **Difficulty:** Beginner
- **Link:** https://ojs.aaai.org/index.php/aimagazine/article/view/18137

### 1.2 Garcez, A.S.d. and Lamb, L.C. "Neurosymbolic AI: The 3rd Wave." Artificial Intelligence Review, 56, 12387--12406, 2023.
- **Summary:** The definitive position paper arguing that neurosymbolic AI represents the third wave of AI (after symbolic AI and deep learning). Garcez and Lamb identify key ingredients for neurosymbolic systems: knowledge representation integrated with learning, sound explainability, and commonsense reasoning. They propose that the field needs to move beyond simple pipeline architectures toward systems where neural and symbolic components co-evolve. Sigil's architecture directly implements their vision of a symbolic reasoning engine guided by neural perception.
- **Difficulty:** Beginner
- **Link:** https://link.springer.com/article/10.1007/s10462-023-10448-w

### 1.3 Wan, Z. et al. "Neuro-Symbolic AI in 2024: A Systematic Review." arXiv:2501.05435, 2025.
- **Summary:** A comprehensive systematic review analyzing 167 qualifying papers across five core research areas: knowledge representation, learning and inference, logic and reasoning, explainability, and trustworthiness. The review finds that 63% of papers focus on learning and inference while only 35% address logic and reasoning, revealing a gap that languages like Sigil could fill. Provides an up-to-date map of who is doing what in the field.
- **Difficulty:** Beginner
- **Link:** https://arxiv.org/abs/2501.05435

### 1.4 Gibaut, W. "Neurosymbolic AI and its Taxonomy: A Survey." arXiv:2305.08876, 2023.
- **Summary:** Synthesizes six survey papers and four seminal books to produce a unified taxonomy of neurosymbolic AI approaches. Particularly useful for understanding the trade-off spectrum between verifiability and learnability -- systems that are more verifiable tend to be less learnable and vice versa. Sigil's design philosophy explicitly prioritizes verifiability (deterministic symbolic execution) while using the `neural` keyword to introduce controlled learnability.
- **Difficulty:** Beginner
- **Link:** https://arxiv.org/abs/2305.08876

### 1.5 Marra, G. et al. "From Statistical Relational to Neurosymbolic Artificial Intelligence: A Survey." Artificial Intelligence, 328, 104062, 2024.
- **Summary:** Traces the intellectual lineage from statistical relational learning (Markov Logic Networks, Probabilistic Soft Logic) through to modern neurosymbolic frameworks. The survey identifies unifying principles across seemingly different approaches and shows how probabilistic programming languages serve as a bridge between the two traditions. Relevant to Sigil because it contextualizes where rule-based reasoning fits in the broader landscape.
- **Difficulty:** Intermediate
- **Link:** https://www.sciencedirect.com/science/article/pii/S0004370223002084

### 1.6 IJCAI 2025 Survey. "Neuro-Symbolic Artificial Intelligence: Towards Improving the Reasoning Abilities of Large Language Models." IJCAI 2025 Proceedings, 2025.
- **Summary:** Examines neuro-symbolic methods for improving LLM reasoning from three integration perspectives: Symbolic->LLM (injecting structured knowledge into neural models), LLM->Symbolic (using LLMs to generate symbolic representations), and LLM+Symbolic (joint architectures). This three-way classification is directly relevant to Sigil's design, where LLMs generate Sigil code (LLM->Symbolic) and the Sigil engine reasons over it deterministically.
- **Difficulty:** Intermediate
- **Link:** https://www.ijcai.org/proceedings/2025/1195.pdf

---

## 2. Autoformalization

Papers on automatically translating natural language mathematics into formal specifications -- the core capability that connects LLMs to formal reasoning systems.

### 2.1 Szegedy, C. "A Promising Path Towards Autoformalization and General Artificial Intelligence." CICM 2020, Springer LNCS 12236, 3--20, 2020.
- **Summary:** The seminal position paper that launched autoformalization as a serious research direction. Szegedy argues that an AI system capable of reading natural language mathematics and producing machine-verifiable formalizations would represent a major step toward general intelligence. He envisions bootstrapping from unlabeled training data with minimal human interaction. This vision directly parallels Sigil's goal of translating domain expert language into executable formal rules.
- **Difficulty:** Beginner
- **Link:** https://link.springer.com/chapter/10.1007/978-3-030-53518-6_1

### 2.2 Wu, Y., Jiang, A.Q., Li, W., Rabe, M., Staats, C., Jamnik, M., and Szegedy, C. "Autoformalization with Large Language Models." NeurIPS, 2022.
- **Summary:** The breakthrough empirical demonstration that LLMs can perform autoformalization. Showed that Codex could correctly translate 25.3% of mathematical competition problems into formal Isabelle/HOL specifications. More importantly, training a neural theorem prover on autoformalized theorems improved the state-of-the-art on miniF2F from 29.6% to 35.2%. This paper proved that the informal-to-formal translation pipeline is viable and productive, validating the core premise of languages like Sigil that sit at this boundary.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2205.12615

### 2.3 Zhou, J.P., Staats, C., Li, W., Szegedy, C., Weinberger, K.Q., and Wu, Y. "Don't Trust: Verify -- Grounding LLM Quantitative Reasoning with Autoformalization." ICLR, 2024.
- **Summary:** Demonstrates a practical pattern for using autoformalization as a verification layer: LLM solutions are automatically formalized into Isabelle code, then checked for internal consistency. Solutions whose formalizations are inconsistent are rejected, consistently outperforming vanilla majority voting by over 12% on GSM8K. This "generate then verify" pattern is exactly the workflow Sigil enables: LLMs generate .sigil code, the symbolic engine verifies and executes it deterministically.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2403.18120

### 2.4 Lu, J. et al. "Process-Driven Autoformalization in Lean 4." arXiv:2406.01940, 2024.
- **Summary:** Introduces FormL4, a benchmark for evaluating autoformalization in Lean 4, and a Process-Supervised Verifier (PSV) that uses compiler feedback to iteratively improve formalizations. The key insight is that autoformalization benefits from process supervision (checking intermediate steps) rather than just outcome supervision (checking final results). This mirrors Sigil's trace-based execution model where every intermediate reasoning step is auditable.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2406.01940

### 2.5 Rethinking and Improving Autoformalization: Towards a Faithful Metric and a Dependency Retrieval-based Approach. ICLR 2025 (Spotlight).
- **Summary:** Addresses two critical gaps: the lack of faithful automated evaluation for autoformalization, and severe hallucination of formal definitions. Proposes BEq (Bidirectional Extended Definitional Equivalence), an automated neuro-symbolic method to determine equivalence between formal statements, and RAutoformalizer, which retrieves dependent objects from formal libraries. The dependency retrieval approach is analogous to Sigil's module system -- formal statements need context from a library, just as Sigil rules need imports from stdlib modules.
- **Difficulty:** Advanced
- **Link:** https://openreview.net/forum?id=hUb2At2DsQ

---

## 3. AI Theorem Proving

Papers on using neural networks and reinforcement learning to find formal proofs -- the cutting edge of AI reasoning.

### 3.1 Polu, S. and Sutskever, I. "Generative Language Modeling for Automated Theorem Proving." (GPT-f) arXiv:2009.03393, 2020.
- **Summary:** The pioneering work showing that transformer language models can generate formal proofs. GPT-f achieved 56.22% proof closure on Metamath (vs. 21.16% for the prior SOTA) and contributed 23 shortened proofs accepted into the Metamath library -- the first time a deep learning system contributed proofs adopted by a formal mathematics community. Established the paradigm of using language models as tactic generators for interactive theorem provers.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2009.03393

### 3.2 Lample, G., Lacroix, T. et al. "HyperTree Proof Search for Neural Theorem Proving." (HTPS) NeurIPS, 2022.
- **Summary:** Proposes HyperTree Proof Search, an AlphaZero-inspired search algorithm for theorem proving. HTPS treats proof search as a game where the "board state" is the current set of proof obligations. With online training (interleaving search and learning), achieves 82.6% on Metamath and 42% on miniF2F -- dramatic improvements over GPT-f. The "hyper" in the name refers to the fact that proof goals can be linked across branches, making the search tree a hypergraph. This paper demonstrated that RL-based search is essential for scaling theorem proving.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2205.11491

### 3.3 Yang, K. et al. "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models." NeurIPS (Datasets and Benchmarks), 2023.
- **Summary:** Created the first open-source infrastructure for AI theorem proving in Lean 4, including programmatic interaction with the proof environment and fine-grained premise annotations. Their ReProver model uses retrieval-augmented generation to select relevant premises from mathlib before generating tactics, achieving 51.2% on the LeanDojo benchmark (vs. 29.0% for GPT-4). The open tooling enabled an explosion of follow-up work. Essential infrastructure paper for anyone building AI theorem proving systems.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2306.15626

### 3.4 Jiang, A.Q. et al. "Thor: Wielding Hammers to Integrate Language Models and Automated Theorem Provers." NeurIPS, 2022.
- **Summary:** Introduces a framework for combining language models with automated theorem provers (specifically Sledgehammer in Isabelle). The key insight is that language models and symbolic hammers have complementary strengths: language models are good at high-level proof strategy while hammers excel at filling in routine details. Thor achieves strong results on both PISA and miniF2F benchmarks by letting each component do what it does best.
- **Difficulty:** Intermediate
- **Link:** https://proceedings.neurips.cc/paper_files/paper/2022/hash/377c25312668e48f2e531e2f2c422483-Abstract-Conference.html

### 3.5 First, E. et al. "Baldur: Whole-Proof Generation and Repair with Large Language Models." FSE, 2023.
- **Summary:** Shows that LLMs can generate entire proofs at once (not just individual tactics), achieving performance competitive with search-based methods. More importantly, introduces proof repair: when a generated proof fails, the error message is fed back to the LLM for correction. Together with Thor, Baldur proves 65.7% of Isabelle/HOL theorems fully automatically. The repair loop is a powerful pattern that could be adapted for Sigil rule debugging.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2303.04910

### 3.6 Jiang, A.Q., Welleck, S. et al. "Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs." ICLR (Oral), 2023.
- **Summary:** Introduces a three-stage pipeline: (1) an LLM drafts an informal proof in natural language, (2) another LLM translates it into a formal proof sketch with holes, (3) an automated prover fills the holes. This decomposition makes the problem tractable by reducing each step's complexity. The approach works in both human-written and LLM-generated informal proof settings. This draft-sketch-prove pattern maps cleanly onto Sigil's workflow: domain experts draft rules in constrained NL, the parser sketches the formal structure, the interpreter proves/executes.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2210.12283

### 3.7 Wang, H. et al. "LEGO-Prover: Neural Theorem Proving with Growing Libraries." ICLR (Oral), 2024.
- **Summary:** Addresses a fundamental limitation of prior work: fixed theorem libraries. LEGO-Prover builds proofs modularly by decomposing problems into sub-goal lemmas, proving them, and adding them to a growing skill library. Over a proof campaign, it generates 20,000+ reusable lemmas. Advances miniF2F from 48.0% to 57.0%. The idea of building a growing library of verified reasoning components is directly applicable to Sigil's module system and stdlib design.
- **Difficulty:** Advanced
- **Link:** https://openreview.net/forum?id=3f5PALef5B

### 3.8 Polu, S., Han, J.M. et al. "Formal Mathematics Statement Curriculum Learning." ICLR, 2023.
- **Summary:** Shows that expert iteration (interleaving proof search with learning) combined with curriculum learning (starting from easy problems and progressing to hard ones) dramatically outperforms proof search alone at the same compute budget. Applied to miniF2F, the method automatically discovers a curriculum of increasingly difficult problems without requiring ground-truth proofs. Demonstrates that self-play-style training works for theorem proving.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2202.01344

### 3.9 AlphaProof Team. "Olympiad-level formal mathematical reasoning with reinforcement learning." Nature, 2025.
- **Summary:** The landmark result: an AlphaZero-inspired system that earned a silver medal at the 2024 International Mathematical Olympiad by proving solutions in Lean 4. AlphaProof trains on 80 million autoformalized Lean statements and uses test-time reinforcement learning to generate and learn from millions of problem variants. Solved 3 of 5 non-geometry problems including the hardest problem. Represents the current ceiling of AI theorem proving capability and validates the autoformalization + RL approach at scale.
- **Difficulty:** Advanced
- **Link:** https://www.nature.com/articles/s41586-025-09833-y

### 3.10 Lin, H. et al. "Lean-STaR: Learning to Interleave Thinking and Proving." ICLR, 2025.
- **Summary:** Trains language models to generate informal "thoughts" (natural language reasoning) before each formal proof step, inspired by chain-of-thought prompting. Uses retrospective ground-truth tactics to generate synthetic thoughts for training. The interleaving of informal reasoning with formal proving is a key pattern: it shows that the bridge between natural language and formal language is productive in both directions. Directly validates Sigil's approach of constrained natural language as an interface to formal reasoning.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2407.10040

### 3.11 Kumarappan, A. et al. "LeanAgent: Lifelong Learning for Formal Theorem Proving." ICLR, 2025.
- **Summary:** The first lifelong learning framework for theorem proving: LeanAgent continuously improves across 23 Lean repositories without forgetting previously learned knowledge. Uses curriculum learning, dynamic knowledge management, and progressive training. Proves 155 previously unproven theorems in areas like abstract algebra and algebraic topology. Demonstrates that AI theorem provers can scale beyond single benchmarks to evolving mathematical knowledge.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2410.06209

### 3.12 CARTS. "Advancing Neural Theorem Proving with Diversified Tactic Calibration and Bias-Resistant Tree Search." ICLR, 2025.
- **Summary:** Addresses the problem of tactic redundancy in MCTS-based theorem proving: many LLM-suggested tactics are semantically similar, wasting search budget. CARTS calibrates tactic diversity during tree expansion and introduces bias-resistant value functions. Achieves 49.6% pass@1 on miniF2F-test. Important for understanding how to make proof search more efficient -- a concern that applies to any rule-based reasoning system including Sigil's forward/backward chaining.
- **Difficulty:** Advanced
- **Link:** https://openreview.net/forum?id=VQwI055flA

### 3.13 Li, Z. et al. "A Survey on Deep Learning for Theorem Proving." COLM, 2024.
- **Summary:** The most comprehensive survey of AI theorem proving to date, covering autoformalization, premise selection, proofstep generation, proof search, datasets, and evaluation metrics. Provides a systematic taxonomy of approaches and identifies persistent challenges. The definitive reference for understanding the full landscape. Read this before diving into individual papers.
- **Difficulty:** Beginner (survey)
- **Link:** https://arxiv.org/abs/2404.09939

---

## 4. LLMs for Formal Reasoning

Papers on using large language models for structured reasoning, chain-of-thought, and tool use in formal domains.

### 4.1 Wei, J. et al. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." NeurIPS, 2022.
- **Summary:** The foundational paper showing that providing intermediate reasoning steps in prompts dramatically improves LLM performance on arithmetic, commonsense, and symbolic reasoning tasks. A 540B-parameter model with just 8 chain-of-thought exemplars achieved SOTA on GSM8K. The key insight -- that externalizing symbolic intermediate steps improves neural reasoning -- is the theoretical basis for Sigil's traces-as-output design philosophy. Every Sigil rule evaluation produces an explicit reasoning chain.
- **Difficulty:** Beginner
- **Link:** https://arxiv.org/abs/2201.11903

### 4.2 Lewkowycz, A. et al. "Solving Quantitative Reasoning Problems with Language Models." (Minerva) NeurIPS, 2022.
- **Summary:** Minerva is a PaLM-based model further trained on 118GB of scientific papers and mathematical content, achieving SOTA on STEM reasoning benchmarks without external tools. Combines chain-of-thought prompting with majority voting over multiple sampled solutions. Important because it showed the limits of pure neural reasoning: Minerva solves roughly a third of undergraduate-level STEM problems, demonstrating both capability and the ceiling that motivates symbolic verification.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2206.14858

### 4.3 Trinh, T.H. et al. "Solving olympiad geometry without human demonstrations." (AlphaGeometry) Nature, 625, 476--482, 2024.
- **Summary:** AlphaGeometry pairs a neural language model (trained on 100M synthetic examples) with a symbolic deduction engine (DD+AR) for Euclidean geometry. The neural model suggests auxiliary constructions when the symbolic engine gets stuck, and the symbolic engine verifies every step. Solved 25 of 30 Olympiad geometry problems (matching human gold medalists). The quintessential example of the neuro-symbolic pattern: neural for creative leaps, symbolic for rigorous verification. This is what Sigil's `neural` keyword aspires to enable.
- **Difficulty:** Intermediate
- **Link:** https://www.nature.com/articles/s41586-023-06747-5

### 4.4 Zheng, K., Han, J.M., and Polu, S. "MiniF2F: A Cross-System Benchmark for Formal Olympiad-level Mathematics." ICLR, 2022.
- **Summary:** Established the standard benchmark for AI theorem proving: 488 problem statements drawn from AMC, AIME, and IMO competitions, formalized in Metamath, Lean, Isabelle, and HOL Light. Nearly every theorem proving paper since 2022 reports results on miniF2F, making it the MNIST of formal mathematics. Understanding this benchmark is essential context for evaluating any AI theorem proving result.
- **Difficulty:** Beginner
- **Link:** https://arxiv.org/abs/2109.00110

---

## 5. Differentiable Reasoning

Papers on making logical reasoning differentiable so it can be integrated with gradient-based learning.

### 5.1 Manhaeve, R. et al. "DeepProbLog: Neural Probabilistic Logic Programming." NeurIPS, 2018.
- **Summary:** The pioneering framework that integrates deep learning with probabilistic logic programming by introducing "neural predicates" -- ProbLog predicates whose truth values are determined by neural networks. Supports symbolic reasoning, probabilistic inference, program induction, and deep learning in a single framework, trained end-to-end. DeepProbLog demonstrated that differentiable logic programming is practical. Sigil's `neural` keyword implements a similar concept at a higher level of abstraction.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/1805.10872

### 5.2 Badreddine, S., Garcez, A.d., Serafini, L., and Spranger, M. "Logic Tensor Networks." Artificial Intelligence, 303, 103649, 2022.
- **Summary:** LTN introduces Real Logic, a fully differentiable first-order logic where predicates, functions, and connectives are grounded as neural computational graphs with fuzzy logic semantics. Supports multi-label classification, relational learning, clustering, semi-supervised learning, and query answering in a unified framework. The idea of grounding logical symbols onto neural computations is foundational for understanding how Sigil's symbolic rules could interact with learned representations.
- **Difficulty:** Intermediate
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0004370221002009

### 5.3 Li, Z. et al. "Scallop: A Language for Neurosymbolic Programming." PLDI, 2023.
- **Summary:** Scallop is the closest existing system to what Sigil aspires to be: a purpose-built programming language for neurosymbolic applications. Built on Datalog with provenance semirings for automatic differentiation through logical reasoning. Supports relational data modeling, recursion, aggregation, and negation. Scales significantly better than DeepProbLog while maintaining accuracy. Sigil and Scallop make different design trade-offs: Scallop optimizes for end-to-end differentiability while Sigil optimizes for readability and auditability.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2304.04812

### 5.4 Rocktaschel, T. and Riedel, S. "End-to-End Differentiable Proving." NeurIPS, 2017.
- **Summary:** Introduces neural networks that perform differentiable backward chaining (Prolog-style), replacing symbolic unification with differentiable operations on vector representations. The architecture is recursively constructed following the backward chaining algorithm, combining symbolic proof structure with learned representations. Outperforms neural link prediction models while inducing interpretable first-order logic rules. Foundational for understanding how Sigil's backward chaining engine could be enhanced with learned components.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/1705.11040

### 5.5 Evans, R. and Grefenstette, E. "Learning Explanatory Rules from Noisy Data." JAIR, 61, 1--64, 2018.
- **Summary:** Proposes differentiable Inductive Logic Programming (dILP), which learns first-order logic rules from noisy data via backpropagation. Unlike traditional ILP, dILP is robust to noise and can be hybridized with neural networks for handling ambiguous perceptual data. The learned rules are fully interpretable. Demonstrates that the boundary between learned and hand-crafted rules can be blurred -- a direction Sigil could explore in future phases.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/1711.04574

---

## 6. Applied Neuro-Symbolic Systems

Papers and reports on real-world deployments of neuro-symbolic AI.

### 6.1 Amazon Web Services. "Automated Reasoning Checks in Amazon Bedrock Guardrails." AWS Blog, 2025.
- **Summary:** AWS integrated formal verification into its generative AI platform: Automated Reasoning checks use sound mathematical techniques to verify LLM outputs against expert-created policies with up to 99% accuracy. Deployed for financial regulatory compliance, healthcare protocol verification, and utility outage management. This is the most prominent production deployment of the "LLM generates, symbolic engine verifies" pattern -- exactly the architecture Sigil embodies. Demonstrates real commercial demand for this approach.
- **Difficulty:** Beginner
- **Link:** https://aws.amazon.com/blogs/aws/minimize-ai-hallucinations-and-deliver-up-to-99-verification-accuracy-with-automated-reasoning-checks-now-available/

### 6.2 Amazon Rufus and Vulcan: Neuro-Symbolic AI in Production. Various sources, 2024--2025.
- **Summary:** Amazon deployed neuro-symbolic AI in two major products: Rufus (shopping assistant handling 274M+ daily queries, combining a custom LLM with symbolic product logic and RAG) and Vulcan (warehouse robots combining neural vision/tactile sensing with symbolic safety constraints and optimization). These deployments demonstrate that neuro-symbolic architectures work at massive scale when the neural and symbolic components have clearly defined roles -- the same separation Sigil enforces by design.
- **Difficulty:** Beginner
- **Link:** https://www.fastcompany.com/91446331/amazon-byron-cook-ai-artificial-intelligence-automated-reasoning-neurosymbolic-hallucination-logic

### 6.3 AWS. "Use of Formal Methods at Amazon Web Services." Newcombe et al., 2014 (updated 2024).
- **Summary:** The landmark industry report on using TLA+ for formal verification of distributed systems at AWS. Engineers used TLA+ to find subtle bugs in DynamoDB, S3, and other core services. The report demonstrates both the value of formal methods in industry and the accessibility barrier: even at Amazon, adoption required significant training investment. Directly motivates the need for more accessible formal specification languages like FizzBee and potentially Sigil.
- **Difficulty:** Beginner
- **Link:** https://lamport.azurewebsites.net/tla/formal-methods-amazon.pdf

### 6.4 WEF Report. "The Power of Neurosymbolic AI: No Hallucinations, Auditable Workings, Real-World Outcomes." World Economic Forum, 2025.
- **Summary:** A high-level industry report documenting the shift toward neurosymbolic AI in regulated industries. Highlights applications in drug repurposing (combining deep learning with symbolic reasoning for explainable predictions), healthcare (auditable clinical decision support), and financial services. The emphasis on auditability and explainability aligns directly with Sigil's design philosophy of traces as fundamental output.
- **Difficulty:** Beginner
- **Link:** https://www.weforum.org/stories/2025/12/neurosymbolic-ai-real-world-outcomes/

---

## 7. Language Design for AI

Papers on designing programming languages and DSLs that are optimized for AI generation, analysis, and integration.

### 7.1 Zhang, H. et al. "MoonBit: Explore the Design of an AI-Friendly Programming Language." LLM4Code Workshop at ICSE, 2024.
- **Summary:** MoonBit is designed from the ground up for LLM code generation: mandatory type signatures at top level (constraining generation), structural interfaces (reducing boilerplate), flat syntax (minimizing nesting), and custom sampling algorithms that ensure syntactic and semantic correctness. Internal tests show "thousands of lines of code running perfectly the first time." MoonBit's design principles directly informed Sigil's syntax choices: flat structure, explicit types at boundaries, ~30 keywords, all designed for LLM-friendly generation.
- **Difficulty:** Beginner
- **Link:** https://dl.acm.org/doi/10.1145/3643795.3648376

### 7.2 Ellis, K. et al. "DreamCoder: Bootstrapping Inductive Program Synthesis with Wake-Sleep Library Learning." PLDI, 2021.
- **Summary:** DreamCoder learns domain-specific languages incrementally: it synthesizes programs to solve tasks, extracts reusable abstractions into a growing library via E-graph refactoring, and trains a neural search policy to guide future synthesis. The wake-sleep loop between program synthesis and library construction is a powerful paradigm for building DSLs. Relevant to Sigil because it shows how domain-specific abstractions (like Sigil's rule patterns) can be learned rather than hand-designed.
- **Difficulty:** Advanced
- **Link:** https://dl.acm.org/doi/10.1145/3453483.3454080

### 7.3 FizzBee: Formal Specification Made Accessible. fizzbee.io, 2024.
- **Summary:** FizzBee is a formal specification language with Python-like syntax designed to make TLA+-style model checking accessible to working engineers. Built with an ANTLR parser and Go interpreter, it uses breadth-first state exploration. A DoorDash engineer learned it over a weekend and used it to model a streaming ingestion platform. FizzBee demonstrates the same thesis as Sigil: formal methods can be made dramatically more accessible through thoughtful language design without sacrificing rigor.
- **Difficulty:** Beginner
- **Link:** https://fizzbee.io/

### 7.4 Moura, L. de and Ullrich, S. "The Lean 4 Theorem Prover and Programming Language." CADE, 2021.
- **Summary:** Lean 4 is both a theorem prover and a programming language, reimplemented in itself with a hygienic macro system, tabled typeclass resolution, and a novel "functional but in-place" paradigm. As the target language for AlphaProof and the platform for mathlib (210,000+ theorems), Lean 4 is the de facto standard for AI-assisted theorem proving. Understanding Lean 4's design -- particularly its extensible syntax and tactic framework -- is essential context for positioning Sigil in the formal reasoning ecosystem.
- **Difficulty:** Intermediate
- **Link:** https://link.springer.com/chapter/10.1007/978-3-030-79876-5_37

### 7.5 Yang, K. et al. "A Comprehensive Survey of the Lean 4 Theorem Prover: Architecture, Applications, and Advances." arXiv:2501.18639, 2025.
- **Summary:** Surveys Lean 4's architecture, its role in AI theorem proving, and the state of the mathlib ecosystem. Covers recent advances including integration with machine learning systems, the growth of formalized mathematics, and challenges in scaling. Provides essential context for understanding where Lean 4 excels and where there remain accessibility gaps that a language like Sigil could address.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2501.18639

---

## 8. Supplementary Papers

Additional important works that provide context across multiple categories.

### 8.1 Reed, S. and de Freitas, N. "Neural Programmer-Interpreters." ICLR (Best Paper), 2016.
- **Summary:** Showed that neural networks can learn to invoke programs rather than being the executor themselves -- a foundational insight for the entire neuro-symbolic field. The separation between neural perception and programmatic execution is the core principle behind Sigil's architecture.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/1511.06279

### 8.2 Azerbayev, Z. et al. "ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics." NeurIPS Math-AI Workshop, 2023.
- **Summary:** Extends autoformalization benchmarks beyond competition math to undergraduate-level problems, which are more representative of practical formal verification needs. Important for understanding the gap between olympiad-level results and real-world applicability.
- **Difficulty:** Intermediate
- **Link:** https://mathai2022.github.io/papers/20.pdf

### 8.3 ProofNet++: A Neuro-Symbolic System for Formal Proof Verification with Self-Correction. arXiv:2505.24230, 2025.
- **Summary:** Combines LLMs with formal proof verification and self-correction: symbolic proof tree supervision, an RL loop using verifiers as reward, and iterative self-correction. Achieves 12% improvement in proof success across miniF2F, mathlib, and HOL Light (120,000+ proofs). Represents the state of the art in neuro-symbolic proof verification.
- **Difficulty:** Advanced
- **Link:** https://arxiv.org/abs/2505.24230

### 8.4 SYSMOBENCH: Evaluating AI on Formally Modeling Complex Real-World Systems. arXiv:2509.23130, 2025.
- **Summary:** Benchmarks LLMs on generating TLA+ specifications for real-world systems. Finds that current models handle small artifacts well but struggle with large, complex systems. Directly relevant to understanding whether LLMs can generate formal specifications (including Sigil code) for real applications.
- **Difficulty:** Intermediate
- **Link:** https://arxiv.org/abs/2509.23130

---

## Reading Paths

### Path A: "I want to understand the neuro-symbolic landscape"
1.1 (Kautz taxonomy) -> 1.2 (Garcez 3rd wave) -> 1.3 (2024 systematic review) -> 3.13 (DL4TP survey) -> 6.4 (WEF real-world report)

### Path B: "I want to understand AI theorem proving"
4.4 (miniF2F benchmark) -> 3.1 (GPT-f) -> 3.3 (LeanDojo/ReProver) -> 3.2 (HTPS) -> 3.9 (AlphaProof) -> 3.7 (LEGO-Prover)

### Path C: "I want to understand autoformalization"
2.1 (Szegedy vision) -> 2.2 (Wu et al. LLM autoformalization) -> 3.6 (Draft-Sketch-Prove) -> 2.3 (Don't Trust: Verify) -> 2.4 (Process-Driven in Lean 4)

### Path D: "I want to build differentiable reasoning systems"
5.4 (Differentiable Proving) -> 5.1 (DeepProbLog) -> 5.2 (Logic Tensor Networks) -> 5.5 (dILP) -> 5.3 (Scallop)

### Path E: "I want to design AI-friendly languages"
7.1 (MoonBit) -> 7.3 (FizzBee) -> 7.4 (Lean 4) -> 7.2 (DreamCoder) -> 4.3 (AlphaGeometry -- language design for neural-symbolic)

### Path F: "I want to connect Sigil to this research"
1.2 (Garcez 3rd wave) -> 4.1 (Chain-of-thought) -> 2.3 (Don't Trust: Verify) -> 5.3 (Scallop) -> 7.1 (MoonBit) -> 6.1 (AWS Automated Reasoning) -> 4.3 (AlphaGeometry)

---

## Quick Reference: Papers by Difficulty

### Beginner (10 papers)
1.1, 1.2, 1.3, 1.4, 2.1, 3.13, 4.1, 4.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.3

### Intermediate (16 papers)
1.5, 1.6, 2.2, 2.3, 3.1, 3.3, 3.4, 3.5, 3.6, 4.2, 4.3, 5.1, 5.2, 7.4, 7.5, 8.1, 8.2, 8.4

### Advanced (14 papers)
2.4, 2.5, 3.2, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 5.3, 5.4, 5.5, 7.2, 8.3
