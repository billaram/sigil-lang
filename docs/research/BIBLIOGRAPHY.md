# Sigil: Complete Research Bibliography

All papers, books, projects, and resources referenced in Sigil's research and design.

---

## Neuro-Symbolic AI

1. **Garcez, A.d., et al. (2017)**. "Neural-Symbolic Learning and Reasoning: A Survey and Interpretation." *arXiv:1711.03902*. 58-page survey by 14 researchers establishing the field's taxonomy.

2. **Kautz, H. (2020)**. "The Third AI Summer." *AAAI Presidential Address*. Introduced the six-type taxonomy of neuro-symbolic integration.

3. **Launchbury, J. (2017)**. "A DARPA Perspective on Artificial Intelligence." *DARPA*. The Three Waves framework: handcrafted knowledge → statistical learning → contextual adaptation.

4. **Reed, S. & de Freitas, N. (2016)**. "Neural Programmer-Interpreters." *ICLR (Best Paper)*. Neural networks learning to invoke programs rather than be the executor.

5. **Wei, J., et al. (2022)**. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS*. Evidence that externalizing symbolic intermediate steps improves neural reasoning.

6. **Trinh, T.H., et al. (2024)**. "Solving Olympiad Geometry without Human Demonstrations." *Nature*. AlphaGeometry: neural intuition + symbolic deduction.

7. **AlphaProof (2024)**. "AI achieves silver-medal standard solving International Mathematical Olympiad problems." *Google DeepMind Blog*. Gemini + AlphaZero + Lean 4.

8. **Li, Z., et al. (2023)**. "Scallop: A Language for Neurosymbolic Programming." *PLDI*. Purpose-built NeSy DSL with provenance semirings.

9. **Manhaeve, R., et al. (2018)**. "DeepProbLog: Neural Probabilistic Logic Programming." *NeurIPS*. Pioneered differentiable logic programming with neural predicates.

10. **SymCode (2025)**. "Neurosymbolic framework for verifiable code generation." *arXiv:2510.25975*. Up to 13.6pp accuracy improvement via symbolic verification.

11. **AgenticDomiKnowS (2026)**. "Agentic framework for neuro-symbolic programming." *arXiv:2601.00743*. NL-driven NeSy program creation.

12. **Ellis, K., et al. (2021)**. "DreamCoder: Learning to Code by Writing Programs." *PLDI*. Incremental DSL learning via wake-sleep algorithm.

13. **Systematic Review of Neuro-Symbolic AI (2025)**. *arXiv:2501.05435*. Survey of 167 qualifying papers across five research areas.

14. **Comparative Survey of NeSy Frameworks (2025)**. *arXiv:2509.07122*. Empirical comparison of NeSy frameworks.

15. **Evans, R. & Grefenstette, E. (2018)**. "Learning Explanatory Rules through Neural Satisfaction." *JAIR*. Differentiable inductive logic programming.

16. **Fedus, W., et al. (2021)**. "Switch Transformers: Scaling to Trillion Parameter Models." *JMLR*. Conditional computation via mixture of experts.

17. **Guu, K., et al. (2020)**. "REALM: Retrieval-Augmented Language Model Pre-Training." *ICML*. Knowledge grounding via retrieval.

18. **Neurosymbolic Programming: Pitfalls and Opportunities (2025)**. Velingker, N., et al. University of Pennsylvania. Key finding: authoring NeSy programs remains challenging.

19. **Active Learning for Neurosymbolic Program Synthesis (2025)**. *POPL*. Semi-automatic NeSy program construction via targeted queries.

---

## Reasoning and LLM Limitations

20. **Dziri, N., et al. (2023)**. "Faith and Fate: Limits of Transformers on Compositionality and Reasoning." *NeurIPS*. Shows accuracy degrades exponentially with reasoning steps.

21. **Valmeekam, K., et al. (2023)**. "On the Planning Abilities of Large Language Models." *NeurIPS*. LLMs fail at classical planning even with CoT.

---

## Programming Languages and Compilers

22. **Ford, B. (2004)**. "Parsing Expression Grammars: A Recognition-Based Syntactic Foundation." *POPL*. Foundational PEG paper.

23. **Nystrom, R. (2021)**. *Crafting Interpreters*. Genever Benning. Complete tree-walking → bytecode VM implementation guide.

24. **MoonBit Team (2024)**. "MoonBit: An AI-Friendly Programming Language." *LLM4Code Workshop at ICSE*. First AI-native language design.

25. **SimPy (2024)**. "AI Coders Are Among Us: Rethinking Programming Language Grammar Towards Efficient Code Generation." *arXiv:2404.16333*. Grammar design impacts LLM codegen efficiency.

26. **LMQL (2023)**. "Prompting Is Programming: A Query Language for Large Language Models." LLM interaction with constrained decoding.

27. **SudoLang (2023)**. Pseudocode language for LLM interaction. Medium article by Eric Elliott.

28. **Grammar-Constrained Decoding (2025)**. *ACL Findings*. Formal grammars as LLM output constraints.

29. **GPeg (2021)**. "Incremental PEG Parsing." *SLE*. Logarithmic-time incremental reparsing.

30. **DuckDB Runtime-Extensible PEG Parsers (2024/2025)**. *CIDR*. PEGs extended at runtime.

31. **Tree-sitter**. Incremental parsing library used by Neovim, Helix, Zed, GitHub.

32. **LLVM**. Compiler infrastructure. https://llvm.org

33. **Move on LLVM (2023)**. Brson. Practical experience writing an LLVM backend in Rust.

---

## LISP and Functional Programming

34. **McCarthy, J. (1960)**. "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I." *Communications of the ACM*. Original LISP paper.

35. **LLMs in LISP Metaprogramming (2025)**. *arXiv:2506.10021*. Persistent metaprogramming loops with LLMs and Common Lisp.

36. **dialectical-symbolic-ai (2025)**. GitHub project combining DSPy + SBCL for knowledge extraction.

37. **Lean 4**. *Mathematics in Lean*. https://leanprover-community.github.io. Won 2025 ACM SIGPLAN PL Software Award.

38. **Wadler, P. (2015)**. "Propositions as Types." *Communications of the ACM*. Curry-Howard correspondence.

---

## Natural Language Programming

39. **Nelson, G. (2006)**. *Inform 7*. http://inform7.com. Constrained NL programming for interactive fiction.

40. **Wolfram, S. (2010)**. "Programming with Natural Language Is Actually Going to Work." *Stephen Wolfram Blog*. NL as input layer to symbolic computation.

41. **AppleScript (1993)**. Apple Inc. English-like syntax for macOS automation. Lessons in NL syntax pitfalls.

---

## Language Interoperability

42. **Clojure**. "Clojure: JVM Hosted." https://clojure.org/about/jvm_hosted. Hosted language interop design.

43. **Zig**. "In-depth Overview: C Interop." https://ziglang.org/learn/overview/. Zero-cost C FFI via embedded Clang.

44. **PyO3**. "Rust Bindings for Python." https://pyo3.rs. Rust↔Python binding framework.

45. **maturin**. Build and publish Rust crates as Python packages. https://www.maturin.rs

46. **Project Panama (JDK 22, 2024)**. Foreign Function & Memory API. 4-5x faster than JNI.

47. **UniFFI (Mozilla)**. Generate multi-language FFI bindings from Rust. https://mozilla.github.io/uniffi-rs/

---

## Industry and Applied Systems

48. **Zest AI**. ML + symbolic compliance for lending decisions. https://www.zest.ai

49. **Featurespace ARIC**. Adaptive behavioral analytics for financial crime detection.

50. **ComplyAdvantage**. AI-powered financial compliance and risk data.

51. **Isabel Healthcare**. Clinical decision support using symbolic reasoning.

52. **Ahn, Y.-Y., et al. (2011)**. "Flavor Network and the Principles of Food Pairing." *Scientific Reports*. Network science applied to ingredient pairing.

---

## Regulatory and Standards References

53. **FinCEN BSA/AML**. Bank Secrecy Act / Anti-Money Laundering regulations.
54. **FATF Risk-Based Approach**. Financial Action Task Force guidance on AML.
55. **CFPB Adverse Action Notices**. Consumer Financial Protection Bureau lending regulations.
56. **ESI (Emergency Severity Index) v4**. Triage protocol for emergency departments.
57. **HIPAA**. Health Insurance Portability and Accountability Act.
58. **EMTALA**. Emergency Medical Treatment and Labor Act.
59. **OFAC SDN**. Office of Foreign Assets Control Specially Designated Nationals list.

---

## Workshops and Venues

60. **NeSy (Neural-Symbolic Learning and Reasoning)**. Annual workshop series.
61. **NSE 2026 (Neuro-Symbolic Software Engineering)**. 2nd International Workshop at ICSE 2026, April 12, 2026.
62. **LLM4Code 2024**. Workshop at ICSE on LLMs for code.

---

## Books

63. **Russell, S. & Norvig, P.** *Artificial Intelligence: A Modern Approach*. Chapter 6: Constraint Satisfaction Problems.
64. **Rossi, F., van Beek, P., & Walsh, T.** *Handbook of Constraint Programming*. Comprehensive CSP reference.
65. **Nystrom, R. (2021)**. *Crafting Interpreters*. Genever Benning. Complete language implementation guide.
