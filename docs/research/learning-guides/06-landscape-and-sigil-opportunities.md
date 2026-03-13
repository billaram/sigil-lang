# Research Landscape and Opportunities for Sigil

A synthesis of the current research landscape in neuro-symbolic AI, autoformalization, and AI theorem proving, with specific opportunities for the Sigil language project.

---

## 1. The Research Landscape: Who Is Doing What

### 1.1 Major Research Groups and Their Focus

**Google DeepMind (London/Mountain View)**
- **Focus:** AI theorem proving at scale, reinforcement learning for formal mathematics
- **Key outputs:** AlphaProof (Nature 2025), AlphaGeometry (Nature 2024), Minerva (NeurIPS 2022)
- **Approach:** Massive compute + RL + autoformalization. Train on millions of synthetic problems, use AlphaZero-style self-play
- **Relevance to Sigil:** DeepMind validates that the autoformalization pipeline works. Their systems translate natural language to formal Lean -- Sigil could serve as an intermediate representation that is more accessible than Lean

**Meta FAIR (Paris/New York)**
- **Focus:** Neural theorem proving, proof search algorithms
- **Key outputs:** HTPS (NeurIPS 2022), contributions to Lean/Metamath proving
- **Approach:** Language models + tree search, online training on discovered proofs
- **Relevance to Sigil:** FAIR's work on proof search algorithms (HTPS, MCTS variants) could inform how Sigil's forward/backward chaining engines explore rule spaces

**OpenAI (San Francisco)**
- **Focus:** Language models for formal mathematics, expert iteration
- **Key outputs:** GPT-f (2020), miniF2F benchmark, Formal Mathematics Statement Curriculum Learning (ICLR 2023)
- **Approach:** Scale language models, use expert iteration to bootstrap from unlabeled problems
- **Relevance to Sigil:** OpenAI's curriculum learning approach -- automatically discovering problems of appropriate difficulty -- could be applied to learning Sigil rule sets

**CMU + Caltech (LeanDojo Team)**
- **Focus:** Open-source infrastructure for AI theorem proving in Lean 4
- **Key outputs:** LeanDojo (NeurIPS 2023), ReProver, LeanAgent (ICLR 2025)
- **Approach:** Build open tooling, retrieval-augmented proving, lifelong learning
- **Relevance to Sigil:** LeanDojo's approach to extracting data from proof environments and building open tooling is a model for how Sigil could instrument its own execution for ML consumption

**University of Pennsylvania (Naik Lab)**
- **Focus:** Neurosymbolic programming languages
- **Key outputs:** Scallop (PLDI 2023), neurosymbolic programming pitfalls analysis
- **Approach:** Differentiable Datalog with provenance semirings, end-to-end trainable
- **Relevance to Sigil:** Scallop is the closest existing system to Sigil in philosophy. Key differences: Scallop optimizes for differentiability, Sigil for readability. Potential for complementary approaches

**University of Cambridge (Jamnik Group)**
- **Focus:** Autoformalization, proof sketching, neuro-symbolic reasoning
- **Key outputs:** Draft-Sketch-Prove (ICLR 2023), Thor (NeurIPS 2022), autoformalization papers with Szegedy/Wu
- **Approach:** Use LLMs as translators between informal and formal mathematics
- **Relevance to Sigil:** Cambridge's work on proof sketching is the closest intellectual ancestor to Sigil's constrained NL approach. Potential collaboration target

**KU Leuven (De Raedt Group)**
- **Focus:** Probabilistic logic programming, neural-symbolic integration
- **Key outputs:** DeepProbLog (NeurIPS 2018), ProbLog ecosystem
- **Approach:** Extend probabilistic logic programming with neural predicates
- **Relevance to Sigil:** DeepProbLog's "neural predicate" concept directly parallels Sigil's `neural` keyword. Lessons from their deployment experience are directly applicable

**Amazon Science / AWS**
- **Focus:** Production deployment of neuro-symbolic AI, automated reasoning for LLM guardrails
- **Key outputs:** Bedrock Guardrails with Automated Reasoning (2025), Rufus shopping assistant, Vulcan warehouse robots
- **Approach:** Formal verification as a guardrail layer on top of LLM outputs
- **Relevance to Sigil:** Amazon is the strongest validation of commercial demand for Sigil's architecture. Their "generate then verify" pattern maps directly to Sigil's workflow

**MoonBit Team (Hongbo Zhang)**
- **Focus:** AI-native programming language design
- **Key outputs:** MoonBit language, LLM4Code workshop paper (ICSE 2024)
- **Approach:** Language designed from ground up for LLM generation: flat syntax, mandatory type signatures, structural interfaces
- **Relevance to Sigil:** MoonBit's design principles directly validate Sigil's syntax choices. Both languages share the thesis that AI-friendly language design is fundamentally different from human-only language design

### 1.2 Where the Field Is Moving

**Trend 1: From Benchmarks to Real Proofs**
The field is moving beyond miniF2F toward proving real theorems in mathlib (LeanAgent proved 155 previously unproven theorems). This means the bar for "useful AI reasoning" is rising rapidly.

**Trend 2: Autoformalization as Infrastructure**
Autoformalization is shifting from a research curiosity to infrastructure. AlphaProof's 80M autoformalized Lean statements show this is now done at industrial scale. The question is no longer "can we autoformalize?" but "what should we autoformalize into?"

**Trend 3: Neurosymbolic Goes to Production**
Amazon's Bedrock Guardrails (99% verification accuracy), Rufus (274M daily queries), and Vulcan robots demonstrate that neuro-symbolic architectures work in production. The 2025 WEF report signals growing industry adoption.

**Trend 4: Language Design for AI Becomes a Field**
MoonBit's ICSE paper, the LLM4Code workshop series, and SYSMOBENCH (evaluating LLMs on TLA+ generation) show that designing languages for AI consumption is becoming a research area in its own right.

**Trend 5: Verification as the Value Proposition**
"Don't Trust: Verify" (ICLR 2024) and AWS Automated Reasoning demonstrate that the killer application of formal methods in the LLM era is verification, not generation. Formal systems add value by checking what LLMs generate.

---

## 2. Specific Opportunities for Sigil

### 2.1 Sigil as a Target Language for Autoformalization

**The Opportunity:**
Current autoformalization targets (Lean, Isabelle, HOL Light) are designed for mathematicians and formal methods experts. They have steep learning curves and require understanding of type theory, tactic languages, and proof automation. There is a massive accessibility gap between "domain expert who can describe a rule in English" and "formal methods expert who can write Lean."

Sigil occupies a unique middle ground: it has formal semantics (PEG grammar, deterministic execution, type system) but surface syntax that reads like constrained English. This makes it a potentially ideal target for autoformalization of *domain rules* rather than mathematical theorems.

**What This Would Look Like:**
```
-- Natural language input from domain expert:
"If a patient's blood pressure exceeds 140 systolic or 90 diastolic,
 and they have diabetes, classify as high-risk."

-- Autoformalized into Sigil:
rule hypertension_risk with priority 10:
  when patient systolic_bp exceeds 140
  or patient diastolic_bp exceeds 90
  and patient has_diabetes is true
  then patient risk_level becomes :high
  explain "Blood pressure exceeds threshold with diabetes comorbidity"
```

**Why Sigil Is Better Suited Than Lean for This:**
- Domain experts can *read and validate* the autoformalized output
- The constrained NL syntax is closer to the input, reducing translation distance
- Sigil's `explain` keyword provides built-in justification (traces)
- No type theory prerequisites for the domain expert to understand the output
- The `neural` keyword handles cases where rules need ML assistance

**Research Contribution:**
A paper titled "Accessible Autoformalization: Translating Domain Rules into Executable Neuro-Symbolic Programs" could introduce Sigil as an autoformalization target, with a benchmark of domain rule translation tasks (medical protocols, financial regulations, safety requirements).

### 2.2 Sigil's Rule Engine for Formal Verification of AI Systems

**The Opportunity:**
AWS Bedrock Guardrails demonstrates that there is enormous demand for verifying AI outputs against formal rules. Currently, these rules are written in proprietary formats or general-purpose languages. Sigil could serve as an open, standardized language for writing AI verification rules.

**What This Would Look Like:**
```sigil
-- Content moderation guardrail
module content_safety:
  export check_response

  rule no_medical_advice with priority 100:
    when response contains_medical_claim is true
    and response has_disclaimer is false
    then response status becomes :blocked
    explain "Medical claims require explicit disclaimers"

  rule no_financial_guarantees with priority 100:
    when response promises_returns is true
    then response status becomes :blocked
    explain "Financial return guarantees violate regulatory requirements"

  neural classify_intent from response_text: Text:
    model "intent-classifier-v2"
    returns Symbol
    confidence_threshold 0.90
    fallback to :unknown
```

**Why Sigil Is Well-Positioned:**
- Traces provide complete audit trails (regulatory requirement)
- Deterministic execution guarantees reproducibility
- The `neural` keyword allows hybrid rules (e.g., neural classification + symbolic policy)
- Forward chaining evaluates all applicable rules (completeness)
- Backward chaining answers specific compliance queries (targeted verification)
- Constrained NL makes rules readable by compliance officers, not just engineers

**Research Contribution:**
A paper titled "Auditable AI Guardrails: A Neuro-Symbolic Language for Verifying LLM Outputs" could position Sigil as an open alternative to proprietary guardrail frameworks, with benchmarks on content moderation, regulatory compliance, and safety-critical domains.

### 2.3 Bridging Domain Experts and Formal Methods

**The Opportunity:**
Formal methods have proven their value at Amazon, Microsoft, and Intel, but adoption remains limited by the accessibility gap. TLA+ requires mathematical maturity; Lean requires type theory; Alloy requires relational logic. FizzBee has shown that a Python-like syntax lowers the barrier dramatically (learned in a weekend). Sigil could go further by offering a constrained natural language interface to formal rule specification.

**What This Would Look Like:**
A domain expert writes rules in Sigil's constrained NL. These rules are:
1. Parsed into a formal AST (verified well-formed)
2. Type-checked (verified internally consistent)
3. Executed against test cases (verified against examples)
4. Traced to produce audit logs (verified observable)
5. Optionally translated to TLA+, Lean, or SMT-LIB for deeper verification

**The Key Insight:**
Sigil's PEG grammar ensures that the "natural language" is actually a formal specification. The domain expert thinks they are writing rules in English; the system knows it is processing a formal language. This is the same insight behind Inform 7 (interactive fiction in natural language that compiles to Z-machine code), applied to business rules and AI verification.

**Research Contribution:**
A user study comparing rule authoring in Sigil vs. TLA+ vs. Python across domain expert populations (nurses writing clinical decision support rules, compliance officers writing regulatory checks, operations managers writing safety protocols).

### 2.4 What a "Sigil for Theorem Proving" Would Look Like

**The Opportunity:**
Current theorem provers (Lean, Coq, Isabelle) are designed for mathematical precision but are inaccessible to most developers. A "theorem prover for the rest of us" that uses Sigil's constrained NL approach could make formal verification mainstream.

**What This Would Look Like:**
```sigil
-- Specification of a simple sorting invariant
type SortedList is record:
  elements: List

define is_sorted as compute from lst: List returns Bool:
  for each pair in adjacent_pairs of lst:
    when pair first exceeds pair second
    then return false
  return true

-- Property to verify
rule sorting_preserves_length:
  given input_list from input
  given sorted_list as sort(input_list)
  when length of sorted_list is not length of input_list
  then report :length_violation
  explain "Sort must preserve list length"

rule sorting_produces_order:
  given input_list from input
  given sorted_list as sort(input_list)
  when is_sorted(sorted_list) is false
  then report :order_violation
  explain "Sort output must be ordered"
```

**Key Design Decisions:**
- Rules as properties: Sigil rules become proof obligations
- `explain` as proof witness: the trace serves as the proof
- Forward chaining as bounded model checking: enumerate states, check properties
- Backward chaining as goal-directed verification: given a property, find violations
- `neural` for heuristic guidance: use ML to suggest interesting test cases

**This is NOT a replacement for Lean.** It is a complement: Sigil handles the specification layer (what should be true) while Lean/SMT solvers handle the proof layer (why it is true). The Sigil-to-Lean translation becomes an autoformalization problem.

### 2.5 Applying Sigil's Neural Keyword Pattern to Formal Math

**The Opportunity:**
AlphaGeometry showed the power of the pattern: symbolic engine does rigorous deduction, neural model suggests creative auxiliary constructions when stuck. This is exactly what Sigil's `neural` keyword enables. The pattern could be generalized to other formal domains.

**What This Would Look Like:**
```sigil
-- Neural-guided constraint solving
rule check_system_property:
  given system_state from input

  -- Symbolic: check known invariants
  when system_state violates invariant_a
  then status becomes :unsafe
  explain "Invariant A violated"

  -- When symbolic analysis is insufficient:
  neural suggest_counterexample from system_state: Record:
    model "counterexample-generator-v1"
    returns Record
    confidence_threshold 0.80
    fallback to empty

  -- Symbolic: verify the neural suggestion
  when suggested counterexample is not empty
  and verify(system_state, counterexample) is true
  then status becomes :unsafe
  explain "Neural-guided counterexample found and verified"
```

**The Pattern:** Neural for creative search (suggesting auxiliary lemmas, counterexamples, proof strategies), symbolic for verification (checking that suggestions are valid). The `neural` keyword with mandatory fallback ensures the system degrades gracefully when the model is uncertain.

---

## 3. Concrete Project Ideas

### Project 1: SigilGuard -- AI Output Verification Framework
**Effort:** 3-6 months, 1-2 developers
**Description:** Build a framework where Sigil programs serve as executable guardrail policies for LLM outputs. An LLM generates a response, the response is parsed into a Sigil `Record`, and a set of Sigil rules evaluate the response for compliance, safety, and accuracy.

**Technical components:**
- JSON/structured input adapter for LLM outputs
- Standard library of guardrail primitives (contains_pii, matches_pattern, sentiment_score)
- Neural predicates for content classification (via Sigil's `neural` keyword)
- REST API wrapper for integration with LLM pipelines
- Trace output in structured JSON for audit logging

**Target venue:** ACL or EMNLP (NLP safety track), or NeurIPS (safety workshop)
**Differentiator vs. AWS Bedrock:** Open source, auditable language semantics, hybrid neural-symbolic rules, portable across LLM providers

### Project 2: SigilFormalize -- Domain Rule Autoformalization Benchmark
**Effort:** 6-9 months, 2-3 researchers
**Description:** Create a benchmark for translating domain expert rules from natural language into executable Sigil programs, and evaluate LLMs on this task. The benchmark would cover:
- Medical clinical decision support rules (e.g., sepsis screening protocols)
- Financial regulatory compliance rules (e.g., KYC/AML checks)
- Industrial safety rules (e.g., equipment operating limits)
- Content moderation policies (e.g., platform community guidelines)

**Technical components:**
- Curated dataset of 500+ natural language rules paired with Sigil formalizations
- Evaluation harness that compiles Sigil output, runs test cases, checks trace correctness
- Baseline results for GPT-4, Claude, Gemini, and open-source models
- Analysis of error categories (syntax errors, semantic mismatches, missing rules)
- Process-supervised evaluation using Sigil compiler feedback (inspired by PSV from Lu et al.)

**Target venue:** ICLR or NeurIPS (datasets and benchmarks track)
**Differentiator:** First autoformalization benchmark targeting domain rules (not math), first benchmark for constrained NL formal languages

### Project 3: SigilProve -- Lightweight Property Verification
**Effort:** 9-12 months, 2-3 developers
**Description:** Extend Sigil's rule engine to support bounded property verification: given a set of rules and constraints, systematically enumerate states up to a bound and check that all properties hold. This is bounded model checking in Sigil's constrained NL.

**Technical components:**
- State space enumeration engine (extend forward chaining to systematic exploration)
- Property specification syntax (`verify that ... for all ...`)
- Counterexample generation and reporting via traces
- Integration with Z3 SMT solver via Python FFI for constraint solving
- Optional neural-guided search for interesting states (via `neural` keyword)
- Translation from Sigil properties to TLA+ or SMT-LIB for deeper verification

**Target venue:** CAV (tools track) or FM (formal methods conference)
**Differentiator:** First formal verification tool with constrained natural language syntax and built-in neuro-symbolic capabilities

### Project 4: SigilTeach -- Interactive Formal Reasoning Tutor
**Effort:** 6-9 months, 2-3 developers
**Description:** An educational tool that teaches formal reasoning through Sigil. Students write rules in constrained NL, the system traces execution step-by-step, and an LLM provides explanations and hints when students get stuck. Targets introductory logic, discrete math, and programming courses.

**Technical components:**
- Web-based Sigil REPL (compile to WASM via Rust core)
- Step-by-step trace visualization
- LLM-powered hint system (using Sigil's `neural` keyword)
- Progressive curriculum from simple rules to complex reasoning chains
- Assessment via automatically generated test cases

**Target venue:** SIGCSE or L@S (education conferences), or NeurIPS (education workshop)
**Differentiator:** Bridges the gap between natural language reasoning and formal methods, making formal reasoning accessible to non-CS students

### Project 5: SigilBridge -- Interoperability Layer Between Formal Systems
**Effort:** 12-18 months, 3-4 researchers
**Description:** Position Sigil as a lingua franca between different formal reasoning systems. Sigil's constrained NL serves as the human-readable specification layer, with backends that compile to Lean 4 (for theorem proving), TLA+ (for model checking), SMT-LIB (for constraint solving), and Datalog (for database queries).

**Technical components:**
- Sigil-to-Lean 4 translator (autoformalization of Sigil rules into Lean propositions)
- Sigil-to-TLA+ translator (Sigil rules as TLA+ temporal properties)
- Sigil-to-SMT-LIB translator (Sigil constraints as SMT assertions)
- Round-trip: formal proof results translated back to Sigil traces
- Neural-assisted translation using LLMs fine-tuned on paired Sigil/Lean data

**Target venue:** POPL or OOPSLA (programming languages), or ITP (theorem proving)
**Differentiator:** First system that uses constrained NL as a universal specification language with multiple formal backends

---

## 4. Potential Collaborators and Communities

### 4.1 Academic Groups to Engage

| Group | Institution | Contact Point | Why |
|-------|------------|---------------|-----|
| Jamnik Lab | Cambridge | Mateja Jamnik | Autoformalization, proof sketching; closest to Sigil's NL-to-formal vision |
| Naik Lab | UPenn | Mayur Naik | Scallop creators; shared interest in NeSy programming languages |
| LeanDojo Team | CMU/Caltech | Kaiyu Yang | Open-source AI theorem proving tooling; potential for Sigil-Lean bridge |
| De Raedt Group | KU Leuven | Luc De Raedt | DeepProbLog creators; neural predicate expertise |
| Garcez Group | City, University of London | Artur d'Avila Garcez | LTN creators, NeSy taxonomy leaders |
| Solar-Lezama Lab | MIT | Armando Solar-Lezama | Program synthesis, DreamCoder; DSL learning |
| MoonBit Team | Independent | Hongbo Zhang | AI-native language design; shared design philosophy |

### 4.2 Industry Contacts

| Organization | Relevance | Engagement Path |
|-------------|-----------|-----------------|
| AWS Automated Reasoning | Production NeSy guardrails | Open-source SigilGuard as alternative/complement to Bedrock |
| Google DeepMind | AlphaProof, autoformalization at scale | Sigil as accessible autoformalization target |
| Anthropic | AI safety, Constitutional AI | Sigil for auditable AI decision policies |
| IBM Research | Neuro-symbolic AI research program | Enterprise rule management in Sigil |
| Toyota Research Institute | Verified autonomous systems | Safety rules in constrained NL |

### 4.3 Communities and Forums

- **NeSy Conference Series** (https://nesyconf.org/) -- The premier annual conference for neurosymbolic AI. NeSy 2025 in Santa Cruz, CA (Sep 8-10). NeSy 2026 in Lisbon, Portugal.
- **Lean Community** (https://leanprover-community.github.io/) -- Extremely active Zulip chat for Lean 4 and mathlib development. Good venue for discussing Sigil-Lean bridges.
- **AITP Conference** (https://aitp-conference.org/) -- Annual workshop on AI and theorem proving. AITP 2025 in Aussois, France (Aug 31 - Sep 5). Intimate, workshop-style.
- **EuroProofNet** (https://europroofnet.github.io/) -- EU COST Action network connecting proof technology researchers across Europe.
- **Machine Learning for Theorem Proving** (Lean Zulip stream) -- Active discussion of ML approaches to formal verification.
- **Neurosymbolic Programming** (emerging community around Scallop, DeepProbLog) -- Centered at UPenn and KU Leuven.

---

## 5. Conferences and Venues

### 5.1 Primary Targets (Highest Relevance to Sigil)

| Conference | Focus | Deadline (typical) | Sigil Angle |
|-----------|-------|-------------------|-------------|
| **NeurIPS** | ML + AI | May | Neuro-symbolic AI, AI theorem proving, benchmarks |
| **ICLR** | Representations + learning | Sep-Oct | Autoformalization, formal reasoning with LLMs |
| **ICML** | Machine learning | Jan | Differentiable reasoning, neural-symbolic integration |
| **AAAI** | Broad AI | Aug | NeSy systems, knowledge representation, AI safety |
| **PLDI** | Programming language design | Nov | Sigil as a language (following Scallop's path) |
| **OOPSLA** | Object-oriented + PL | Apr | Language design, type systems, DSLs |

### 5.2 Specialized Venues (High Relevance, Smaller Communities)

| Conference | Focus | Deadline (typical) | Sigil Angle |
|-----------|-------|-------------------|-------------|
| **NeSy** | Neurosymbolic AI | May-Jun | Core venue for Sigil's NeSy contributions |
| **AITP** | AI + theorem proving | Apr-May | Sigil-to-Lean bridge, accessible formalization |
| **ITP** | Interactive theorem proving | Feb-Mar | SigilProve, Sigil as specification layer |
| **CPP** | Certified programs + proofs | Sep | Formal properties of Sigil's type system |
| **CAV** | Computer-aided verification | Jan | SigilProve tool paper, bounded model checking |
| **COLM** | Language modeling | Feb | LLMs for Sigil code generation |

### 5.3 Workshop Targets (Lower Bar, Good for Early Results)

| Workshop | Co-located With | Sigil Angle |
|----------|----------------|-------------|
| LLM4Code | ICSE | Sigil as AI-friendly language (following MoonBit) |
| Math-AI | NeurIPS | Autoformalization into Sigil |
| NeSy (workshops) | IJCAI/AAAI | Neurosymbolic language design |
| FoRLM (Formal Reasoning with LMs) | NeurIPS 2025 | Sigil for structured formal reasoning |
| Efficient Reasoning | NeurIPS 2025 | Sigil's symbolic engine for reasoning efficiency |
| SafeGenAI | Various | SigilGuard for AI safety |

### 5.4 Recommended Publication Strategy

**Phase 1 (0-6 months): Establish Presence**
- Workshop paper at LLM4Code or NeSy workshop: "Sigil: A Constrained Natural Language for Neuro-Symbolic Programming"
- Blog post / technical report comparing Sigil to Scallop, DeepProbLog, and FizzBee

**Phase 2 (6-12 months): First Research Contribution**
- Conference paper at NeSy 2026 (Lisbon) or AAAI: SigilGuard or SigilFormalize
- Tool demo at PLDI or OOPSLA: Sigil language and toolchain

**Phase 3 (12-24 months): Major Venue**
- Full paper at NeurIPS/ICLR: SigilFormalize benchmark with comprehensive LLM evaluation
- Tool paper at CAV or ITP: SigilProve bounded verification

---

## 6. Strategic Positioning Summary

### What Sigil Is (and Is Not)

Sigil is NOT:
- A replacement for Lean/Coq/Isabelle (no dependent types, no proof tactics)
- A replacement for Scallop (no differentiable reasoning, not end-to-end trainable)
- A replacement for TLA+/Alloy (no model checking, no temporal logic)

Sigil IS:
- **The specification layer** between domain experts and formal systems
- **The verification layer** between LLM outputs and trusted decisions
- **The readable layer** that makes neuro-symbolic AI auditable
- **The generation target** that LLMs can reliably produce (constrained NL + PEG grammar)

### The Unique Value Proposition

No existing system combines all of:
1. Constrained natural language syntax (readable by domain experts)
2. Formal PEG grammar (parseable by machines, generable by LLMs)
3. Deterministic symbolic execution (auditable, reproducible)
4. Explicit neural/symbolic boundary (the `neural` keyword)
5. Execution traces as first-class output (built-in explainability)
6. Forward AND backward chaining (complete and targeted reasoning)
7. Python FFI + Rust core (ecosystem access + performance)

This combination positions Sigil uniquely at the intersection of three growing trends:
- **Autoformalization** (LLMs translating natural language to formal specifications)
- **AI verification** (formal methods checking LLM outputs)
- **Accessible formal methods** (making formal reasoning available to non-experts)

The research opportunity is to demonstrate that this combination is not just theoretically appealing but practically effective -- and the five project ideas above provide concrete paths to doing so.
