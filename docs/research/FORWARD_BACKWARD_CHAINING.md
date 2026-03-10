# Forward Chaining & Backward Chaining — What They Are

> Not a compiler thing. A **reasoning engine** thing. This doc explains both, when to use which, and how Sigil implements them.

---

## 0. The Short Answer

**Is this a compiler concept?** No.

Forward and backward chaining are **runtime reasoning strategies** — they determine how a rule engine evaluates rules against data. They belong to the **interpreter/evaluator**, not the compiler/parser.

```
Compiler concepts:           Runtime/reasoning concepts:
  Lexing                       Forward chaining      ← this doc
  Parsing (PEG)                Backward chaining     ← this doc
  AST construction             Conflict resolution
  Type checking                Trace generation
```

The compiler turns text into a tree. The chaining engine decides **what to do with that tree**.

---

## 1. The Setup: Rules + Facts

Both strategies operate on the same two things:

**Facts** — things we know to be true:
```
age = 35
credit_score = 720
income = 85000
```

**Rules** — if-then relationships:
```
Rule 1: IF age between 21 and 65       THEN age_eligible = true
Rule 2: IF credit_score exceeds 680    THEN credit_ok = true
Rule 3: IF income exceeds 50000        THEN income_ok = true
Rule 4: IF age_eligible AND credit_ok AND income_ok  THEN loan_approved = true
```

The question: **how do we get from facts to conclusions?**

There are exactly two directions to reason, and they have different names.

---

## 2. Forward Chaining — "What Can I Conclude?"

### Direction: Facts → Conclusions (data-driven)

Forward chaining starts with what you **know** and asks: "given these facts, which rules fire?"

```
Step 1: We know age=35, credit_score=720, income=85000
        Check all rules against known facts.

Step 2: Rule 1 fires (age between 21 and 65) → age_eligible = true
        Rule 2 fires (credit_score > 680)    → credit_ok = true
        Rule 3 fires (income > 50000)         → income_ok = true

        New facts added. Check all rules again.

Step 3: Rule 4 fires (all three are true)     → loan_approved = true

        New fact added. Check all rules again.

Step 4: No new rules fire. Done.
        RESULT: loan_approved = true
```

### How It Works

```
                    ┌──────────────┐
                    │  Known Facts │ ◄─── Start here
                    └──────┬───────┘
                           │
                           ▼
                  ┌──────────────────┐
             ┌───►│  Check ALL rules  │
             │    └────────┬─────────┘
             │             │
             │     Any rule fires?
             │        │         │
             │       Yes        No ──► DONE (fixed point)
             │        │
             │        ▼
             │    ┌─────────────┐
             │    │ Execute rule │
             │    │ Add new facts│
             │    └─────────────┘
             │        │
             └────────┘  (loop until no new facts)
```

### Key Properties

| Property | Value |
|----------|-------|
| **Direction** | Data → conclusions |
| **Question answered** | "What follows from what I know?" |
| **Termination** | When no new rules fire (fixed point) |
| **Completeness** | Derives everything derivable from the facts |
| **When to use** | You have data and want all possible conclusions |
| **Analogy** | A doctor examining a patient: "You have fever, cough, fatigue → this could be flu, COVID, or cold" |

### Real-World Examples

- **Monitoring systems**: sensor readings come in → rules fire alerts
- **Spam filters**: email features → classification rules → spam/not-spam
- **Medical diagnosis**: symptoms → condition rules → possible diagnoses
- **Sigil's `evaluate all rules`**: runs forward chaining until fixed point

---

## 3. Backward Chaining — "Can I Prove This?"

### Direction: Goal → Supporting Facts (goal-driven)

Backward chaining starts with what you **want to prove** and asks: "what facts do I need to make this true?"

```
Goal: Prove loan_approved = true

Step 1: Which rules conclude loan_approved?
        → Rule 4: IF age_eligible AND credit_ok AND income_ok

Step 2: I need to prove age_eligible, credit_ok, and income_ok.

        Subgoal: Prove age_eligible
        → Rule 1: IF age between 21 and 65
        → age = 35 → YES, age_eligible = true ✓

        Subgoal: Prove credit_ok
        → Rule 2: IF credit_score exceeds 680
        → credit_score = 720 → YES, credit_ok = true ✓

        Subgoal: Prove income_ok
        → Rule 3: IF income exceeds 50000
        → income = 85000 → YES, income_ok = true ✓

Step 3: All subgoals proved → loan_approved = true ✓
        RESULT: loan_approved = true (with proof tree)
```

### How It Works

```
                    ┌──────────────┐
                    │     GOAL     │ ◄─── Start here
                    └──────┬───────┘
                           │
                           ▼
                  ┌──────────────────────┐
                  │ Find rules that       │
                  │ conclude this goal    │
                  └────────┬─────────────┘
                           │
                           ▼
                  ┌──────────────────────┐
                  │ For each condition    │
                  │ in the rule:          │
                  │                       │
                  │ Is it a known fact?   │
                  │   Yes → continue      │
                  │   No  → RECURSE       │◄── backward chain on the subgoal
                  └────────┬─────────────┘
                           │
                    All conditions met?
                      │           │
                     Yes          No ──► Try next rule / FAIL
                      │
                      ▼
                  ┌─────────────┐
                  │ Goal proved! │
                  │ Return proof │
                  │    tree      │
                  └─────────────┘
```

### Key Properties

| Property | Value |
|----------|-------|
| **Direction** | Goal → supporting facts |
| **Question answered** | "Is this goal achievable? Why or why not?" |
| **Termination** | When goal is proved or all paths exhausted |
| **Efficiency** | Only evaluates rules relevant to the goal |
| **When to use** | You have a specific question and want a proof |
| **Analogy** | A detective: "Was it murder? → I need motive, means, opportunity → Did they have a motive? → ..." |

### Real-World Examples

- **Expert systems**: "Is this patient at risk for X?" → trace back through diagnostic rules
- **Logic programming** (Prolog): every query is backward chaining
- **Tax software**: "Am I eligible for this deduction?" → check qualifying conditions
- **Sigil's `query` statement**: backward chaining with proof tree (max depth 50, cycle detection)

---

## 4. Side-by-Side Comparison

```
FORWARD CHAINING                    BACKWARD CHAINING
(data-driven)                       (goal-driven)

  facts ──────► conclusions           goal
                                       │
  "I have these facts.               "I want to prove this.
   What can I conclude?"              What do I need?"

  age=35 ──► age_eligible            loan_approved?
  score=720 ──► credit_ok              ├── age_eligible?
  income=85k ──► income_ok             │     └── age between 21-65? ✓
  all three ──► loan_approved          ├── credit_ok?
                                       │     └── score > 680? ✓
                                       └── income_ok?
                                             └── income > 50k? ✓
```

| Dimension | Forward Chaining | Backward Chaining |
|-----------|-----------------|-------------------|
| **Starts with** | Known facts | A goal to prove |
| **Direction** | Bottom-up (facts → conclusions) | Top-down (goal → facts) |
| **Evaluates** | ALL rules (exhaustive) | Only RELEVANT rules |
| **Output** | All derivable conclusions | Proof tree for one goal |
| **Efficiency** | Explores everything | Focused on the question |
| **Best for** | Monitoring, alerting, classification | Diagnosis, verification, explanation |
| **Trace** | "These rules fired in this order" | "Here's WHY this is true" |
| **Sigil keyword** | `evaluate all rules` | `query` |

---

## 5. They're Not Opposites — They're Complementary

Most real systems use **both**:

```sigil
-- FORWARD CHAINING: evaluate all rules, derive everything
main:
  given applicant from input
  evaluate all rules with applicant

  -- At this point, all derivable facts are in the environment
  -- age_eligible, credit_ok, income_ok, loan_approved, etc.

-- BACKWARD CHAINING: prove a specific goal, get a proof tree
main:
  given applicant from input
  query loan_approved with applicant

  -- At this point, we have a proof tree:
  -- loan_approved was proved via Rule 4
  --   which needed age_eligible (proved via Rule 1)
  --   which needed credit_ok (proved via Rule 2)
  --   which needed income_ok (proved via Rule 3)
```

**Forward chaining** is like casting a wide net — "tell me everything."
**Backward chaining** is like asking a specific question — "prove this one thing."

### When to Use Which

| Scenario | Use |
|----------|-----|
| Incoming sensor data → what alerts to fire? | Forward |
| User asks "am I eligible for this loan?" | Backward |
| Batch processing a dataset | Forward |
| Debugging why a decision was made | Backward |
| Real-time monitoring | Forward |
| Compliance check ("does this meet regulation X?") | Backward |
| "What can I conclude from these symptoms?" | Forward |
| "Could this patient have condition X?" | Backward |

---

## 6. How Sigil Implements Them

### Forward Chaining (Phase 1 — Implemented)

Location: `src/sigil/interpreter/evaluator.py`

```python
def _forward_chain(self, rules, env):
    """Iterative forward chaining until fixed point."""
    fired_rules = set()
    for iteration in range(MAX_ITERATIONS):  # 100 max
        new_fires = False
        for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
            if rule.name in fired_rules:
                continue  # already fired, skip
            if self._conditions_met(rule, env):
                env = self._execute_action(rule, env)
                fired_rules.add(rule.name)
                new_fires = True
                self._record_trace(rule)  # trace every evaluation
        if not new_fires:
            break  # fixed point reached
    return env
```

Key implementation details:
- **Priority ordering**: Higher priority rules fire first
- **Fixed point**: Stops when no new rules fire
- **No re-firing**: Each rule fires at most once (`fired_rules` set)
- **Max iterations**: Safety limit of 100 prevents infinite loops
- **Traces**: Every rule evaluation is recorded

### Backward Chaining (Phase 2 Sprint 3 — Implemented)

Location: `src/sigil/interpreter/backward.py`

```python
def query(self, goal: str, depth: int = 0) -> ProofNode:
    """Try to prove a goal by backward chaining."""
    # Base case: goal is already a known fact
    if goal in self.env and self.env[goal] is not UNBOUND:
        return ProofNode(goal=goal, result=True)

    # Recursive case: find rules that conclude this goal
    for rule in self._rules_for(goal):
        subgoals = []
        all_met = True
        for condition in rule.conditions:
            if not self._is_satisfied(condition):
                # Recurse: try to prove this condition
                sub = self.query(condition.variable, depth + 1)
                subgoals.append(sub)
                if not sub.result:
                    all_met = False
                    break
        if all_met:
            return ProofNode(goal=goal, rule=rule, subgoals=subgoals, result=True)

    return ProofNode(goal=goal, result=False)  # unprovable
```

Key implementation details:
- **Max depth**: Safety limit prevents infinite recursion (50)
- **Proof tree**: Returns a tree showing exactly how the goal was proved
- **Rule indexing**: Rules indexed by their conclusion for fast lookup
- **Traces**: Proof tree is added to the program trace

---

## 7. Neuro-Symbolic AI — Where Chaining Fits In

Forward and backward chaining are not just classical AI relics. They are the **symbolic half** of every neuro-symbolic system. Understanding how they fit into the neuro-symbolic pipeline is key to understanding why Sigil exists.

### 7.1 The Neuro-Symbolic Pipeline

Every neuro-symbolic system has the same fundamental shape:

```
Raw World ──► [Neural Layer] ──► Structured Facts ──► [Symbolic Layer] ──► Decision + Trace
               perception          extraction            reasoning           output
               (probabilistic)     (bridge)              (deterministic)     (auditable)
```

**The neural layer** handles what computers are bad at — understanding messy, ambiguous, unstructured input. An LLM reads a patient's complaint. A vision model recognizes objects. A speech model transcribes audio. The output is structured data: extracted entities, classifications, confidence scores.

**The symbolic layer** handles what LLMs are bad at — deterministic, auditable, reproducible reasoning over that structured data. This is where chaining lives.

```
Neural Layer:                          Symbolic Layer:
  "Patient reports chest pain          Facts:
   and shortness of breath"              symptom_1 = :chest_pain
           │                             symptom_2 = :shortness_of_breath
           │  (LLM extraction)           severity = :high
           │                             confidence = 0.92
           ▼                                    │
   { symptoms: [chest_pain,                     │  Forward chaining:
     shortness_of_breath],                      │  "What follows from these facts?"
     severity: high,                            ▼
     confidence: 0.92 }                  triage_level = :emergency
                                         trace: "Rule critical_symptom fired
                                                 because chest_pain ∈ CRITICAL_SET"
```

**Forward and backward chaining ARE the symbolic layer.** They are the reasoning engine that makes neuro-symbolic AI deterministic and auditable.

### 7.2 Why LLMs Can't Replace Chaining

LLMs can do something that looks like reasoning:

```
Prompt: "Given credit_score=720, income=85000, age=35, is this applicant eligible for a loan?"
LLM:    "Yes, the applicant appears eligible because their credit score exceeds
         the typical threshold of 680 and their income is sufficient..."
```

This looks right. But it has three fatal problems:

| Problem | Why It's Fatal |
|---------|---------------|
| **Non-deterministic** | Ask the same question twice, get different wording. Change the temperature, get a different decision. Run it tomorrow, the model weights may have changed. |
| **No trace** | "Appears eligible" is not a proof. Which rule fired? What threshold was used? Was the age check performed? You cannot audit what didn't happen in a structured way. |
| **Hallucination** | The LLM might say "credit score exceeds 680" even if the threshold is actually 700 in your policy. It's pattern-matching on training data, not evaluating your rules. |

Forward/backward chaining solves all three:

| Property | LLM "Reasoning" | Symbolic Chaining |
|----------|-----------------|-------------------|
| **Same input → same output?** | No | Yes, always |
| **Auditable trace?** | No (free-text explanation) | Yes (structured proof tree) |
| **Hallucination risk?** | Yes | Impossible — rules are source code |
| **Modifiable rules?** | Retrain or re-prompt | Edit a `.sigil` file |
| **Regulatory compliance?** | Difficult to certify | Trace satisfies audit |

### 7.3 The Split: Neural Perceives, Chaining Decides

In a neuro-symbolic system, the division of labor is:

```
NEURAL does:                         CHAINING does:
  Read natural language                Evaluate rules against facts
  Extract entities                     Fire rules deterministically
  Classify intent                      Produce auditable traces
  Score confidence                     Prove or disprove goals
  Handle ambiguity                     Enforce business logic
  Generalize from examples             Guarantee reproducibility
```

This maps directly to Sigil's language design:

```sigil
-- NEURAL: perception (probabilistic, explicit boundary)
neural extract_symptoms from clinical_text: Text:
  model "medical-ner-v3"
  returns list of Text
  confidence_threshold 0.75
  fallback to empty list

-- FORWARD CHAINING: derive all conclusions from extracted facts
rule critical_symptom with priority 100:
  when any symptom in symptoms is in CRITICAL_SET
  then triage_level is :emergency
  explain "Critical symptom detected — immediate escalation"

rule moderate_symptom with priority 50:
  when any symptom in symptoms is in MODERATE_SET
  and not triage_level is :emergency
  then triage_level is :urgent
  explain "Moderate symptom detected — urgent care"

main:
  given symptoms from extract_symptoms(patient.notes)
  evaluate all rules with symptoms
  -- Forward chaining fires critical_symptom first (priority 100),
  -- then moderate_symptom checks but triage_level is already :emergency

-- BACKWARD CHAINING: prove why a specific decision was made
main:
  given symptoms from extract_symptoms(patient.notes)
  query triage_level
  -- Proof tree: triage_level = :emergency
  --   because critical_symptom fired
  --     because "chest_pain" ∈ CRITICAL_SET
```

### 7.4 Real Neuro-Symbolic Use Cases and Which Chaining They Need

| Use Case | Neural Layer Does | Chaining Type | Symbolic Layer Does |
|----------|-------------------|---------------|---------------------|
| **Medical Triage** | NER extracts symptoms from patient text | Forward | Evaluate all triage rules → assign level |
| **Loan Eligibility** | OCR/NLP extracts fields from application documents | Forward | Evaluate all eligibility criteria → approve/deny |
| **Fraud Detection** | Anomaly model scores transactions | Forward | Fire alert rules when risk score + patterns match |
| **Compliance Audit** | NLP parses regulatory text into structured requirements | Backward | "Does transaction X satisfy regulation Y?" → proof tree |
| **Insurance Claims** | NLP extracts claim details from free-text submissions | Both | Forward: classify claim type. Backward: "Is this claim valid under policy Z?" |
| **Conversational Agents** | LLM understands user intent from natural language | Forward | State machine fires transition rules based on intent + state |
| **Content Moderation** | Classifier labels content (toxic, spam, safe) | Forward | Policy rules decide action: remove, flag, allow |
| **Supply Chain Decisions** | Demand forecasting models predict shortages | Backward | "Can we fulfill order X?" → trace through inventory + routing rules |
| **Legal Document Review** | NLP extracts clauses, entities, obligations | Both | Forward: flag all risks. Backward: "Does clause X conflict with regulation Y?" |
| **Autonomous Safety** | Vision model detects objects, pedestrians, signals | Forward | Safety rules fire: stop, slow, yield — deterministic, traceable, auditable |

### 7.5 The Trace Is the Product

In every use case above, the decision alone is not enough. Stakeholders need to know **why**:

- A regulator asks: "Why was this loan denied?" → backward chaining proof tree
- A doctor asks: "What triggered the emergency escalation?" → forward chaining trace
- An auditor asks: "Does this transaction comply with FCRA?" → backward chaining proof tree
- An engineer asks: "Why did the safety system brake?" → forward chaining trace

This is why Sigil treats traces as fundamental output, not debugging. The chaining strategy determines the **shape** of the trace:

```
Forward chaining trace (what happened):
  RULE credit_check → FIRED (priority 10)
    EVAL credit_score >= 680 → true [720]
    ACTION credit_eligible = true
  RULE income_check → FIRED (priority 10)
    EVAL income >= 50000 → true [85000]
    ACTION income_eligible = true
  RULE final_decision → FIRED (priority 5)
    EVAL credit_eligible AND income_eligible → true
    ACTION loan_approved = true

Backward chaining trace (why it's true):
  GOAL loan_approved
    └── RULE final_decision
        ├── SUBGOAL credit_eligible
        │   └── RULE credit_check
        │       └── FACT credit_score = 720 >= 680 ✓
        └── SUBGOAL income_eligible
            └── RULE income_check
                └── FACT income = 85000 >= 50000 ✓
    PROVED: loan_approved = true
```

Both traces describe the same decision. Forward chaining answers "what happened." Backward chaining answers "why."

### 7.6 Where This Puts Sigil

Sigil is a **neuro-symbolic programming language** — the interface between the neural and symbolic layers. Chaining is not an add-on feature. It is the core of what Sigil's interpreter does:

```
     The Full Neuro-Symbolic Pipeline (Sigil's Architecture)

     Natural Language
           │
           ▼
     [Neural Parser]        ← LLM converts NL to .sigil (Phase 4)
           │
           ▼
     .sigil source code     ← Human-readable, versionable, auditable
           │
           ▼
     [Lexer → Parser → Type Checker]   ← Compilation pipeline (PEG-based)
           │
           ▼
     [Interpreter]
       ├── Forward Chaining   ← "evaluate all rules" — derive conclusions
       ├── Backward Chaining  ← "query goal" — prove specific claims
       └── Trace Logger       ← Every step recorded
           │
           ▼
     Decision + Trace + Explanation   ← The output
```

Every neuro-symbolic use case — triage, lending, fraud, compliance, agents — maps onto this pipeline. The neural layer handles the messy perception. Sigil's chaining engine handles the deterministic reasoning. The trace proves it.

---

## 8. Historical Context (Updated)

| System | Year | Chaining | Notable For |
|--------|------|----------|-------------|
| **CLIPS** | 1985 | Forward | NASA's expert system tool |
| **Prolog** | 1972 | Backward | Logic programming language |
| **Drools** | 2001 | Forward (Rete) | Java business rules engine |
| **OPS5** | 1977 | Forward | First production system language |
| **Sigil** | 2026 | Both | Neuro-symbolic with NL syntax |

Prolog is purely backward chaining — every query works top-down. CLIPS is purely forward chaining — facts drive conclusions. Modern systems (including Sigil) support both because they answer different questions.

---

## 9. Key Takeaways

1. **Forward and backward chaining are NOT compiler concepts.** They are runtime reasoning strategies used by rule engines and AI systems.
2. **Forward chaining** = data-driven: "I have facts, what can I conclude?" → Sigil's `evaluate all rules`
3. **Backward chaining** = goal-driven: "I want to prove X, what do I need?" → Sigil's `query`
4. **They're complementary**, not competing. Real systems use both.
5. **They are the symbolic half of neuro-symbolic AI.** Neural layers perceive. Chaining decides. The boundary is explicit.
6. **The trace output is different**: forward chaining traces show "what fired and in what order." Backward chaining traces show "why this is true" (proof tree).
7. **In regulated domains, the trace is the product.** The decision is a side effect. Chaining produces the structured proof that auditors, regulators, and engineers need.
8. **Where they live in Sigil's pipeline**: entirely in the interpreter/evaluator, after parsing and type checking are already done.

```
Lexer → Parser → Type Checker → Interpreter
                                     │
                                     ├── Forward Chaining (evaluate all rules)
                                     └── Backward Chaining (query goal)
```

---

## References

- Russell, S. & Norvig, P. *Artificial Intelligence: A Modern Approach* — Chapter 9 (Inference in First-Order Logic)
- `src/sigil/interpreter/evaluator.py` — Sigil's forward chaining implementation
- `src/sigil/interpreter/backward.py` — Sigil's backward chaining implementation
