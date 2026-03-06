# The Neuro-Symbolic Bridge: How Sigil Connects Neural Perception to Symbolic Reasoning

## A Real-World Research Document with Data Flow Diagrams, Domain Studies, and Pipeline Comparisons

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Fundamental Problem: Two Worlds, No Common Language](#2-the-fundamental-problem)
3. [How Real-World Neuro-Symbolic Pipelines Work Today](#3-how-real-world-pipelines-work-today)
4. [The Gap: What Breaks Without a Formal Bridge](#4-the-gap)
5. [How Sigil Bridges the Gap](#5-how-sigil-bridges-the-gap)
6. [Domain Studies](#6-domain-studies)
   - 6.1 [Finance & Compliance (AML/KYC)](#61-finance--compliance)
   - 6.2 [Healthcare & Clinical Decision Support](#62-healthcare--clinical-decision-support)
   - 6.3 [Physical AI & Robotics](#63-physical-ai--robotics)
   - 6.4 [Computer Vision & Scene Understanding](#64-computer-vision--scene-understanding)
   - 6.5 [Autonomous Vehicles](#65-autonomous-vehicles)
   - 6.6 [Legal & Contract Analysis](#66-legal--contract-analysis)
   - 6.7 [Manufacturing & Quality Control](#67-manufacturing--quality-control)
7. [Data Flow Diagrams: With vs Without Sigil](#7-data-flow-diagrams)
8. [Comparative Analysis: Sigil vs Existing Approaches](#8-comparative-analysis)
9. [The Evidence: Why the Bridge Matters](#9-the-evidence)
10. [Sources & References](#10-sources--references)

---

## 1. Executive Summary

Every serious AI system in 2025-2026 faces the same architectural problem: **neural networks perceive the world (text, images, sensor data), but cannot reason deterministically about what they perceive**. Symbolic engines (rule systems, constraint solvers, formal provers) can reason deterministically, but cannot understand raw, unstructured data. The bridge between these two worlds is currently built with ad-hoc glue code — JSON configs, Python scripts, REST APIs, YAML files — with no shared representation, no standard interface, and no auditable trace.

**Sigil is that bridge.** It is a programming language designed at the exact boundary where neural perception meets symbolic reasoning. The `neural` keyword marks where non-determinism enters. Everything else executes deterministically with full execution traces.

This document provides evidence from seven real-world domains that the gap is real, costly, and growing — and shows how Sigil's architecture directly addresses it.

### Key Findings

| Finding | Evidence |
|---------|----------|
| The neural-symbolic gap costs billions annually in glue code | JPMorgan: $2B AI investment; 60% of effort is integration engineering |
| No standard interface exists between neural and symbolic | 167-paper systematic review (arXiv:2501.05435) confirms fragmentation |
| Auditability is becoming legally mandated | EU AI Act, FinCEN AML rules, HIPAA all require decision traces |
| Every domain reinvents the same bridge pattern | Finance, healthcare, robotics, legal all use neural→structured→rules→trace |
| Existing NeSy languages target researchers, not domain experts | Scallop (Datalog), DeepProbLog (Prolog), LTN (tensor logic) — all require ML expertise |
| The "confidence-to-predicate" interface is the core technical challenge | Sigil's `neural` keyword with `confidence_threshold` and `fallback` solves this directly |

---

## 2. The Fundamental Problem: Two Worlds, No Common Language

### The Neural World

Large Language Models, computer vision systems, and neural networks excel at:
- Understanding natural language and extracting structured information from unstructured text
- Recognizing patterns in images, audio, and sensor data
- Generalizing from examples and handling ambiguity
- Generating fluent, contextually appropriate text

But they **cannot**:
- Produce deterministic outputs (same input → same output)
- Guarantee logical consistency across decisions
- Provide verifiable, auditable reasoning traces
- Follow precise rule sets without statistical drift

### The Symbolic World

Rule engines, constraint solvers, theorem provers, and formal systems excel at:
- Deterministic execution with provable guarantees
- Auditable decision traces showing exactly why a conclusion was reached
- Enforcing complex regulatory constraints consistently
- Composing rules into verifiable decision systems

But they **cannot**:
- Understand natural language or unstructured data
- Handle ambiguity, noise, or incomplete information
- Learn from examples or adapt to new patterns
- Process raw sensor data (images, audio, text)

### The Current State: Ad-Hoc Bridges

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HOW IT WORKS TODAY (The Mess)                           │
│                                                                             │
│  ┌──────────┐    JSON     ┌──────────┐   Python    ┌──────────┐            │
│  │  Neural   │───────────▶│  Custom   │───scripts──▶│  Rules   │            │
│  │  Model    │   /YAML    │  Glue     │   /REST    │  Engine   │            │
│  │ (LLM/CV)  │   /CSV     │  Code     │   APIs     │ (Drools/  │            │
│  └──────────┘            └──────────┘             │  OPA/etc) │            │
│       │                       │                     └──────────┘            │
│       │                       │                          │                  │
│       ▼                       ▼                          ▼                  │
│  No standard          No type safety            No integrated              │
│  output format        No error handling          audit trail               │
│  No confidence        No trace propagation       No confidence             │
│  semantics            Brittle transforms         awareness                  │
│                                                                             │
│  Result: Every team builds this from scratch. Every integration breaks     │
│  differently. No two systems produce compatible traces.                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The cost**: A 2025 McKinsey analysis found that 60-70% of AI project effort in regulated industries goes to integration engineering, compliance documentation, and audit trail construction — not the AI models themselves.

---

## 3. How Real-World Neuro-Symbolic Pipelines Work Today

### 3.1 The Canonical Pipeline

Every neuro-symbolic system, across all domains, follows the same three-layer pattern:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   THE UNIVERSAL NEURO-SYMBOLIC PIPELINE                     │
│                                                                             │
│  LAYER 1: NEURAL PERCEPTION                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Raw Data (text, images, sensor feeds, documents, transactions)     │    │
│  │       │                                                             │    │
│  │       ▼                                                             │    │
│  │  Neural Model (LLM, CNN, Transformer, GNN)                         │    │
│  │       │                                                             │    │
│  │       ▼                                                             │    │
│  │  Structured Output + Confidence Scores                              │    │
│  │  (entities, classifications, embeddings, features)                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                              │
│                    ══════════╪══════════  THE GAP  ══════════════════       │
│                              │                                              │
│  LAYER 2: SYMBOL GROUNDING (Where Things Break)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Neural outputs → Discrete symbolic predicates                      │    │
│  │  Confidence scores → Boolean/probabilistic facts                    │    │
│  │  Continuous embeddings → Categorical assignments                    │    │
│  │                                                                     │    │
│  │  ⚠️  THIS IS CUSTOM-BUILT FOR EVERY APPLICATION                    │    │
│  │  ⚠️  NO STANDARD FORMAT, NO STANDARD SEMANTICS                     │    │
│  │  ⚠️  NO CONFIDENCE PROPAGATION, NO FALLBACK POLICIES               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                              │
│  LAYER 3: SYMBOLIC REASONING                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Symbolic predicates + Knowledge base (rules, ontologies)           │    │
│  │       │                                                             │    │
│  │       ▼                                                             │    │
│  │  Inference Engine (forward/backward chaining, ILP, ASP)             │    │
│  │       │                                                             │    │
│  │       ▼                                                             │    │
│  │  Decision + Explanation Trace                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Existing Framework Approaches to the Bridge

| Framework | Bridge Mechanism | Target User | Limitation |
|-----------|-----------------|-------------|------------|
| **Scallop** | Provenance semirings over Datalog tuples | ML researchers | Requires Datalog expertise; not human-readable |
| **DeepProbLog** | Neural predicates as probabilistic facts in ProbLog | Logic programmers | Prolog syntax; steep learning curve |
| **NeurASP** | Neural outputs as probability distributions over ASP atoms | ASP experts | Answer Set Programming is niche |
| **LTN** | Real Logic grounding onto neural computational graphs | Researchers | Tensor-level reasoning; no natural language |
| **DomiKnowS** | Graph-based constraint specification | ML engineers | Python library, not a language; complex API |
| **JSON/YAML configs** | Manual mapping of model outputs to rule inputs | Everyone (by default) | No type safety, no traces, brittle, no standard |

**Key insight**: Every existing framework solves the bridge for a *research* audience. None provides a bridge that domain experts (compliance officers, clinicians, operations managers) can read, write, or audit.

---

## 4. The Gap: What Breaks Without a Formal Bridge

### 4.1 The Five Failure Modes

Research from 2024-2025 (arXiv:2411.04383, ICML 2025 NeSy workshop) documents five systematic failure modes:

#### Failure 1: Hallucination Propagation
```
Neural Model outputs: "Patient has cardiac_arrest symptoms" (confidence: 0.61)
                              │
                   No confidence check ──── BRIDGE GAP
                              │
                              ▼
Rules Engine receives: cardiac_arrest = TRUE
Rules Engine fires: ESI Level 1 (Resuscitation)

Result: False alarm. Patient had anxiety symptoms misclassified.
        No trace of the low confidence. No way to audit.
```

**Without Sigil**: The 0.61 confidence score is lost in the JSON transform. The rules engine treats it as certain truth.

**With Sigil**: `confidence_threshold 0.75` blocks this. `fallback to empty list` triggers. The trace records: "Neural confidence 0.61 below threshold 0.75; fallback applied."

#### Failure 2: Stochastic Reasoning Traces
The same unstructured input processed by the same LLM at different times produces different intermediate representations — different entity extractions, different classifications. Without a formal interface that enforces consistency, the symbolic layer receives different inputs for identical source data.

#### Failure 3: Reasoning Shortcuts (arXiv:2510.14538)
NeSy models learn to exploit spurious correlations rather than intended symbolic meanings. They achieve good task performance with wrong internal representations — the symbol grounding is incorrect even though the output appears correct. This is undetectable without formal trace auditing.

#### Failure 4: Representational Drift
Neural model updates (fine-tuning, retraining) change the mapping from inputs to symbolic predicates. Without a typed interface contract, the symbolic layer doesn't know its inputs have semantically shifted.

#### Failure 5: Audit Trail Fragmentation
When neural perception and symbolic reasoning use different logging systems, formats, and timestamps, reconstructing a complete decision trace for regulatory audit requires manual correlation across systems — expensive, error-prone, and often legally insufficient.

### 4.2 The Cost of the Gap

| Domain | Annual Cost of Gap | Source |
|--------|-------------------|--------|
| Financial compliance | $180B globally in fines + compliance costs (2023) | GFMI Report |
| Healthcare misdiagnosis | $750B annually (US) | Johns Hopkins / BMJ Quality & Safety |
| Manufacturing defects | $2T globally in quality failures | ASQ Cost of Quality |
| Legal contract review | 60-80% of lawyer time on document review | McKinsey Legal Report |
| Autonomous vehicle recalls | $8B in 2024 ADAS-related recalls | NHTSA database |

Not all of this is attributable to the neural-symbolic gap. But in each domain, the inability to formally bridge perception and reasoning is a significant contributor to errors, compliance failures, and integration costs.

---

## 5. How Sigil Bridges the Gap

### 5.1 Sigil's Architecture at the Bridge Point

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SIGIL: THE FORMAL BRIDGE                                 │
│                                                                             │
│  ┌───────────────────────────────┐                                         │
│  │     UNSTRUCTURED WORLD        │                                         │
│  │  (text, images, sensor data)  │                                         │
│  └──────────────┬────────────────┘                                         │
│                 │                                                            │
│                 ▼                                                            │
│  ┌───────────────────────────────┐                                         │
│  │   NEURAL KEYWORD BOUNDARY     │  ◄── Sigil's key innovation            │
│  │                               │                                         │
│  │  neural parse_transaction     │  • Declares the neural call explicitly  │
│  │    from narrative: Text:      │  • Specifies expected return type       │
│  │    model "fin-ner-v2"         │  • Sets confidence threshold            │
│  │    returns Transaction        │  • Defines fallback behavior            │
│  │    confidence_threshold 0.85  │  • Creates auditable boundary           │
│  │    fallback to manual_review  │                                         │
│  └──────────────┬────────────────┘                                         │
│                 │                                                            │
│                 │  Typed, confidence-checked, traceable output              │
│                 │                                                            │
│                 ▼                                                            │
│  ┌───────────────────────────────┐                                         │
│  │   SIGIL TYPE SYSTEM           │  ◄── Contracts at boundaries            │
│  │                               │                                         │
│  │  type Transaction is record:  │  • Gradual typing (optional internal,   │
│  │    id: Text                   │    required at boundaries)              │
│  │    amount: Number             │  • Sum types for decisions              │
│  │    currency: Symbol           │  • Record types for structured data     │
│  │    sender_pep_status: Boolean │  • Unit types (100 degrees)             │
│  └──────────────┬────────────────┘                                         │
│                 │                                                            │
│                 │  Fully typed, validated symbolic data                     │
│                 │                                                            │
│                 ▼                                                            │
│  ┌───────────────────────────────┐                                         │
│  │   SIGIL RULE ENGINE           │  ◄── Deterministic, priority-ordered    │
│  │                               │                                         │
│  │  rule sanctions_block:        │  • Forward chaining to fixed point      │
│  │    priority 100               │  • Priority-based rule ordering         │
│  │    when ... then ...          │  • Constrained NL syntax                │
│  │    explain "..."              │  • Explain clauses for humans           │
│  │    trace:                     │  • Trace metadata for compliance        │
│  │      compliance [:ofac]       │                                         │
│  └──────────────┬────────────────┘                                         │
│                 │                                                            │
│                 ▼                                                            │
│  ┌───────────────────────────────┐                                         │
│  │   DECISION + TRACE            │  ◄── Fundamental output                 │
│  │                               │                                         │
│  │  Decision: block              │  • Every rule evaluation traced         │
│  │  Reason: "OFAC sanctions"     │  • Neural confidence recorded           │
│  │  Trace:                       │  • Regulatory tags preserved            │
│  │    neural_confidence: 0.92    │  • Retention policies enforced          │
│  │    rules_fired: [sanctions]   │  • Full audit trail, single format     │
│  │    compliance: [:ofac, :bsa]  │                                         │
│  │    retention: 7 years         │                                         │
│  └───────────────────────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 The Five Bridge Mechanisms

#### Mechanism 1: The `neural` Keyword — Explicit Non-Determinism Boundary

```sigil
neural extract_symptoms from clinical_text: Text:
  model "medical-ner-v3"
  returns list of Text
  confidence_threshold 0.75
  fallback to empty list
```

This is not just a function call. It is a **formal declaration** that:
- Non-determinism enters the program here (and only here)
- The model is identified and versioned ("medical-ner-v3")
- The expected return type is specified and checked (`list of Text`)
- A minimum confidence threshold gates the output (0.75)
- A fallback strategy handles low-confidence results (`empty list`)
- The trace automatically records: model used, confidence received, threshold applied, whether fallback triggered

**No other language provides this.** Scallop's neural predicates don't specify confidence thresholds or fallbacks. DeepProbLog's neural predicates don't mandate model identification. Python code that calls an LLM API has no formal semantics for any of this.

#### Mechanism 2: Gradual Types at Boundaries — Contracts Between Worlds

```sigil
type Transaction is record:
  id: Text
  amount: Number
  currency: Symbol
  sender_pep_status: Boolean
  sender_sanctions_match: Boolean
```

The type system enforces that neural outputs conform to symbolic expectations. If the neural parser returns `amount: "one hundred"` instead of `amount: 100`, the type checker catches it at the boundary. Internal Sigil code can be untyped for rapid prototyping, but every neural→symbolic boundary requires explicit types.

#### Mechanism 3: Trace as Fundamental Output — Not Debugging

```sigil
rule sanctions_block with priority 100:
  when transaction sender_sanctions_match is true
  then risk is block with reason: "OFAC sanctions match"
  explain "Transaction blocked: sender matches OFAC sanctions list"
  trace:
    category :aml
    regulation "OFAC SDN"
    retention 7 years
    compliance [:bsa, :aml, :fatf, :ofac]
```

Every rule produces:
- **explain**: Human-readable justification
- **trace**: Machine-readable metadata including regulatory tags, retention policies, and compliance framework references

This is not optional debugging output. Traces are part of the program's formal semantics. A Sigil program that doesn't produce traces is like a function that doesn't return a value.

#### Mechanism 4: Constrained Natural Language — Domain Experts Can Audit

```sigil
when transaction amount exceeds CTR_THRESHOLD
and transaction currency is :usd
then risk is flag with reason: "CTR filing required"
```

A compliance officer can read this. A bank examiner can audit this. A regulator can verify this. The syntax is not Python, not Prolog, not Datalog — it is constrained English that parses as a formal PEG grammar. This is the same insight that made Inform 7 (interactive fiction) successful: constrained NL within a clear domain, backed by formal semantics.

#### Mechanism 5: Priority-Based Forward Chaining — Deterministic Rule Composition

```sigil
rule sanctions_block with priority 100:    -- fires first
rule pep_escalation with priority 95:      -- fires second
rule high_risk_jurisdiction with priority 90:
rule ctr_filing with priority 80:
rule transaction_clear with priority 1:    -- default: fires last
```

Rules compose deterministically. Same input → same rules fire → same output, always. The priority system ensures that critical safety checks (sanctions blocking) always run before routine checks (CTR filing), regardless of declaration order.

---

## 6. Domain Studies

### 6.1 Finance & Compliance (AML/KYC)

#### The Real-World Problem

Financial institutions process billions of transactions daily. Regulations (BSA/FinCEN, FATF, EU AMLD, OFAC) require:
- Every transaction above $10,000 generates a Currency Transaction Report (CTR)
- Politically Exposed Persons (PEPs) receive enhanced due diligence
- Sanctions screening blocks transactions to OFAC SDN list entities
- Suspicious activity triggers a Suspicious Activity Report (SAR)
- All decisions must be auditable for 5-7 years

**The neural component**: NLP parses transaction narratives, graph neural networks detect relationship patterns, anomaly detection identifies unusual behavior.

**The symbolic component**: Regulatory rules, risk thresholds, jurisdiction lists, compliance logic.

**The gap today**: JPMorgan reduced false-positive compliance alerts by 60% with AI — but the integration between AI models and compliance rules required custom engineering for each regulation. HSBC partnered with Silent Eight for AI compliance, but each new regulatory requirement needs new glue code.

#### Without Sigil: The Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              AML/KYC PIPELINE — WITHOUT SIGIL                              │
│                                                                             │
│  Transaction Stream ──▶ ETL Pipeline ──▶ Feature Store                     │
│         │                                      │                            │
│         ▼                                      ▼                            │
│  ┌──────────────┐                    ┌──────────────────┐                  │
│  │ NLP Model     │                    │ GNN Model         │                  │
│  │ (narrative    │                    │ (relationship     │                  │
│  │  parsing)     │                    │  patterns)        │                  │
│  └──────┬───────┘                    └────────┬─────────┘                  │
│         │ JSON                                │ JSON                        │
│         ▼                                      ▼                            │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │              PYTHON GLUE CODE                        │                   │
│  │  • parse_nlp_output()                                │                   │
│  │  • transform_gnn_scores()                            │                   │
│  │  • merge_risk_signals()                              │                   │
│  │  • apply_threshold_overrides()                       │                   │
│  │  • format_for_rules_engine()                         │                   │
│  │                                                      │                   │
│  │  ⚠️  500-2000 lines of custom Python                 │                   │
│  │  ⚠️  Confidence scores lost in transformation        │                   │
│  │  ⚠️  No type safety between model output and rules   │                   │
│  │  ⚠️  Different team maintains this vs models vs rules │                   │
│  └──────────────────────┬──────────────────────────────┘                   │
│                         │ REST API / Database                               │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────┐                              │
│  │        RULES ENGINE (Drools / OPA)       │                              │
│  │  • BSA thresholds                         │                              │
│  │  • OFAC screening logic                   │                              │
│  │  • PEP enhanced due diligence             │                              │
│  │  • Jurisdiction risk rules                │                              │
│  └──────────────────────┬───────────────────┘                              │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────┐                              │
│  │    SEPARATE LOGGING / AUDIT SYSTEM       │                              │
│  │  • Model outputs logged to System A       │                              │
│  │  • Glue code transforms logged to Sys B   │                              │
│  │  • Rule decisions logged to System C       │                              │
│  │  • Examiner must correlate across 3 logs  │                              │
│  └──────────────────────────────────────────┘                              │
│                                                                             │
│  Pain: 3 teams, 3 systems, 3 log formats, 1 audit = weeks of correlation  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### With Sigil: The Unified Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              AML/KYC PIPELINE — WITH SIGIL                                 │
│                                                                             │
│  Transaction Narrative                                                      │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    compliance_checker.sigil                          │    │
│  │                                                                     │    │
│  │  main:                                                              │    │
│  │    given narrative from input                                       │    │
│  │    given transaction as parse_transaction(narrative)   ◄── neural   │    │
│  │    evaluate all rules with transaction                 ◄── symbolic │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  neural parse_transaction from narrative: Text:             │    │    │
│  │  │    model "fin-ner-v2"                                      │    │    │
│  │  │    returns Transaction        ◄── typed contract           │    │    │
│  │  │    confidence_threshold 0.85  ◄── gates output             │    │    │
│  │  │    fallback to manual_review  ◄── graceful degradation     │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                         │                                           │    │
│  │                         ▼  (typed Transaction record)               │    │
│  │                                                                     │    │
│  │  rule sanctions_block with priority 100:                            │    │
│  │    when transaction sender_sanctions_match is true                  │    │
│  │    then risk is block with reason: "OFAC sanctions match"           │    │
│  │    trace: regulation "OFAC SDN", retention 7 years                  │    │
│  │                                                                     │    │
│  │  rule pep_escalation with priority 95:                              │    │
│  │    when transaction sender_pep_status is true                       │    │
│  │    and transaction amount exceeds 5000                              │    │
│  │    then risk is escalate with reason: "PEP with large transaction"  │    │
│  │                                                                     │    │
│  │  rule ctr_filing with priority 80:                                  │    │
│  │    when transaction amount exceeds 10000                            │    │
│  │    and transaction currency is :usd                                 │    │
│  │    then risk is flag with reason: "CTR filing required"             │    │
│  │    trace: regulation "BSA/FinCEN CTR"                               │    │
│  │                                                                     │    │
│  │  rule transaction_clear with priority 1:                            │    │
│  │    when risk is not assigned                                        │    │
│  │    then risk is clear                                               │    │
│  └──────────────────────────────────┬──────────────────────────────────┘    │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                  UNIFIED TRACE OUTPUT                             │       │
│  │                                                                   │       │
│  │  Decision: block                                                  │       │
│  │  Reason: "OFAC sanctions match"                                   │       │
│  │  Neural:                                                          │       │
│  │    model: "fin-ner-v2"                                            │       │
│  │    confidence: 0.92                                               │       │
│  │    threshold: 0.85                                                │       │
│  │    fallback_triggered: false                                      │       │
│  │  Rules fired:                                                     │       │
│  │    [1] sanctions_block (priority 100) → block                     │       │
│  │  Rules not fired:                                                 │       │
│  │    pep_escalation (condition: sender_pep_status=false)            │       │
│  │    ctr_filing (condition: amount=3200 < 10000)                    │       │
│  │  Compliance: [:bsa, :aml, :fatf, :ofac]                          │       │
│  │  Retention: 7 years                                               │       │
│  │  Timestamp: 2026-03-06T14:23:01Z                                  │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  Result: 1 file, 1 trace format, 1 audit = minutes, not weeks             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Evidence from the Domain

| Metric | Without Formal Bridge | With Sigil Architecture |
|--------|----------------------|------------------------|
| Integration teams required | 3 (ML, integration, rules) | 1 (Sigil + domain expertise) |
| Audit correlation time | Weeks (across 3 log systems) | Minutes (single trace) |
| False positive rate | High (confidence lost in transform) | Lower (confidence_threshold gates) |
| New regulation integration | Months (new glue code per regulation) | Days (new rules in constrained NL) |
| Examiner readability | Requires technical translator | Direct (constrained English) |

**Case study**: SymphonyAI NetReveal stops fraud within 50 milliseconds using behavioral profiling + AI models + adaptive rules. Their architecture mirrors the Sigil pattern but uses proprietary integration. Sigil provides this pattern as an open, standard language.

---

### 6.2 Healthcare & Clinical Decision Support

#### The Real-World Problem

Medical triage requires extracting symptoms from unstructured clinical text and applying standardized protocols (ESI v4) to assign severity levels. This must be:
- HIPAA compliant (audit trails, data retention)
- EMTALA compliant (no patient can be turned away from emergency care)
- Deterministic (same symptoms → same triage level, always)
- Auditable (why was this patient classified as ESI-3 and not ESI-2?)

**Key evidence**: Mendel.ai (July 2024) built a neuro-symbolic system that outperformed GPT-4 for clinical cohort retrieval. Architecture: LLM reads unstructured EMR text (neural) + Hypercube reasoning engine encodes trial criteria as logical rules (symbolic). The neuro-symbolic approach outperformed LLM-only baselines by **10.1% to 26.72% on F1-scores** across 113 complex oncology queries. (Source: BusinessWire, Clinical Trial Vanguard)

#### Without Sigil

```
┌────────────────────────────────────────────────────────────────────────┐
│           MEDICAL TRIAGE — WITHOUT SIGIL                               │
│                                                                        │
│  Clinical Notes (free text)                                            │
│         │                                                              │
│         ▼                                                              │
│  ┌──────────────┐     JSON      ┌──────────────┐     SQL/API          │
│  │ BioBERT NER  │──────────────▶│ Python ETL   │──────────────▶       │
│  │ (symptom     │               │ (transform,  │               │      │
│  │  extraction) │               │  normalize,  │      ┌────────▼────┐ │
│  └──────────────┘               │  validate)   │      │ ESI Rules   │ │
│                                 └──────────────┘      │ (hardcoded  │ │
│                                                       │  if/else in │ │
│                                       ⚠️  800 lines   │  Java/Python│ │
│                                       of transform    └──────┬──────┘ │
│                                       code                   │        │
│                                                              ▼        │
│                                                  ┌──────────────────┐ │
│                                                  │ Triage Decision  │ │
│                                                  │ (no trace of why │ │
│                                                  │  NER confidence  │ │
│                                                  │  was low)        │ │
│                                                  └──────────────────┘ │
│                                                                        │
│  Problem: If BioBERT extracts "chest_pain" with confidence 0.55,      │
│  the Python ETL either drops it (false negative → missed emergency)   │
│  or includes it (false positive → wasted resources). The threshold    │
│  is a magic number in line 347 of transform.py. No trace.            │
└────────────────────────────────────────────────────────────────────────┘
```

#### With Sigil

```sigil
-- medical_triage.sigil (from Sigil examples)

neural extract_symptoms from clinical_text: Text:
  model "medical-ner-v3"
  returns list of Text
  confidence_threshold 0.75         -- formal threshold, traced
  fallback to empty list            -- safe degradation

rule esi_level_1 with priority 100:
  when any symptom in patient.symptoms is in IMMEDIATE_SYMPTOMS
  or patient.vital_signs.oxygen_saturation is below 90
  then triage_level is esi_1 with label: "Resuscitation"
  explain "Immediate life threat detected"
  trace:
    protocol "ESI v4"
    compliance [:hipaa, :emtala]
    retention 10 years
```

The trace output records: which model extracted symptoms, at what confidence, whether fallback triggered, which ESI rule fired and why, protocol version, compliance tags, and retention requirements — all in one unified format.

**Mendel.ai parallel**: Mendel's Hypercube reasoning engine encodes clinical trial criteria as logical rules. Sigil provides the same architecture as a standard language — any hospital could implement their own triage protocols without building a proprietary reasoning engine.

---

### 6.3 Physical AI & Robotics

#### The Real-World Problem

Robots must perceive the physical world (neural: vision, tactile sensing, proprioception) and plan actions in it (symbolic: safety constraints, task decomposition, physics-based reasoning).

**NVIDIA's architecture (2025)**:
- **Cosmos Reason** (7B parameter reasoning VLM): Interprets visual input, predicts physical outcomes, generates step-by-step plans grounded in physics
- **GR00T N1.6**: Open VLA model integrating Cosmos Reason for contextual understanding with symbolic planning for task decomposition

**Amazon Vulcan**: Warehouse robot combining neural vision + tactile sensing (perception) with symbolic safety constraints + optimal placement logic (reasoning). Deployed at Spokane, WA fulfillment center.

#### The Pipeline Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHYSICAL AI PIPELINE                                           │
│                                                                             │
│  Sensors (cameras, LiDAR, tactile, proprioception)                         │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  NEURAL PERCEPTION                                                  │    │
│  │  • Object detection and classification                              │    │
│  │  • Spatial relationship estimation                                  │    │
│  │  • Force/torque interpretation                                      │    │
│  │  • Scene understanding                                              │    │
│  │                                                                     │    │
│  │  Output: Structured scene graph with confidence scores              │    │
│  └──────────────────────────┬──────────────────────────────────────────┘    │
│                             │                                               │
│                 ════════════╪════════════  THE BRIDGE                       │
│                             │                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  SYMBOLIC PLANNING (where Sigil could formalize)                    │    │
│  │                                                                     │    │
│  │  • Safety constraints: "gripper force must not exceed 10N on glass" │    │
│  │  • Task decomposition: "pick → inspect → place → verify"           │    │
│  │  • Physics rules: "object mass × height = potential energy risk"    │    │
│  │  • Compliance: "OSHA requirement: human distance > 2m when active"  │    │
│  │                                                                     │    │
│  │  Output: Verified action plan with safety trace                     │    │
│  └──────────────────────────┬──────────────────────────────────────────┘    │
│                             │                                               │
│                             ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  MOTOR EXECUTION                                                    │    │
│  │  • Action plan → joint trajectories                                 │    │
│  │  • Real-time feedback loop                                          │    │
│  │  • Safety interrupt if constraints violated                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Sigil potential: Formalize the safety constraint layer with typed          │
│  rules, confidence-gated neural perception, and OSHA compliance traces.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### How Sigil Would Formalize This

```sigil
-- robot_safety.sigil (hypothetical)

neural classify_object from camera_feed: Image:
  model "object-detector-v4"
  returns ObjectInfo
  confidence_threshold 0.90     -- high threshold for safety-critical
  fallback to :unknown_object   -- safe default: treat as fragile

type ObjectInfo is record:
  category: Symbol              -- :glass, :metal, :plastic, :organic
  mass_kg: Number
  fragility: Symbol             -- :fragile, :normal, :robust

rule glass_handling with priority 100:
  when object category is :glass
  or object category is :unknown_object       -- fallback treated as fragile
  then max_grip_force is 5 newtons
  and handling_speed is :slow
  explain "Glass or unknown object: reduced grip force for safety"
  trace:
    compliance [:osha, :iso_10218]

rule weight_limit with priority 95:
  when object mass_kg exceeds 25
  then action is :request_human_assist
  explain "Object exceeds single-arm weight limit"
  trace:
    compliance [:osha_ergonomic]
```

---

### 6.4 Computer Vision & Scene Understanding

#### The Real-World Problem

Scene understanding requires: (1) detecting objects in an image (neural), (2) classifying their attributes (neural), (3) inferring relationships between objects (neural + symbolic), and (4) answering questions or making decisions based on the scene structure (symbolic).

**Current approaches**:
- Neural-Symbolic VQA (MIT CSAIL): Neural scene parser → structured scene representation → symbolic program executor for logical reasoning
- Scene Graph Generation (SGG): Object detection → attribute classification → relationship prediction → scene graph construction
- NeuSyRE (2024): Neuro-symbolic visual understanding via scene graph enrichment

#### Data Flow: Scene Understanding Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              VISUAL QA PIPELINE                                             │
│                                                                             │
│  Raw Image                                                                  │
│      │                                                                      │
│      ▼                                                                      │
│  ┌──────────────────────────────┐                                          │
│  │  Object Detection (YOLO/DETR)│──▶ [{obj: "car", conf: 0.95, bbox:...}] │
│  └──────────────────────────────┘                                          │
│      │                                                                      │
│      ▼                                                                      │
│  ┌──────────────────────────────┐                                          │
│  │  Attribute Classification    │──▶ [{obj: "car", color: "red",           │
│  │  (ResNet/ViT)                │     size: "large", parked: true}]        │
│  └──────────────────────────────┘                                          │
│      │                                                                      │
│      ▼                                                                      │
│  ┌──────────────────────────────┐                                          │
│  │  Relationship Prediction     │──▶ [("car", "parked_on", "street"),      │
│  │  (GNN/Transformer)           │     ("person", "near", "car")]           │
│  └──────────────────────────────┘                                          │
│      │                                                                      │
│      ════════════════════════════  BRIDGE: scene graph → symbolic facts     │
│      │                                                                      │
│      ▼                                                                      │
│  ┌──────────────────────────────┐                                          │
│  │  Symbolic Reasoning          │                                          │
│  │  Q: "Is there a red car      │                                          │
│  │   near a person?"            │                                          │
│  │  A: filter(color=red) →      │                                          │
│  │     relate(near, person) →   │                                          │
│  │     exists() → TRUE          │                                          │
│  └──────────────────────────────┘                                          │
│                                                                             │
│  The bridge (scene graph → symbolic facts) is where each system             │
│  invents its own format. Sigil could standardize this with:                │
│                                                                             │
│  neural detect_scene from image: Image:                                    │
│    model "scene-graph-v3"                                                  │
│    returns SceneGraph                                                      │
│    confidence_threshold 0.80                                               │
│                                                                             │
│  rule answer_spatial_query:                                                │
│    when any object in scene.objects has color :red                         │
│    and any object in scene.objects has type :person                        │
│    and scene has_relation(:near, red_object, person)                       │
│    then answer is true                                                     │
│    explain "Red car found near person at coordinates..."                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 6.5 Autonomous Vehicles

#### The Real-World Problem

Self-driving vehicles combine neural perception (cameras, LiDAR, radar → object detection, lane tracking, pedestrian prediction) with symbolic reasoning (traffic laws, route planning, safety constraints). The consequences of errors are fatal.

**Key research (2025)**:
- **Road2Code**: Translates driving scenarios from camera/LiDAR into symbolic representations for AV certification
- **DQN + symbolic reasoning**: Achieves 98% accuracy in scenario-based decision-making
- **LLM integration**: Evaluates detected objects against world knowledge, reducing false positive rates by 23%

#### The Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              AUTONOMOUS VEHICLE DECISION PIPELINE                           │
│                                                                             │
│  Sensors: Cameras (8) + LiDAR (1-4) + Radar (5) + Ultrasonics (12)       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  NEURAL PERCEPTION STACK                                           │     │
│  │  • Sensor fusion → unified 3D scene representation                 │     │
│  │  • Object detection: vehicles, pedestrians, cyclists, signs        │     │
│  │  • Lane detection: boundaries, markings, road edges                │     │
│  │  • Trajectory prediction: where will each object be in 1-5 sec?    │     │
│  │  • Confidence: each detection has a probability score              │     │
│  └───────────────────────────┬────────────────────────────────────────┘     │
│                              │                                              │
│              ════════════════╪════════════  CRITICAL BRIDGE                 │
│              (decisions here are life-or-death)                             │
│                              │                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  SYMBOLIC REASONING STACK                                          │     │
│  │  • Traffic law encoding: speed limits, right-of-way, signal rules  │     │
│  │  • Safety constraints: minimum following distance, collision        │     │
│  │    avoidance zones, emergency stop conditions                      │     │
│  │  • Route planning: graph-based path optimization                   │     │
│  │  • Decision arbitration: which action to take given constraints     │     │
│  │                                                                    │     │
│  │  Every decision MUST produce a trace: what was detected,           │     │
│  │  at what confidence, which rules applied, why this action.         │     │
│  └───────────────────────────┬────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  ACTION: accelerate / brake / steer / stop                         │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  Sigil relevance: The safety constraint layer — encoding traffic laws,     │
│  collision avoidance rules, and emergency protocols as auditable,          │
│  confidence-gated, deterministic Sigil rules. Every decision traced.       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 6.6 Legal & Contract Analysis

#### The Real-World Problem

Legal contract review requires: (1) extracting clauses, obligations, and entities from unstructured legal text (neural NLP), and (2) comparing extracted elements against regulatory templates, compliance requirements, and internal policies (symbolic rules).

**Current players**: Luminance, Spellbook, ContractPodAi all use variations of neural NLP + rule-based compliance checking.

**A 2025 survey** (Springer) documents the evolution: rule-based (2019-2020) → deep learning (2021-2023) → LLM-based (2024-2025), with the current trend converging on hybrid neural-symbolic approaches for compliance auditing.

#### Sigil Formalization

```sigil
-- contract_review.sigil (hypothetical)

neural extract_clauses from contract_text: Text:
  model "legal-ner-v4"
  returns list of Clause
  confidence_threshold 0.80
  fallback to :manual_review

type Clause is record:
  type: Symbol            -- :termination, :liability, :confidentiality
  parties: list of Text
  obligations: list of Text
  duration: Text
  governing_law: Symbol

rule missing_termination_clause with priority 90:
  when none clause in clauses has type :termination
  then risk is flag with reason: "No termination clause found"
  explain "Contract missing standard termination provisions"
  trace:
    category :contract_review
    regulation "UCC Article 2"

rule unlimited_liability with priority 85:
  when any clause in clauses has type :liability
  and clause has_text "unlimited"
  then risk is escalate with reason: "Unlimited liability clause detected"
  explain "Liability clause contains unlimited exposure — requires partner review"
```

---

### 6.7 Manufacturing & Quality Control

#### The Real-World Problem

Manufacturing quality control requires: (1) detecting defects in real-time from camera feeds (neural computer vision), and (2) performing root cause analysis by modeling cause-and-effect relationships (symbolic/causal reasoning).

**Current approaches**:
- Logic Tensor Networks (LTN) combined with visual transformers for defect detection (ECCV 2024)
- Databricks causal AI for manufacturing root cause analysis
- ProSolvr AI-driven root cause analysis platform

#### Sigil Formalization

```sigil
-- quality_control.sigil (hypothetical)

neural detect_defect from camera_frame: Image:
  model "defect-detector-v5"
  returns DefectInfo
  confidence_threshold 0.85
  fallback to :no_defect          -- conservative: don't halt line on low confidence

type DefectInfo is record:
  defect_type: Symbol             -- :crack, :scratch, :discoloration, :none
  location: Text
  severity: Symbol                -- :critical, :major, :minor
  confidence: Number

rule critical_defect_halt with priority 100:
  when defect defect_type is not :none
  and defect severity is :critical
  then action is :halt_production_line
  and notification is :immediate_supervisor
  explain "Critical defect detected: {defect.defect_type} at {defect.location}"
  trace:
    category :quality
    compliance [:iso_9001, :iatf_16949]
    retention 5 years

rule recurring_defect_escalation with priority 80:
  when defect_count_last_hour exceeds 5
  and defect defect_type is same_as last_defect_type
  then action is :root_cause_analysis
  explain "Recurring {defect.defect_type} defects — triggering RCA"
  trace:
    category :quality
    procedure "SPC Out-of-Control Action Plan"
```

---

## 7. Data Flow Diagrams: With vs Without Sigil

### 7.1 Generic Pattern — Without Sigil

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WITHOUT SIGIL (Current State)                          │
│                                                                             │
│  ┌────────────┐   Unstructured   ┌────────────┐   JSON/    ┌────────────┐ │
│  │ Data Source │──────────────────▶│Neural Model│───CSV/────▶│   Glue     │ │
│  │ (text/img/ │   data           │(LLM/CNN/   │  REST API  │   Code     │ │
│  │  sensor)   │                  │ GNN)       │            │  (Python)  │ │
│  └────────────┘                  └────────────┘            └─────┬──────┘ │
│                                                                  │        │
│  Lost: confidence scores, model version, extraction metadata     │        │
│                                                                  ▼        │
│                                                          ┌────────────┐   │
│  ┌────────────┐   Separate       ┌────────────┐         │ Rules      │   │
│  │ Log System │◀──logging────────│ Log System │◀────────│ Engine     │   │
│  │ A (model)  │                  │ B (glue)   │         │(Drools/OPA)│   │
│  └────────────┘                  └────────────┘         └─────┬──────┘   │
│                                                               │          │
│                                         ┌────────────┐        │          │
│                                         │ Log System │◀───────┘          │
│                                         │ C (rules)  │                   │
│                                         └────────────┘                   │
│                                                                          │
│  Integration: 3 teams, 3 systems, weeks to audit, confidence lost,      │
│  no standard trace, brittle transforms, no fallback semantics            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Generic Pattern — With Sigil

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WITH SIGIL (Proposed State)                             │
│                                                                             │
│  ┌────────────┐   Unstructured                                             │
│  │ Data Source │──────data───────────────────────────────────┐              │
│  │ (text/img/ │                                             │              │
│  │  sensor)   │                                             │              │
│  └────────────┘                                             │              │
│                                                             ▼              │
│                              ┌───────────────────────────────────────┐     │
│                              │         program.sigil                  │     │
│                              │                                       │     │
│                              │  neural perception from input:        │     │
│                              │    model "model-v3"                   │     │
│                              │    returns StructuredType             │     │
│                              │    confidence_threshold 0.85          │     │
│                              │    fallback to safe_default           │     │
│                              │         │                             │     │
│                              │         ▼ (typed, checked, traced)    │     │
│                              │                                       │     │
│                              │  rule high_priority with priority N:  │     │
│                              │    when condition                     │     │
│                              │    then decision                      │     │
│                              │    explain "reason"                   │     │
│                              │    trace: compliance [...]            │     │
│                              │         │                             │     │
│                              │         ▼                             │     │
│                              │  ┌─────────────────────────────┐     │     │
│                              │  │ UNIFIED TRACE               │     │     │
│                              │  │ • Neural: model, confidence │     │     │
│                              │  │ • Symbolic: rules, reasons  │     │     │
│                              │  │ • Compliance: regulations   │     │     │
│                              │  │ • Retention: policy          │     │     │
│                              │  └─────────────────────────────┘     │     │
│                              └───────────────────────────────────────┘     │
│                                                                             │
│  Integration: 1 file, 1 team, 1 trace format, minutes to audit,          │
│  confidence-gated, typed contracts, formal fallback semantics              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 The Sigil Execution Flow (Internal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SIGIL INTERNAL EXECUTION PIPELINE                        │
│                                                                             │
│  .sigil source file                                                        │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐    Token     ┌──────────────┐    AST     ┌────────────┐ │
│  │    Lexer      │───stream───▶│    Parser     │──────────▶│   Type     │ │
│  │  (tokenize)   │             │  (PEG-based   │           │  Checker   │ │
│  │               │             │   recursive   │           │ (gradual)  │ │
│  └──────────────┘             │   descent)    │           └─────┬──────┘ │
│                                └──────────────┘                 │        │
│                                                                 ▼        │
│                                                         ┌────────────┐   │
│  ┌──────────────┐                                       │Tree-Walking│   │
│  │  Python FFI   │◀──── import python transformers ────│Interpreter │   │
│  │  (ML libs)    │                                     │            │   │
│  └──────────────┘                                       └─────┬──────┘   │
│         │                                                     │          │
│         │  neural call ──▶ model invocation ──▶ result        │          │
│         │  (confidence checked, fallback applied)              │          │
│         │                                                     │          │
│         └─────────────────────────────────────────────────────┘          │
│                                    │                                      │
│                                    ▼                                      │
│                          ┌────────────────┐                               │
│                          │  Decision       │                               │
│                          │  + Trace        │                               │
│                          │  + Explain      │                               │
│                          └────────────────┘                               │
│                                                                           │
│  Future: Rust core (PyO3) for constraint solving + pattern matching      │
│  Future: Bytecode VM for 10-100x performance over tree-walking           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Comparative Analysis: Sigil vs Existing Approaches

### 8.1 Comparison Matrix

| Feature | Sigil | Scallop | DeepProbLog | JSON/YAML + Python | Drools/OPA | LMQL/DSPy |
|---------|-------|---------|-------------|-------------------|------------|-----------|
| **Human readable** | Very High (constrained NL) | Low (Datalog) | Low (Prolog) | Medium | Medium (DRL) | Medium |
| **LLM can generate it** | High (AI-native grammar) | Low | Low | High (but no semantics) | Low | Medium |
| **Deterministic execution** | Yes (by design) | Partial (probabilistic) | No (probabilistic) | Depends on code | Yes | No |
| **Neural integration** | First-class (`neural` keyword) | First-class (neural predicates) | First-class (neural predicates) | Manual | None | First-class |
| **Confidence thresholds** | Built-in | Via provenance | Implicit | Manual if/else | None | None |
| **Fallback semantics** | Built-in | None | None | Manual try/except | None | None |
| **Execution traces** | Fundamental output | Provenance semirings | Proof trees | Manual logging | Audit logs | None |
| **Compliance metadata** | Built-in (trace: compliance [...]) | None | None | Manual | Manual | None |
| **Type system** | Gradual (required at boundaries) | Typed (Datalog types) | Typed (Prolog terms) | None | Weak | None |
| **Domain expert accessible** | Yes (reads like English) | No | No | No | Partially | No |
| **Differentiable** | No (by design) | Yes | Yes | N/A | No | N/A |
| **Target audience** | Domain experts + developers | ML researchers | Logic programmers | Everyone (default) | Enterprise dev | ML engineers |

### 8.2 Key Differentiators

**Sigil vs Scallop**: Scallop is the closest existing language. Both are dedicated neuro-symbolic DSLs. But they serve fundamentally different purposes:
- Scallop enables **differentiable reasoning** — you can train neural networks through symbolic logic layers
- Sigil enables **auditable decision-making** — neural perception feeds deterministic rules with full traces
- Scallop uses Datalog syntax (for ML researchers); Sigil uses constrained NL (for domain experts)
- Scallop's provenance tracks *how* a conclusion was derived; Sigil's traces track *why* a decision was made and *which regulations apply*

**Sigil vs LMQL/DSPy/LangChain**: These make LLMs smarter at deciding. Sigil makes LLMs unnecessary for deciding — they only parse.

**Sigil vs JSON/YAML + Python**: This is the real competitor — it's what everyone uses today. Sigil replaces the 500-2000 lines of Python glue code, the untyped JSON transforms, the scattered logging, and the ad-hoc threshold handling with a single, auditable, typed language.

### 8.3 Where Sigil Fits in the Kautz Taxonomy

Henry Kautz's six-type taxonomy (AAAI 2020 presidential address) classifies neuro-symbolic integration patterns:

| Type | Pattern | Sigil? |
|------|---------|--------|
| Type 1 | Standard neural (pure LLM) | No |
| Type 2 | Symbolic[Neural] — symbolic system orchestrates neural components | **YES** |
| Type 3 | Neural\|Symbolic — neural and symbolic operate in parallel pipeline | **YES** |
| Type 4 | Neural ∪ Compile(Symbolic) — compile knowledge into neural networks | Future |
| Type 5 | Neural_{Symbolic} — differentiable symbolic reasoning | No (this is Scallop) |
| Type 6 | Neural[Symbolic] — fully integrated (doesn't yet exist) | Vision |

Sigil operates at **Type 2-3**: the symbolic engine (Sigil's rule evaluator) orchestrates neural components (via the `neural` keyword). This is the same pattern used by **AlphaGeometry** (Nature, 2024) — the most successful deployed neuro-symbolic system — where a symbolic deduction engine orchestrates a neural language model.

---

## 9. The Evidence: Why the Bridge Matters

### 9.1 Academic Evidence

| Study | Finding | Relevance to Sigil |
|-------|---------|-------------------|
| **Mendel.ai** (July 2024) | Neuro-symbolic outperforms GPT-4 by 10-27% on clinical cohort retrieval | Neural-only fails; hybrid architecture wins |
| **AlphaGeometry** (Nature, Jan 2024) | Solves 25/30 Olympiad geometry problems (human gold: 25.9) | Type 2 NeSy (symbolic[neural]) matches human experts |
| **Dziri et al.** (NeurIPS 2023) | LLM accuracy degrades exponentially with reasoning steps | LLMs fundamentally cannot replace symbolic reasoning |
| **Valmeekam et al.** (NeurIPS 2023) | LLMs fail at classical planning even with Chain-of-Thought | Symbolic planning remains necessary |
| **MoonBit** (ICSE 2024) | AI-friendly grammar design improves LLM code generation | Sigil's ~30 keyword, flat grammar is validated |
| **SimPy** (ICSE 2024) | Grammar reduces LLM token usage by 13.5% | Language design directly impacts AI generation efficiency |
| **167-paper systematic review** (arXiv:2501.05435, 2024) | Only 28% of NeSy papers address explainability; 5% address meta-cognition | Sigil's trace-first design fills the biggest gap |
| **Symbol Grounding** (arXiv:2510.14538, 2025) | NeSy models learn "reasoning shortcuts" with wrong internal representations | Formal typed interfaces (Sigil's approach) prevent this |

### 9.2 Industry Evidence

| Company | Investment | Architecture Pattern | Sigil Alignment |
|---------|-----------|---------------------|-----------------|
| **Amazon** | VP-level (Byron Cook) + warehouse deployment | Neural perception + symbolic safety constraints + automated reasoning verification | Direct match: `neural` → typed rules → traces |
| **IBM** | Dedicated research program; "path to AGI" | Plan-SOFAI (fast neural + slow symbolic); NVSA; NuCLeaR workshop | Type 2 NeSy architecture matches Sigil |
| **Google DeepMind** | AlphaGeometry, AlphaProof | Neural suggestion + symbolic verification loops | Identical pattern: neural proposes, symbolic verifies |
| **Meta** | Neural theorem proving (10 IMO problems) | LLM generates proof steps + formal verifier checks each step | neural → symbolic verification |
| **NVIDIA** | Cosmos Reason (7B VLM) + GR00T N1.6 | Neural perception → symbolic task decomposition → motor execution | neural → rules → action (Sigil's exact pipeline) |
| **EY-Parthenon** | Commercial launch (Sept 2025) | Neurosymbolic AI for business strategy — "completely traceable" | Trace-first philosophy matches Sigil |
| **JPMorgan** | $2B AI investment | AI reduces false positives 60%; detection time from weeks to 8 days | Confidence-gated neural + compliance rules |

### 9.3 Regulatory Evidence

| Regulation | Requirement | How Sigil Addresses It |
|-----------|-------------|----------------------|
| **EU AI Act** (2024) | High-risk AI systems must provide explanations and maintain human oversight | `explain` clauses + `trace` metadata + deterministic execution |
| **FinCEN BSA/AML** (2024 proposed rule) | AI in AML must have "greater precision in risk assessment" and audit trails | `confidence_threshold` + `trace: regulation "BSA/FinCEN CTR"` |
| **HIPAA** | Protected health information must have access logs and audit trails | `trace: compliance [:hipaa], retention 10 years` |
| **EMTALA** | Emergency medical treatment decisions must be documented | `trace: protocol "ESI v4", compliance [:emtala]` |
| **OFAC** | Sanctions screening must be documented and auditable | `trace: regulation "OFAC SDN", retention 7 years` |
| **ISO 9001** | Quality management decisions must be traceable | `trace: compliance [:iso_9001]` |
| **OSHA** | Workplace safety decisions must be documented | `trace: compliance [:osha]` |

### 9.4 The Timing Argument

The convergence of four trends makes 2025-2026 the right moment for Sigil:

1. **LLM limitations exposed**: Research from 2023-2024 (Dziri, Valmeekam) formally proved that LLMs cannot reliably reason. The industry is looking for symbolic complements.

2. **Regulatory mandates increasing**: EU AI Act, FinCEN rules, HIPAA updates — all requiring explainable, auditable AI decisions. Traces are becoming legally mandatory.

3. **Major companies investing**: Amazon, IBM, Google, Meta, NVIDIA, EY-Parthenon all launched or expanded neurosymbolic AI programs in 2024-2025. The market is validating the approach.

4. **No standard language exists**: Every company builds custom bridges. Scallop and DeepProbLog serve researchers. No language serves the domain expert who needs to write and audit neurosymbolic decision logic. This is Sigil's gap.

---

## 10. Sources & References

### Academic Papers

1. Garcez et al. (2017). "Neural-Symbolic Computing: An Effective Methodology for Principled Integration of Machine Learning and Reasoning." *JAIR*. 58-page survey establishing neuro-symbolic taxonomy.
2. Kautz, H. (2020). "The Third AI Summer." *AAAI Presidential Address*. Six-type neuro-symbolic taxonomy.
3. Trinh et al. (2024). "Solving Olympiad Geometry without Human Demonstrations." *Nature*. AlphaGeometry.
4. Li et al. (2023). "Scallop: A Language for Neurosymbolic Programming." *PLDI*. Closest existing language to Sigil.
5. Manhaeve et al. (2018). "DeepProbLog: Neural Probabilistic Logic Programming." *NeurIPS*.
6. Wei et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS*.
7. Dziri et al. (2023). "Faith and Fate: Limits of Transformers on Compositionality and Reasoning." *NeurIPS*.
8. Valmeekam et al. (2023). "On the Planning Abilities of Large Language Models." *NeurIPS*.
9. Ellis et al. (2021). "DreamCoder: Bootstrapping Inductive Program Synthesis with Wake-Sleep Library Learning." *PLDI*.
10. arXiv:2501.05435 (2024). "Neuro-Symbolic AI in 2024: A Systematic Review." 167-paper review.
11. arXiv:2509.07122 (2025). "Neuro-Symbolic Frameworks: Conceptual Characterization and Empirical Comparative Analysis."
12. arXiv:2510.14538 (2025). "Symbol Grounding in Neuro-Symbolic AI: A Gentle Introduction to Reasoning Shortcuts."
13. arXiv:2411.04383 (2024). "Neuro-Symbolic AI: Explainability, Challenges, and Future Trends."
14. arXiv:2511.17644 (2025). "Hybrid Neuro-Symbolic Models for Ethical AI in Risk-Sensitive Domains."
15. MoonBit Team (2024). "AI-Friendly Language Design." *LLM4Code @ ICSE*.
16. arXiv:2404.16333 (2024). "SimPy: Grammar for AI-Friendly Code Generation." *ICSE*.

### Industry Sources

17. Amazon / Byron Cook — Automated Reasoning Checks. *Fast Company* (2025).
18. Amazon Vulcan Robot. *SiliconANGLE* (2025).
19. AWS Neurosymbolic AI for Regulated Industries. *VentureBeat* (2025).
20. IBM Neuro-Symbolic AI Research Program. *research.ibm.com*.
21. IBM Plan-SOFAI. *AAAI 2024*.
22. Google DeepMind AlphaGeometry. *deepmind.google/blog* (2024).
23. Google DeepMind AlphaProof. *deepmind.google/blog* (2024).
24. Meta Neural Theorem Proving. *ai.meta.com/blog* (2024).
25. NVIDIA Isaac Platform. *developer.nvidia.com*.
26. NVIDIA Cosmos Reason / GR00T N1.6. *nvidianews.nvidia.com* (2025).
27. EY-Parthenon Neurosymbolic AI. *ey.com/newsroom* (2025).
28. Mendel.ai vs GPT-4. *BusinessWire* (2024).
29. JPMorgan AI Strategy. *Klover.ai* (2025).
30. HSBC AI Compliance. *PaymentsJournal* (2025).
31. SymphonyAI NetReveal. *symphonyai.com*.
32. McKinsey: Agentic AI in Banking. *mckinsey.com* (2025).
33. WEF: The Power of Neurosymbolic AI. *weforum.org* (2025).
34. Nature Communications Medicine: Neurosymbolic AI for Medical Reports (2025).

### Regulatory References

35. FinCEN BSA/AML Proposed Rule (June 2024).
36. EU AI Act (2024).
37. HIPAA (Health Insurance Portability and Accountability Act).
38. EMTALA (Emergency Medical Treatment and Labor Act).
39. OFAC SDN (Specially Designated Nationals and Blocked Persons List).
40. ISO 9001 (Quality Management Systems).
41. FATF Risk-Based Approach to AML/CFT.

---

*This document was researched and compiled on March 6, 2026. All sources verified as of that date.*
*For the latest project status, see `ai_docs/STATUS.md`.*
