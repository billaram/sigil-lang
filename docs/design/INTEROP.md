# Sigil: Interoperability Design

## Philosophy

Sigil follows the **"hosted language"** pattern — like Clojure on the JVM or Zig with C. It is not an island. It anchors to Python for the ML/AI ecosystem and Rust for performance-critical symbolic execution.

The interop is not an afterthought; it is a core language feature. Sigil programs should seamlessly call Python libraries and Rust functions as if they were native Sigil operations.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   SIGIL PROGRAM                      │
│                                                     │
│  ┌─────────────────┐   ┌─────────────────────────┐  │
│  │  Symbolic Rules  │   │   Neural Declarations   │  │
│  │  (pure Sigil)    │   │   (Sigil + backends)    │  │
│  └────────┬────────┘   └──────────┬──────────────┘  │
│           │                       │                  │
│           ▼                       ▼                  │
│  ┌─────────────────────────────────────────────────┐ │
│  │              FFI BOUNDARY LAYER                  │ │
│  │                                                  │ │
│  │  ┌──────────────┐       ┌───────────────────┐   │ │
│  │  │  Type Marshal │       │  Error Transform  │   │ │
│  │  │  (Sigil↔Host) │       │  (Host→Sigil)     │   │ │
│  │  └──────────────┘       └───────────────────┘   │ │
│  └─────────┬─────────────────────┬─────────────────┘ │
│            │                     │                    │
└────────────┼─────────────────────┼────────────────────┘
             │                     │
    ┌────────▼────────┐   ┌───────▼─────────┐
    │  Python Runtime  │   │   Rust Core     │
    │                  │   │  (via PyO3)     │
    │  - torch         │   │                 │
    │  - transformers   │   │  - solver       │
    │  - pandas         │   │  - matcher      │
    │  - numpy          │   │  - constraint   │
    │  - scikit-learn   │   │  - trace_opt    │
    │  - any pip pkg    │   │  - bytecode_vm  │
    └──────────────────┘   └─────────────────┘
```

## Python FFI

### Why Python

- **The ML ecosystem lives in Python**: PyTorch, TensorFlow, HuggingFace, scikit-learn, pandas, numpy
- **Sigil's interpreter runs on Python**: FFI is zero-overhead for dynamic dispatch
- **Largest package ecosystem**: 500K+ packages on PyPI
- **Domain expert familiarity**: Data scientists and ML engineers already know Python

### Usage Patterns

#### Direct Import
```sigil
import python pandas as pd
import python numpy as np
import python torch

-- Use Python objects directly
define df as pd.read_csv("data.csv")
define tensor as torch.tensor([1.0, 2.0, 3.0])
```

#### Selective Import
```sigil
from python sklearn.ensemble import RandomForestClassifier
from python transformers import pipeline

define classifier as RandomForestClassifier(n_estimators: 100)
define summarizer as pipeline("summarization")
```

#### Python Function Wrapping
```sigil
-- Wrap a Python function with Sigil types
define predict_risk as python function:
  from risk_model import predict
  accepts applicant: Record
  returns Confidence

-- Now use it in rules
rule risk_assessment:
  given risk as predict_risk(applicant)
  when risk exceeds 0.8
  then flag_for_review
```

#### Inline Python (escape hatch)
```sigil
-- For complex Python operations
define processed_data as python:
  import pandas as pd
  df = pd.read_csv("data.csv")
  df = df.dropna().reset_index(drop=True)
  return df[df['status'] == 'active']
```

### Type Marshaling (Python ↔ Sigil)

| Sigil Type | Python Type | Notes |
|-----------|------------|-------|
| Number | int / float | Automatic promotion |
| Text | str | UTF-8 |
| Boolean | bool | Direct |
| Symbol | str (prefixed) | `:active` → `"active"` |
| List[T] | list | Element-wise conversion |
| Record{...} | dict / dataclass | Key-value mapping |
| Option[T] | Optional[T] | None handling |
| Confidence | float | Range-checked 0.0-1.0 |
| Unit(N, U) | float | Unit stripped at boundary |
| Trace | SigilTrace | Custom class |

### Error Handling at Boundary

```sigil
-- Python exceptions become Sigil errors
define result as try python:
  import requests
  response = requests.get("https://api.example.com/data")
  return response.json()
on error:
  fallback to default_data
  trace warning "Python API call failed: {error}"
```

## Neural Bridge (Multi-Backend)

The `neural` keyword is the only way to introduce non-determinism in Sigil. Neural declarations invoke ML models through a pluggable backend system.

### Architecture

```
ModelRegistry
  ├── "hf:"      → HuggingFaceBackend     (classification, zero-shot)
  ├── "claude:"  → AnthropicBackend        (Claude API — generation, structured output)
  ├── "openai:"  → OpenAIBackend           (GPT API — generation, structured output)
  ├── "onnx:"    → ONNXBackend             (ONNX Runtime — fast local inference)
  ├── "python:"  → PythonCallableBackend   (any Python function)
  └── "mock:"    → MockBackend             (deterministic testing)
```

All backends implement `ModelBackend.predict(model_id, input_data, config) → ModelResult`. The registry routes by model ID prefix. All ML dependencies are optional — missing backends return the `fallback` value.

### NeuralConfig Parameters

Every neural declaration's fields are extracted into a `NeuralConfig` frozen dataclass:

| Parameter | Type | Default | Used By |
|-----------|------|---------|---------|
| `model` | Text | (required) | All |
| `returns` | TypeRef | (required) | All |
| `confidence_threshold` | Number | 0.5 | All |
| `fallback` | Value | (required) | All |
| `labels` | List[Symbol] | None | HuggingFace (triggers zero-shot) |
| `hypothesis` | Text | None | HuggingFace (zero-shot template) |
| `system_prompt` | Text | None | Claude, OpenAI |
| `temperature` | Number | None | Claude, OpenAI |
| `max_tokens` | Number | None | Claude, OpenAI |
| `top_p` | Number | None | Claude, OpenAI |
| `top_k` | Number | None | Claude |
| `stop_sequences` | List[Text] | None | Claude, OpenAI |
| `output_schema` | Text | None | Claude, OpenAI |
| `num_candidates` | Number | 1 | All |
| `beam_size` | Number | None | HuggingFace |
| `timeout` | Number | 60 | All (enforced in registry via threading) |

The parser requires **zero changes** for new fields — `_parse_neural_field()` already accepts any IDENTIFIER followed by an expression.

### Backend Examples

```sigil
-- Zero-shot classification (HuggingFace)
neural classify_topic from text: Text:
  model "hf:facebook/bart-large-mnli"
  returns Symbol
  labels [:triangle, :rectangle, :circle]
  confidence_threshold 0.7
  fallback to :unknown

-- LLM structured output (Claude)
neural suggest_strategy from problem: Text:
  model "claude:claude-sonnet-4-20250514"
  returns Symbol
  system_prompt "You are a math expert. Respond with one word."
  temperature 0.0
  max_tokens 10
  confidence_threshold 0.5
  fallback to :unknown

-- Custom Python function
neural predict_risk from features: Record:
  model "python:risk_model.predict"
  returns Number
  confidence_threshold 0.6
  fallback to 0.5

-- Deterministic testing
neural classify from text: Text:
  model "mock:fixed:positive"
  returns Symbol
  confidence_threshold 0.5
  fallback to :unknown
```

### Fallback Cascade

Every neural call follows this sequence:
1. Look up backend by model ID prefix
2. Call `backend.predict()` with timeout enforcement
3. If confidence >= threshold → return model result
4. If confidence < threshold → return fallback value
5. If error (timeout, API failure, missing SDK) → return fallback value
6. Always record `NeuralTrace` for auditability

### Dependencies

```toml
[project.optional-dependencies]
hf = ["transformers>=4.30", "torch>=2.0"]
claude = ["anthropic>=0.40"]
openai = ["openai>=1.0"]
onnx = ["onnxruntime>=1.16"]
all = ["sigil-lang[hf,claude,openai,onnx,dev]"]
```

Python callable and mock backends have no dependencies (always available).

## Rust FFI

### Why Rust

- **Performance**: Symbolic execution at <1ms requires native speed
- **Memory safety**: No segfaults in the rule engine
- **WASM target**: Rust compiles to WebAssembly for browser deployment
- **C/C++ interop**: Rust calls C libraries, giving Sigil indirect access to BLAS, LAPACK, etc.
- **Concurrency**: Rust's ownership model enables safe parallel rule evaluation

### The sigil_core Crate

The Rust core (`src/sigil_core/`) provides performance-critical components:

```rust
// src/sigil_core/src/lib.rs
use pyo3::prelude::*;

/// High-performance constraint solver
#[pyfunction]
fn solve_constraints(constraints: Vec<Constraint>, facts: HashMap<String, Value>) -> PyResult<Solution> {
    // Rust implementation: ~100x faster than Python equivalent
    let solver = ConstraintSolver::new();
    solver.solve(&constraints, &facts)
}

/// Pattern matcher using Rete algorithm
#[pyfunction]
fn match_rules(rules: Vec<Rule>, facts: HashMap<String, Value>) -> PyResult<Vec<Match>> {
    let rete = ReteNetwork::compile(&rules);
    rete.match_facts(&facts)
}

/// Optimized trace serialization
#[pyfunction]
fn serialize_trace(trace: &Trace) -> PyResult<Vec<u8>> {
    bincode::serialize(trace).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

#[pymodule]
fn sigil_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(solve_constraints, m)?)?;
    m.add_function(wrap_pyfunction!(match_rules, m)?)?;
    m.add_function(wrap_pyfunction!(serialize_trace, m)?)?;
    Ok(())
}
```

### Usage from Sigil

```sigil
import rust sigil_core::solver
import rust sigil_core::matcher

-- Transparently use Rust for hot paths
rule complex_constraint_check:
  given solution as solver.solve(constraints, facts)
  when solution is satisfiable
  then proceed with solution.assignments
  using rust  -- hint to use Rust backend for this rule's evaluation
```

### Build Integration

```toml
# Cargo.toml for sigil_core
[package]
name = "sigil_core"
version = "0.1.0"
edition = "2021"

[lib]
name = "sigil_core"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.21", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
bincode = "1.3"
```

```toml
# pyproject.toml integration
[tool.maturin]
module-name = "sigil._sigil_core"
```

Build with: `maturin develop` (dev) or `maturin build --release` (production)

## Interop Patterns

### Pattern 1: Neural Parse → Symbolic Execute
```sigil
-- Python handles the neural parsing
neural parse_request from text: Text:
  using python intent_parser.parse  -- Python/transformers backend
  returns Record
  confidence_threshold 0.8
  fallback to {intent: :unknown}

-- Rust handles the symbolic execution
rule process_request:
  given parsed as parse_request(input_text)
  when parsed.intent is :purchase
  and parsed.amount exceeds 0
  then execute_purchase(parsed)
  using rust sigil_core::purchase_engine
```

### Pattern 2: Hybrid Pipeline
```sigil
-- Stage 1: Python ML model
define features as python:
  return feature_extractor.transform(raw_data)

-- Stage 2: Sigil rules (interpreted or Rust-backed)
rule feature_gate:
  when features.risk_score exceeds threshold
  then flag_for_review

-- Stage 3: Python visualization
define report as python:
  return generate_report(decision, trace)
```

### Pattern 3: Gradual Rust Migration
```sigil
-- Start with pure Sigil (Python interpreter)
rule initial_implementation:
  when x exceeds y then alert

-- Later, add Rust backend for hot paths (same Sigil code!)
rule optimized_implementation:
  when x exceeds y then alert
  using rust  -- same logic, 100x faster
```

The `using rust` directive tells the interpreter to delegate this rule's evaluation to the Rust core. The Sigil code doesn't change — only the execution backend.

## Future: C/C++ FFI via Rust

Since Rust has zero-cost C FFI, Sigil gains indirect access to C/C++ libraries:

```sigil
-- Access BLAS/LAPACK via Rust's ndarray
import rust sigil_core::linalg

-- Access SQLite via Rust's rusqlite
import rust sigil_core::database

-- Access any C library wrapped in Rust
import rust sigil_core::custom_c_wrapper
```

## Future: WASM Target

Both Sigil's interpreter logic and Rust core can compile to WebAssembly:

```
sigil_core (Rust) → wasm32-wasi → browser/edge
sigil interpreter (Python) → Pyodide → browser
```

This enables client-side rule evaluation — Sigil programs running in the browser with no server round-trip.
