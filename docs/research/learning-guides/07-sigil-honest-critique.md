# A Brutally Honest Critique of Sigil

> Does the world need Sigil? The short answer: not yet, and maybe not ever — unless sharp strategic choices are made now.

---

## 1. The Identity Crisis Problem

Sigil tries to be three things simultaneously:

- A **programming language** for neuro-symbolic AI
- A **rule engine** for deterministic business decisions
- An **LLM target language** that AI generates

No successful language has won by serving three masters. PL/I tried to serve both FORTRAN and COBOL users — both rejected it. Sigil risks the same: too weird for Python developers, too limited for Prolog/Lean researchers, too unfamiliar for business analysts who use visual rule builders.

**Who is the user?** This hasn't been answered concretely:

| Potential User | What They Use Instead | Why They Won't Switch |
|---|---|---|
| Data scientist | DSPy (28K GitHub stars, 160K monthly pip downloads) | Already works in Python, no new language needed |
| Compliance officer | Visual rule builder (GoRules, Nected) | Doesn't want to write code at all |
| Language researcher | Scallop (differentiable Datalog, PLDI 2023) | Published, peer-reviewed, PyTorch integration |
| Enterprise architect | Drools (decades of trust, now integrating LLMs via LangChain4j) | Battle-tested, Java ecosystem, huge community |
| ML engineer | Instructor (3M+ pip/month) + Pydantic | 5 lines of Python does what `neural` does |

---

## 2. The Chicken-and-Egg Problem (Fatal)

Sigil's core vision: *"LLMs generate Sigil code."* But:

- LLMs need training data to generate Sigil.
- There is no Sigil training data (25 example files, ~1,100 lines total).
- Without LLM support, developers won't adopt Sigil.
- Without developers, there's no training data.

This is the **single biggest existential risk**. Every other new language (Go, Rust, Swift, Mojo) was adopted by humans first, then LLMs learned it from human-written code. Sigil's vision *requires* LLMs to write it, but LLMs *can't* write it yet. Designing a car that needs roads that don't exist.

Research confirms: "LLMs hallucinate random tokens for uncommon DSLs" (IEEE Spectrum 2025). With ~1,100 lines of examples, Claude/GPT will confidently generate Sigil-*looking* code that doesn't parse.

---

## 3. The "Just Use Python" Problem

Everything Sigil does today can be done in Python:

| Sigil Feature | Python Equivalent |
|---|---|
| `neural classify from text:` | `client.chat(model="gpt-4o", response_model=Classification)` (Instructor, 3M+ monthly downloads) |
| `rule X with priority 10: when...then...` | Drools, Venmo `business-rules`, or 50 lines of Python |
| `explain "reason"` | A comment string in a dict |
| `--trace` | Python logging / OpenTelemetry |
| `import python math` | `import math` (why add a layer?) |
| `confidence_threshold 0.85` | `if result.confidence < 0.85: fallback()` |

The uncomfortable truth: **Sigil's `import python math` is strictly worse than `import math`**. It adds marshaling overhead, another abstraction layer, and another failure mode — for zero benefit.

Structured output from LLMs is now a *native feature* of OpenAI/Anthropic APIs (100% JSON schema compliance). Pydantic + Instructor handles the "neural boundary" in 5 lines of Python. A keyword isn't needed for this.

---

## 4. The Performance Story Is Weak

The roadmap promises `<1ms rule evaluation via Rust core`. Current benchmarks show:

- Pattern matching: ~2.4x speedup (Rust vs Python) — but only at 50+ rules
- Constraint solving: **Python-to-Rust marshaling overhead dominates at small scale**
- Trace serialization: ~1.3x speedup

A 2.4x speedup is not a compelling reason to learn a new language:

| System | Performance | Maturity |
|---|---|---|
| Drools (JVM) | Millions of rules/second | 20+ years production |
| OPA/Rego | Microsecond policy evaluation | Netflix (1M+ decisions/day) |
| GoRules (Rust-native) | Millisecond startup, native perf | Modern, cross-platform |
| Sigil Rust core | 2.4x over Python, alpha-nodes only | No beta-node joins, Rete-lite |

Sigil's Rust core, which is a Rete-*lite* with alpha nodes only (no beta-node joins), is a toy compared to these production systems.

---

## 5. The Constrained NL Syntax Is a Trap

Sigil reads like English:

```sigil
when sensor temperature exceeds 100 degrees
and sensor status is :active
then trigger alert with severity :critical
```

This looks great in demos. But constrained NL has a long history of failure:

- **AppleScript** (1993): English-like syntax that "creates the illusion of flexibility while being rigidly constrained." Universally disliked by developers.
- **COBOL**: Readable, yes. But verbosity becomes a liability at scale.
- **Inform 7**: Succeeded, but only in the niche of interactive fiction.

The problem: when users encounter the *edge* of the constrained NL, they hit a wall. Can I write `when temperature is above 100`? No, it's `exceeds`. Can I write `if temperature > 100`? Maybe, but now paradigms are mixing. The syntax creates **false familiarity** — users assume they can write English, then get parse errors from a PEG grammar they don't understand.

The parser is 1,499 lines. The evaluator is 1,444 lines. These are growing. Every new feature makes the "constrained" part harder to maintain. 8 grammar gaps were found in Phase 1 alone.

---

## 6. The Competitive Landscape Has Moved

While Sigil was being built (March 2026), the market moved:

| Competitor | Traction | What They Do | Why Sigil Loses |
|---|---|---|---|
| **DSPy** | 28K stars, 160K pip/month | Programming — not prompting — LLMs | Solves LLM orchestration in Python |
| **BAML** | Growing fast | DSL for AI functions with type-safe output | Ships to Python/TS/Go/Rust/Java/C# |
| **Instructor** | 11K stars, 3M pip/month | Structured LLM output with Pydantic | Does `neural` keyword's job in 5 lines |
| **Guardrails AI** | $7.5M funded, $1.1M revenue | LLM output validation | Commercially validated, growing |
| **Drools + LLM** | Decades of enterprise trust | Rule engine + LangChain4j integration | Already deployed, Java ecosystem |
| **OPA/Rego** | 68% enterprise adoption | Policy as code | Proven at Netflix scale |
| **Scallop** | 657 stars, PLDI paper | Differentiable neuro-symbolic Datalog | Published, peer-reviewed, differentiable |

None of these required users to learn a new language. They all work *within* existing ecosystems.

---

## 7. The Vision Doc Promises Things That Don't Exist

The VISION.md paints a beautiful picture:

> *"A domain expert describes a decision process in natural language → LLM translates → Sigil program is type-checked → executes deterministically → every decision is auditable."*

Current reality:

- No NL-to-Sigil translator exists (Phase 4, not started)
- No CI pipeline (noted as "NOT YET CREATED")
- No PyPI package
- No user documentation beyond developer docs
- No community (zero external users)
- 807 tests but zero production deployments

An impressive *compiler project* has been built. A *product* has not.

---

## 8. Language Adoption Research: The Evidence

Research from UC Berkeley (Meyerovich, OOPSLA 2013) found that **intrinsic language features have only secondary importance in adoption**. Open source libraries, existing code, and developer experience are the primary drivers.

### Why Languages Fail

1. **The Haskell Problem (Complexity Barrier):** Technically excellent, steep learning curve, no corporate sponsor. "The language everybody wished they could program in, but nobody did."

2. **The Elm Problem (BDFL Governance):** No updates since 0.19.1 (October 2019). Community contributions blocked. Core team left to create forks.

3. **The PL/I Problem (Identity Crisis):** Tried to serve FORTRAN and COBOL users. Both rejected it.

4. **The Smalltalk Problem (Ecosystem Isolation):** Technically brilliant, failed on interoperability. Java won because of seamless interop, not better design.

5. **The AI Training Data Problem (2025-specific):** Without a critical mass of code in the wild, LLMs cannot help developers write in your language — now a **hard requirement** for adoption (IEEE Spectrum 2025).

### What Makes Languages Succeed

| Language | Why It Worked |
|---|---|
| Go | Google backing, solved real problems (concurrency), extreme simplicity |
| Rust | Mozilla backing, fearless concurrency narrative, exceptional tooling (Cargo), passionate community |
| Swift | Apple mandate for iOS (captive audience), progressive disclosure |
| Mojo | Python superset ("not having to retrain hundreds of millions of Python developers is a huge feature") |

**Key lesson:** Every successful new language had either (a) a corporate backer with a captive audience, (b) a 10x performance story in a specific domain, or (c) compatibility with an existing ecosystem. Pure technical merit is never sufficient.

Sigil has none of these.

---

## 9. What Sigil Gets RIGHT

To be fair, Sigil has genuine strengths:

### Traces as First-Class Output
This is genuinely novel. No other rule engine or LLM framework treats traces as fundamental output (not debug). In regulated industries (finance, healthcare, compliance), the trace IS the output. The decision is a side effect.

### The `neural` Keyword as Explicit Boundary
The idea of marking non-determinism at the language level is elegant and maps directly to what AlphaGeometry/AlphaProof do architecturally. This is a real design insight that no competitor has replicated at the language level.

### Solid Engineering
807 tests, clean mypy, ruff passing, frozen dataclasses, hand-written recursive descent parser, 6 neural backends, Rust core via PyO3. The code quality is high.

### 6 Neural Backends
hf:, claude:, openai:, onnx:, python:, mock: — this is practical, well-designed, and more complete than most comparable projects.

### The Right Thesis at the Right Time
Amazon is investing in neuro-symbolic AI. The BRMS market is $2B+ and growing at 12.1% CAGR. The research community agrees neural+symbolic is the future. The timing is right — the vehicle might be wrong.

---

## 10. The Rule Engine Market: Is There Demand?

**Yes.** The Business Rules Management Systems (BRMS) market:
- **$1.82 billion in 2025**, projected to reach **$5.71 billion by 2035** (12.1% CAGR)
- 75%+ of large enterprises use rule engines in core business applications
- 58% of new BRMS have AI capabilities

But the trend is toward **JSON/YAML rules + visual editors + polyglot engines**, not new programming languages. GoRules (Rust engine + visual editor + JSON rules) represents the modern approach. Venmo's `business-rules` library does rules-as-JSON in Python.

The market wants *rule evaluation as a service*, not *rule evaluation as a language*.

---

## 11. The Neuro-Symbolic Thesis: Validated or Not?

### Evidence FOR

- **Amazon production deployments**: Vulcan warehouse robots (neural vision + symbolic safety constraints), Rufus shopping assistant (neuro-symbolic to reduce hallucinations)
- **AWS investment**: "Dedicated infrastructure, tools, and research initiatives to scale hybrid systems" (SiliconANGLE, July 2025)
- **PNAS Nexus 2025**: Neurosymbolic AI as "antithesis to scaling laws" — symbolic reasoning enables networks to outperform models 100x their size using 1% of the data
- **AlphaProof/AlphaGeometry**: Proved neuro-symbolic can achieve superhuman reasoning

### Evidence AGAINST

- Most neuro-symbolic systems are **bespoke** (custom-built for specific applications), not general-purpose
- No standard framework has won (Scallop: 657 stars)
- Integration overhead is real — maintaining two paradigms is harder than one
- Pure LLM approaches keep getting better (o1/o3 chain-of-thought reasoning)
- IBM Watson recommended "unsafe and incorrect" cancer treatments — the architecture was right, the knowledge was wrong
- Explainability and trustworthiness are represented in only 28% of neuro-symbolic research

**Verdict**: The thesis is validated in principle but not yet proven at scale as a *general-purpose* approach.

---

## 12. Strategic Options

### Option A: Pivot to a Python Library (Lowest Risk, Highest Adoption)

Kill the language. Ship a Python library called `sigil` that provides:

```python
from sigil import rule, neural, RuleEngine, trace

@neural(model="claude:claude-sonnet-4-20250514", confidence=0.85, fallback="unknown")
def classify_intent(text: str) -> str: ...

@rule(priority=10, explain="Positive review auto-approved")
def auto_approve(classification: str, channel: str) -> dict:
    if classification == "positive" and channel == "reviews":
        return {"action": "approve"}

engine = RuleEngine([auto_approve, flag_negative, unknown_hold])
result = engine.evaluate({"classification": classify_intent(text), "channel": "reviews"})
print(result.trace)  # Full auditable trace
```

**Gains**: Zero adoption barrier (`pip install sigil`), LLM support for free (it's Python), access to entire ecosystem without marshaling, same conceptual model.

**Loses**: Constrained NL syntax, the "it's a real language" narrative.

### Option B: Double Down on the Language (High Risk, High Reward)

If the language is essential, these are non-negotiable:

1. **Pick ONE user persona** — compliance officers? ML engineers? Who?
2. **Build NL-to-Sigil TODAY** — not Phase 4. Without this, the core vision is vapor.
3. **Ship to PyPI** — installable in one command or it doesn't exist.
4. **Generate 10K+ lines of synthetic Sigil** — fine-tune a model to generate Sigil code.
5. **Build ONE killer demo** — a real-world compliance/triage system that makes jaws drop.
6. **Find a design partner** — one company that will use Sigil in production.
7. **Publish a paper** — position Sigil in the academic neuro-symbolic space (NeSy, PLDI, OOPSLA).

### Option C: Become a Research Vehicle (Lowest Risk, Lowest Impact)

Position Sigil as a research contribution to the neuro-symbolic programming languages space. Compare against Scallop. Target NeSy, PLDI, or OOPSLA. Publish a paper. This validates the ideas without requiring commercial adoption.

---

## 13. The Bottom Line

**Sigil is a well-engineered solution searching for a problem that the market is already solving in Python.**

The thesis (neural + symbolic + auditable) is correct. The execution as a *new programming language* is the wrong vehicle. The constrained NL syntax is a demo strength and an adoption weakness. The chicken-and-egg problem with LLM generation is potentially fatal.

The world needs what Sigil *represents* — explicit neural/symbolic boundaries with mandatory traces. The world probably doesn't need it as a separate language.

The autoformalization/Lean research reinforces this: Lean succeeded because it had a captive audience (mathematicians who NEED formal proofs), corporate backing (Microsoft, then Simons/Sloan Foundation), and a killer app (Mathlib with 250K+ theorems). Sigil has none of these yet.

The hardest question isn't "is Sigil technically good?" (it is). It's **"why would anyone choose to learn Sigil instead of writing Python?"**

Until that question has a compelling answer that can be stated in one sentence, Sigil remains an impressive compiler project, not a product.

---

## Sources

- [Scallop: A Language for Neurosymbolic Programming (PLDI 2023)](https://arxiv.org/abs/2304.04812)
- [Drools + LLM Integration (Quarkus)](https://github.com/mariofusco/quarkus-drools-llm)
- [OPA vs Cedar vs Zanzibar (2025)](https://www.osohq.com/learn/opa-vs-cedar-vs-zanzibar)
- [DSPy Framework](https://dspy.ai/) — 28K stars, 160K monthly pip downloads
- [BAML (BoundaryML)](https://boundaryml.com/)
- [Guardrails AI](https://guardrailsai.com/) — $7.5M seed, $1.1M revenue
- [Instructor Library](https://python.useinstructor.com/) — 11K stars, 3M+ monthly downloads
- [BRMS Market Report](https://www.marketgrowthreports.com/market-reports/business-rules-management-systems-brms-market-105612) — $1.82B in 2025
- [GoRules (Rust Rule Engine)](https://gorules.io/)
- [IEEE Spectrum Top Programming Languages 2025](https://spectrum.ieee.org/top-programming-languages-2025)
- [Empirical Analysis of Programming Language Adoption (OOPSLA 2013)](https://lmeyerov.github.io/projects/socioplt/papers/oopsla2013.pdf)
- [What Killed Haskell, Could Kill Rust Too](https://gist.github.com/graninas/22ab535d2913311e47a742c70f1d2f2b)
- [Amazon Vulcan Robots — Neuro-Symbolic Production Deployment](https://www.amazon.science/blog/how-amazons-vulcan-robots-use-touch-to-plan-and-execute-motions)
- [AWS Neuro-Symbolic AI Investment (SiliconANGLE 2025)](https://siliconangle.com/2025/07/17/aws-invests-neuro-symbolic-ai-smarter-safer-intelligence-aicloudleaders/)
- [Neurosymbolic AI as Antithesis to Scaling Laws (PNAS Nexus 2025)](https://academic.oup.com/pnasnexus/article/4/5/pgaf117/8134151)
- [DSL Generation with LLMs](https://medium.com/itemis/large-language-models-for-domain-specific-language-generation-how-to-train-your-dragon-0b5360e8ed76)
- [SWE-bench+ Analysis (60% Solution Leakage)](https://openreview.net/forum?id=R40rS2afQ3)
- [IBM rule-based-llms](https://github.com/DecisionsDev/rule-based-llms)
- [Mojo Adoption Challenges](https://newsletter.pragmaticengineer.com/p/from-swift-to-mojo-and-high-performance)
