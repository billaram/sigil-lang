# Phase 3: Ecosystem Integration — Implementation Plan

## Context

Phase 2 is complete (665 tests, 7 subsystems, 18 examples). Sigil has a full symbolic engine — lexer, parser, AST, interpreter with forward+backward chaining, type checker, module system, and 7 stdlib modules. But it's isolated: Python imports are silently ignored, neural declarations return hardcoded fallbacks, and the Rust core is an empty PyO3 stub.

Phase 3 connects Sigil to the real world: Python FFI for ML libraries, a pluggable neural bridge for real model inference, and Rust core components for 10-100x performance on hot paths.

## Design Decisions

- **Neural backend**: Pluggable `ModelBackend` interface with HuggingFace as default backend
- **Rust core**: All three components — constraint solver, pattern matcher (Rete), trace serialization
- **Python FFI scope**: `import python`, `from python import`, function wrapping, error translation. Inline Python blocks deferred to Phase 4
- **Sprint structure**: 3 sprints matching the 3 ROADMAP milestones

## Current State (What Already Exists)

| Component | Parser | AST | Evaluator | Tests |
|-----------|--------|-----|-----------|-------|
| `import python X` | Yes — `_parse_import_decl()` handles `python` kind | `ImportDecl(kind="python")` | **Silently ignored** (returns env unchanged) | 0 |
| `import rust X` | Yes — handles `rust` kind + `::` paths | `ImportDecl(kind="rust")` | **Silently ignored** | 0 |
| `neural` declarations | Yes — full parsing | `NeuralDecl` + `NeuralField` | **Stub** — `_call_neural_stub()` returns fallback | 0 (covered by integration) |
| Rust core | N/A | N/A | `_sigil_core` PyO3 module with `__version__` only | 0 |
| FFI module | N/A | N/A | Empty `src/sigil/ffi/__init__.py` | 0 |
| Type marshaling | N/A | N/A | None | 0 |

---

## Sprint 1: Python FFI (~30 tests)

**Goal**: Make `import python X` actually import and call Python libraries from Sigil.

### What to Build

#### 1. Type Marshaling Layer
**File**: `src/sigil/ffi/marshal.py` (NEW)

Bidirectional conversion between Sigil `Value` types and Python objects:

| Sigil → Python | Python → Sigil |
|----------------|----------------|
| `int/float` → `int/float` | `int/float` → `int/float` |
| `str` → `str` | `str` → `str` |
| `bool` → `bool` | `bool` → `bool` |
| `None` → `None` | `None` → `None` |
| `Symbol("x")` → `str("x")` | N/A (no auto-symbol) |
| `Record(fields)` → `dict` | `dict` → `Record(None, fields)` |
| `list[Value]` → `list` | `list` → `list[Value]` |
| `Closure` → not marshaled (error) | `callable` → wrapped callable |

Key functions:
- `sigil_to_python(value: Value) -> Any`
- `python_to_sigil(obj: Any) -> Value`
- `wrap_python_callable(func: Callable) -> Callable` — wraps a Python function to accept/return Sigil values

#### 2. Python Module Importer
**File**: `src/sigil/ffi/python_interop.py` (NEW)

- `import_python_module(source: str) -> dict[str, Value]` — uses `importlib` to import a Python module and marshal its public API into Sigil values
- Handle dotted paths: `import python sklearn.ensemble` → `importlib.import_module("sklearn.ensemble")`
- Handle selective imports: `from python pandas import DataFrame, read_csv`
- Error translation: Python `ImportError` → `SigilRuntimeError`, `TypeError` → `SigilTypeError`

#### 3. Update Evaluator Import Handling
**File**: `src/sigil/interpreter/evaluator.py` — modify `_eval_import()`

Currently Python/Rust imports silently return `env`. Change to:
- `kind == "python"` → call `import_python_module()`, marshal results, bind to env
- `kind == "rust"` → keep as no-op for now (Sprint 3)
- Wrap Python callables so they can be called from Sigil compute/rule contexts

#### 4. Python Function Call Integration
**File**: `src/sigil/interpreter/evaluator.py` — modify `_eval_func_call()`

When a function value is a wrapped Python callable:
- Marshal arguments from Sigil → Python
- Call the Python function
- Marshal return value from Python → Sigil
- Catch Python exceptions → `SigilRuntimeError` with source context

#### 5. Error Translation
**File**: `src/sigil/ffi/errors.py` (NEW)

- `translate_python_error(exc: Exception, context: str) -> SigilRuntimeError`
- Wraps Python tracebacks with Sigil context (which import, which call)
- Preserves original exception as `__cause__`

### Files (Sprint 1)

```
NEW:  src/sigil/ffi/marshal.py
NEW:  src/sigil/ffi/python_interop.py
NEW:  src/sigil/ffi/errors.py
MOD:  src/sigil/ffi/__init__.py
MOD:  src/sigil/interpreter/evaluator.py
NEW:  tests/ffi/test_marshal.py          — 15+ marshaling tests
NEW:  tests/ffi/test_python_interop.py   — 10+ import/call tests
NEW:  tests/ffi/test_errors.py           — 5+ error translation tests
NEW:  examples/interop/python_math.sigil
```

### Sprint 1 Exit Criteria

```sigil
import python math
import python json

main:
  given result as math.sqrt(144)
  print(result)  -- 12.0

  given data as json.loads("{\"name\": \"sigil\"}")
  print(data)  -- record(name: "sigil")
```

---

## Sprint 2: Neural Bridge (~25 tests)

**Goal**: Replace neural stubs with a pluggable model registry that can run real ML models.

### What to Build

#### 1. Model Backend Interface
**File**: `src/sigil/neural/backend.py` (NEW)

```python
class ModelBackend(Protocol):
    def load(self, model_id: str) -> None: ...
    def predict(self, input_data: Value) -> tuple[Value, float]: ...

@dataclass
class ModelResult:
    value: Value
    confidence: float
    model_id: str
    latency_ms: float
```

#### 2. HuggingFace Backend
**File**: `src/sigil/neural/huggingface.py` (NEW)

- Uses `transformers.pipeline()` for inference
- Supports text-classification, sentiment-analysis, zero-shot-classification
- Maps HuggingFace output → `ModelResult`
- Graceful degradation if `transformers` not installed

#### 3. Model Registry
**File**: `src/sigil/neural/registry.py` (NEW)

- Singleton registry mapping model IDs → backends
- Built-in: `"hf:*"` prefix → HuggingFace backend
- Caching: loaded models stay in memory

#### 4. Confidence Type
**File**: `src/sigil/interpreter/values.py` — add `Confidence` to Value union

#### 5. Neural Evaluator (Replace Stub)
**File**: `src/sigil/interpreter/evaluator.py` — replace `_call_neural_stub()`

1. Look up model from registry
2. Marshal input, call backend
3. Check confidence against threshold
4. If below threshold or error → use fallback
5. Record neural trace entry

#### 6. Neural Trace Integration
**File**: `src/sigil/interpreter/trace.py` — add `NeuralTrace` dataclass

Add `neural_traces: list[NeuralTrace]` to `ProgramTrace`.
Update `format_trace()` to render neural steps distinctly from symbolic ones.

### Files (Sprint 2)

```
NEW:  src/sigil/neural/__init__.py
NEW:  src/sigil/neural/backend.py
NEW:  src/sigil/neural/registry.py
NEW:  src/sigil/neural/huggingface.py
MOD:  src/sigil/interpreter/values.py
MOD:  src/sigil/interpreter/evaluator.py
MOD:  src/sigil/interpreter/trace.py
NEW:  tests/neural/test_backend.py       — 5+ tests
NEW:  tests/neural/test_registry.py      — 5+ tests
NEW:  tests/neural/test_huggingface.py   — 5+ tests (mock transformers)
NEW:  tests/neural/test_integration.py   — 10+ end-to-end tests
NEW:  examples/neuro_symbolic/sentiment_analysis.sigil
```

### Sprint 2 Exit Criteria

```sigil
-- With transformers installed:
neural classify_sentiment from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"
  returns Symbol
  confidence_threshold 0.7
  fallback to :neutral

main:
  given sentiment as classify_sentiment("This product is amazing!")
  print(sentiment)  -- :positive

-- Without transformers (graceful fallback):
-- prints :neutral (fallback used)
```

---

## Sprint 3: Rust Core (~25 tests)

**Goal**: Implement performance-critical components in Rust via PyO3 for 10x+ speedup.

### What to Build

#### 1. Value Representation in Rust
**File**: `src/sigil_core/src/values.rs` (NEW)

Rust `SigilValue` enum with PyO3 `FromPyObject`/`IntoPy` traits.

#### 2. Pattern Matcher (Rete-lite)
**File**: `src/sigil_core/src/matcher.rs` (NEW)

- `ReteNetwork::compile(rules)` — build discrimination network
- `ReteNetwork::match_facts(facts) -> Vec<Match>` — find matching rules
- Alpha nodes (single-condition) + Beta nodes (joins)
- Exposed via `#[pyfunction] fn match_rules(...)`

#### 3. Constraint Solver
**File**: `src/sigil_core/src/solver.rs` (NEW)

- Lightweight constraint satisfaction (not full SAT/SMT)
- Numeric comparisons, range checks, set membership, boolean logic
- Exposed via `#[pyfunction] fn solve_constraints(...)`

#### 4. Trace Serialization
**File**: `src/sigil_core/src/trace.rs` (NEW)

- `serialize_trace(trace) -> bytes` (bincode/msgpack)
- `serialize_trace_json(trace) -> String`
- Exposed via PyO3

#### 5. Python Integration
**File**: `src/sigil_core/src/lib.rs` — expand with submodules

#### 6. Evaluator Integration
**File**: `src/sigil/interpreter/evaluator.py` — Rust dispatch

- Try import `_sigil_core`; use Rust fast paths if available
- Transparent fallback to Python if Rust not compiled

### Files (Sprint 3)

```
NEW:  src/sigil_core/src/values.rs
NEW:  src/sigil_core/src/matcher.rs
NEW:  src/sigil_core/src/solver.rs
NEW:  src/sigil_core/src/trace.rs
MOD:  src/sigil_core/src/lib.rs
MOD:  src/sigil_core/Cargo.toml          — serde, bincode deps
MOD:  src/sigil/interpreter/evaluator.py
NEW:  tests/rust_core/test_matcher.py    — 10+ tests
NEW:  tests/rust_core/test_solver.py     — 8+ tests
NEW:  tests/rust_core/test_trace.py      — 5+ tests
NEW:  benchmarks/bench_rust_vs_python.py
NEW:  examples/interop/rust_speedup.sigil
```

### Sprint 3 Exit Criteria

```bash
maturin develop                    # Builds
pytest tests/rust_core/ -v         # All pass
python benchmarks/bench_rust_vs_python.py  # >10x speedup shown
```

---

## Implementation Order

```
Sprint 1: Python FFI
  1. marshal.py (type marshaling)
  2. errors.py (error translation)
  3. python_interop.py (module import)
  4. evaluator.py (wire imports + calls)
  5. tests + example
  CHECKPOINT: all tests pass

Sprint 2: Neural Bridge
  6. backend.py (ModelBackend protocol)
  7. registry.py (model registry)
  8. huggingface.py (HF backend)
  9. values.py (Confidence type)
  10. evaluator.py (replace stub)
  11. trace.py (NeuralTrace)
  12. tests + example
  CHECKPOINT: neural tests pass (mocked + real if HF available)

Sprint 3: Rust Core
  13. values.rs → matcher.rs → solver.rs → trace.rs
  14. lib.rs (PyO3 module)
  15. evaluator.py (Rust dispatch)
  16. tests + benchmarks
  CHECKPOINT: maturin develop && pytest && benchmarks
```

## Verification

```bash
# Target: 745+ tests (665 + 80 new)
pytest tests/ -v --tb=short
ruff check src/ tests/
mypy src/sigil/
sigil run examples/interop/python_math.sigil
maturin develop && python benchmarks/bench_rust_vs_python.py
# All 18+ existing examples still work
```

## Risk Register

| Risk | Mitigation |
|------|------------|
| HuggingFace models too large for CI | Mock in tests; real model tests marked `@pytest.mark.slow` |
| Python FFI security (arbitrary exec) | No inline Python blocks; document security model |
| Rete algorithm complexity | Start with Rete-lite; full Rete in Phase 5 |
| Type marshaling edge cases | Property-based tests for marshal.py |

