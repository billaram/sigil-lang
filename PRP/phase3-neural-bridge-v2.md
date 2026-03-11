# Neural Bridge v2: Multi-Backend Architecture & Enhanced Parameters

**Date**: 2026-03-11
**Status**: COMPLETE (implemented 2026-03-11)
**Depends on**: Phase 3 Sprint 2 (complete — 764 tests)
**Scope**: Extend the neural bridge from "HuggingFace-only classification" to a production-grade multi-backend system supporting all 5 neuro-symbolic patterns
**Result**: 6 backends, NeuralConfig with 16 parameters, timeout enforcement, 76 neural tests (807 total)

---

## Problem Statement

Phase 3 Sprint 2 delivered a working neural bridge, but it has three bottlenecks:

1. **Single backend**: Only HuggingFace `pipeline()` is supported. No LLM APIs (Claude, GPT, Gemini), no ONNX, no custom Python models.
2. **Missing parameters**: No `labels` (zero-shot), no `temperature`/`prompt` (LLM generation), no `output_schema` (structured output). The neural declaration can't express what real neuro-symbolic systems need.
3. **Single return shape**: `ModelResult` only holds one value + one confidence. Real systems return ranked candidate lists, structured records, or formal expressions.

### What This Means in Practice

```sigil
-- THIS is all we can do today:
neural classify from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"
  returns Symbol
  confidence_threshold 0.7
  fallback to :neutral

-- BUT real neuro-symbolic systems need ALL of these:

-- 1. Zero-shot: "which of these labels fits?"
neural classify_topic from text: Text:
  model "hf:facebook/bart-large-mnli"
  labels :triangle, :rectangle, :circle     -- ← CAN'T DO THIS
  returns Symbol

-- 2. LLM: "generate a structured plan"
neural suggest_strategy from problem: Text:
  model "claude:claude-sonnet-4-20250514"                -- ← CAN'T DO THIS
  system_prompt "You are a math expert..."   -- ← CAN'T DO THIS
  temperature 0.2                            -- ← CAN'T DO THIS
  returns record:                            -- ← CAN'T DO THIS (structured)
    strategy: Symbol
    reasoning: Text

-- 3. ONNX: "fast edge inference"
neural detect_object from image: Bytes:
  model "onnx:yolov8n.onnx"                 -- ← CAN'T DO THIS
  returns Symbol

-- 4. Custom Python model
neural predict_churn from features: Record:
  model "python:models.churn_model.predict"  -- ← CAN'T DO THIS
  returns Number
```

---

## The 5 Neuro-Symbolic Patterns Sigil Must Support

Research on real systems (AlphaGeometry, AlphaProof, AlphaCode, DeepProbLog, Scallop) reveals 5 distinct patterns at the neural-symbolic boundary. Each has different parameter and return type requirements.

### Pattern 1: Classification (Text → Symbol)

**Real-world**: Sentiment analysis, content moderation, intent detection
**Neural returns**: Single label + confidence
**Parameters needed**: Just model + threshold + fallback
**Status**: **Works today**

```sigil
neural classify_sentiment from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"
  returns Symbol
  confidence_threshold 0.7
  fallback to :neutral
```

### Pattern 2: Zero-Shot Classification (Text + Labels → Symbol)

**Real-world**: Topic routing, problem type detection, dynamic categorization
**Neural returns**: Best-matching label from candidates + confidence
**Parameters needed**: `labels` (candidate list), optional `hypothesis` template
**Status**: **Not supported — MISSING `labels`**

```sigil
neural parse_problem_type from text: Text:
  model "hf:facebook/bart-large-mnli"
  returns Symbol
  labels :triangle, :rectangle, :circle, :algebra, :calculus
  hypothesis "This math problem involves a {}."
  confidence_threshold 0.7
  fallback to :unknown
```

**How it works under the hood**:
```python
# HuggingFace zero-shot-classification pipeline
pipe = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = pipe(
    "Find side c of triangle where a=10 b=8 angle_C=60",
    candidate_labels=["triangle", "rectangle", "circle", "algebra", "calculus"],
    hypothesis_template="This math problem involves a {}."
)
# → {"labels": ["triangle", ...], "scores": [0.89, ...]}
```

### Pattern 3: LLM Structured Output (Text + Prompt → Record)

**Real-world**: AlphaGeometry (construction suggestions), risk assessment, proof planning
**Neural returns**: Structured record/dict matching a schema
**Parameters needed**: `system_prompt`, `temperature`, `max_tokens`, `output_schema`
**Status**: **Not supported — no LLM backend, no generation params**

```sigil
neural suggest_proof_plan from problem: Text:
  model "claude:claude-sonnet-4-20250514"
  returns record:
    strategy: Symbol
    steps: list
    reasoning: Text
  system_prompt "You are a math proof assistant. Given a geometry problem, suggest a proof strategy. Return JSON with strategy (one of: law_of_cosines, law_of_sines, pythagorean), steps (list of strings), and reasoning."
  temperature 0.2
  max_tokens 300
  confidence_threshold 0.5
  fallback to {strategy: :unknown, steps: [], reasoning: "Model unavailable"}
```

**How it works under the hood**:
```python
# Anthropic API with structured output
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system="You are a math proof assistant...",
    messages=[{"role": "user", "content": problem_text}],
    temperature=0.2,
    max_tokens=300,
)
# Parse JSON from response → Sigil Record
```

### Pattern 4: Candidate Generation (Text → Ranked List)

**Real-world**: AlphaCode (millions of solutions), AlphaProof (tactic suggestions), beam search
**Neural returns**: Ranked list of (value, score) pairs
**Parameters needed**: `num_candidates`, `temperature` (high for diversity)
**Status**: **Not supported — ModelResult holds single value**

```sigil
-- LLM API: no beam search, use temperature for diversity
neural generate_constructions from proof_state: Text:
  model "claude:claude-sonnet-4-20250514"
  returns list of Symbol
  num_candidates 5
  temperature 0.8
  system_prompt "Suggest geometric construction steps..."
  confidence_threshold 0.3
  fallback to [:no_construction]

-- HuggingFace: beam search for thorough exploration (AlphaGeometry style)
neural suggest_construction from state: Text:
  model "hf:custom-geometry-model"
  returns Symbol
  beam_size 128
  num_candidates 10
  temperature 1.0
  confidence_threshold 0.3
  fallback to :no_construction
```

### Pattern 5: Custom Python Model (Features → Prediction)

**Real-world**: scikit-learn classifiers, PyTorch models, custom inference
**Neural returns**: Depends on model (Number, Symbol, Record)
**Parameters needed**: Python callable path, optional preprocessing
**Status**: **Not supported — no Python callable backend**

```sigil
neural predict_churn from customer: Record:
  model "python:models.churn_model.predict"
  returns Number
  confidence_threshold 0.6
  fallback to 0.5
```

---

## Neural Declaration: Full Parameter Reference

### Universal Parameters (all patterns)

| Parameter | Sigil Syntax | Type | Default | Purpose |
|-----------|-------------|------|---------|---------|
| `model` | `model "prefix:model-id"` | Text | (required) | Model identifier with backend prefix |
| `returns` | `returns Symbol` | TypeRef | (required) | Expected return type |
| `confidence_threshold` | `confidence_threshold 0.85` | Number | 0.5 | Minimum confidence to accept result |
| `fallback` | `fallback to :unknown` | Value | (required) | Value when confidence too low / error / timeout |
| `timeout` | `timeout 30 seconds` | Duration | 60s | Maximum inference time before fallback |

### Classification Parameters (HuggingFace text-classification)

| Parameter | Sigil Syntax | Type | Default | Purpose |
|-----------|-------------|------|---------|---------|
| (none beyond universal) | | | | Model is pre-configured for its task |

### Zero-Shot Parameters (HuggingFace zero-shot-classification)

| Parameter | Sigil Syntax | Type | Default | Purpose |
|-----------|-------------|------|---------|---------|
| `labels` | `labels :a, :b, :c` | List[Symbol] | (required for zero-shot) | Candidate classification labels |
| `hypothesis` | `hypothesis "This is about {}."` | Text | `"This example is {}."` | NLI hypothesis template |
| `multi_label` | `multi_label true` | Bool | false | Allow multiple true labels |

### LLM Generation Parameters (Claude, GPT, Gemini)

| Parameter | Sigil Syntax | Type | Default | Purpose |
|-----------|-------------|------|---------|---------|
| `system_prompt` | `system_prompt "You are..."` | Text | none | System instruction for the LLM |
| `temperature` | `temperature 0.7` | Number | 1.0 | Sampling randomness (0.0 = deterministic, 2.0 = max random) |
| `max_tokens` | `max_tokens 500` | Number | 1024 | Maximum output length |
| `top_p` | `top_p 0.9` | Number | 1.0 | Nucleus sampling threshold |
| `top_k` | `top_k 40` | Number | none | Top-k sampling (Anthropic/Google) |
| `stop_sequences` | `stop_at ["\n", "END"]` | List[Text] | none | Stop generation at these strings |
| `output_schema` | `output_schema RecordTypeName` | TypeRef | none | Constrain output to match a Sigil record type |

### Candidate Generation Parameters

| Parameter | Sigil Syntax | Type | Default | Purpose |
|-----------|-------------|------|---------|---------|
| `num_candidates` | `num_candidates 10` | Number | 1 | How many results to return |
| `beam_size` | `beam_size 128` | Number | none | Internal search width (HF only — how many paths to explore). LLM APIs ignore this; they use `temperature` + `num_candidates` for diversity. AlphaGeometry uses 128. |
| (uses LLM params) | `temperature 0.8` | Number | | High temperature for diversity |

**`beam_size` vs `num_candidates` vs `temperature`**:
- `beam_size` = how many paths the model explores internally (HuggingFace `num_beams`). Deterministic search — high beam → better results but slower.
- `num_candidates` = how many results are returned to Sigil. Maps to HuggingFace `num_return_sequences` or OpenAI `n`.
- `temperature` = randomness per generation. High temp + multiple candidates → diverse exploration.
- LLM APIs (Claude, OpenAI) don't expose beam search. Use `temperature` + `num_candidates` instead.
- HuggingFace text-generation supports all three: `num_beams=128, num_return_sequences=5, temperature=1.0`.

### Python Callable Parameters

| Parameter | Sigil Syntax | Type | Default | Purpose |
|-----------|-------------|------|---------|---------|
| (none beyond universal) | | | | The Python function IS the model |

---

## Multi-Backend Architecture

### Current State

```
ModelRegistry
  └── "hf:" prefix → HuggingFaceBackend (text-classification only)
```

### Target State

```
ModelRegistry
  ├── "hf:"      → HuggingFaceBackend     (classification, zero-shot, NER, QA)
  ├── "claude:"  → AnthropicBackend        (Claude API — structured output, generation)
  ├── "openai:"  → OpenAIBackend           (GPT API — structured output, generation)
  ├── "onnx:"    → ONNXBackend             (ONNX Runtime — fast edge inference)
  ├── "python:"  → PythonCallableBackend   (any Python function/class)
  └── "mock:"    → MockBackend             (deterministic testing)
```

### Backend Protocol (Enhanced)

```python
@dataclass(frozen=True)
class NeuralConfig:
    """All parameters from the neural declaration, passed to backend."""
    model_id: str
    return_type: str                                    # "Symbol", "Number", "Record", etc.
    confidence_threshold: float
    fallback: Value
    # Zero-shot
    labels: tuple[str, ...] | None = None               # candidate labels
    hypothesis_template: str | None = None               # NLI template
    # LLM generation
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: tuple[str, ...] | None = None
    output_schema: dict | None = None                    # JSON schema for structured output
    # Candidate generation
    num_candidates: int = 1
    beam_size: int | None = None                          # HF num_beams (ignored by LLM APIs)
    # Timeout
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class CandidateResult:
    """A single candidate in a ranked list."""
    value: Value
    score: float


@dataclass(frozen=True)
class ModelResult:
    value: Value                                         # Primary result (top candidate)
    confidence: float                                    # Primary confidence
    model_id: str
    latency_ms: float
    candidates: tuple[CandidateResult, ...] | None = None  # Ranked alternatives
    metadata: dict[str, Any] | None = None                  # Backend-specific metadata


class ModelBackend(Protocol):
    def load(self, model_id: str, config: NeuralConfig) -> None: ...
    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult: ...
```

**Key change**: `predict()` now receives `NeuralConfig` so each backend can use the parameters it cares about and ignore the rest.

---

## Backend Specifications

### 1. HuggingFaceBackend (`hf:` prefix) — ENHANCE EXISTING

**File**: `src/sigil/neural/huggingface.py`

**Currently supports**: `text-classification` pipeline only.

**Enhance to support**:

| HF Pipeline | Trigger | Example Model |
|-------------|---------|---------------|
| `text-classification` | No `labels` field | `hf:distilbert-base-uncased-finetuned-sst-2-english` |
| `zero-shot-classification` | Has `labels` field | `hf:facebook/bart-large-mnli` |
| `token-classification` | `returns list of Record` | `hf:dslim/bert-base-NER` |
| `question-answering` | Two input params | `hf:deepset/roberta-base-squad2` |
| `text-generation` | Has `max_tokens` | `hf:gpt2` |

**Zero-shot classification flow**:
```python
def predict(self, model_id, input_data, config):
    if config.labels:
        # Use zero-shot-classification pipeline
        pipe = pipeline("zero-shot-classification", model=hf_model)
        result = pipe(
            str(input_data),
            candidate_labels=[str(l) for l in config.labels],
            hypothesis_template=config.hypothesis_template or "This example is {}.",
        )
        top_label = result["labels"][0]
        top_score = result["scores"][0]
        return ModelResult(
            value=Symbol(top_label),
            confidence=top_score,
            model_id=model_id,
            latency_ms=...,
            candidates=tuple(
                CandidateResult(Symbol(l), s)
                for l, s in zip(result["labels"], result["scores"])
            ),
        )
    else:
        # Existing text-classification logic
        ...
```

**Dependencies**: `transformers` (optional — graceful fallback if not installed)

---

### 2. AnthropicBackend (`claude:` prefix) — NEW

**File**: `src/sigil/neural/anthropic_backend.py`

**Handles**: All Claude API models via the `anthropic` Python SDK.

**Model ID format**: `claude:<model-name>`
- `claude:claude-sonnet-4-20250514` → Anthropic `claude-sonnet-4-20250514`
- `claude:claude-haiku-4-5-20251001` → Anthropic `claude-haiku-4-5-20251001`

**Predict flow**:
```python
import anthropic

class AnthropicBackend(ModelBackend):
    def __init__(self):
        self._client: anthropic.Anthropic | None = None

    def load(self, model_id: str, config: NeuralConfig) -> None:
        # Lazy init client (uses ANTHROPIC_API_KEY env var)
        if self._client is None:
            self._client = anthropic.Anthropic()

    def predict(self, model_id, input_data, config):
        model_name = model_id.removeprefix("claude:")
        messages = [{"role": "user", "content": str(input_data)}]
        kwargs = {"model": model_name, "messages": messages, "max_tokens": config.max_tokens or 1024}

        if config.system_prompt:
            kwargs["system"] = config.system_prompt
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature

        response = self._client.messages.create(**kwargs)
        text = response.content[0].text

        # Marshal based on return type
        if config.output_schema or config.return_type == "Record":
            value = json.loads(text)  # → Sigil Record via marshal
            confidence = 1.0  # Structured output is schema-guaranteed
        else:
            value = Symbol(text.strip().lower().replace(" ", "_"))
            confidence = response.usage.output_tokens / (config.max_tokens or 1024)

        return ModelResult(value=marshal(value), confidence=confidence, ...)
```

**Confidence heuristic for LLMs**: LLMs don't return confidence scores natively. Options:
1. **Always 1.0** for structured output (schema-guaranteed correctness)
2. **Token probability** if available (logprobs)
3. **Self-reported confidence** — ask the model to include a confidence field in structured output
4. **Default to threshold + 0.01** (always passes unless explicitly overridden)

**Recommendation**: Use option 3 — require `confidence: Number` field in `output_schema` when using LLM backends. The model self-reports, and the symbolic engine verifies.

**Dependencies**: `anthropic` (optional — graceful fallback)
**Auth**: `ANTHROPIC_API_KEY` environment variable (standard)

---

### 3. OpenAIBackend (`openai:` prefix) — NEW

**File**: `src/sigil/neural/openai_backend.py`

**Handles**: All OpenAI API models and compatible APIs (Azure OpenAI, local vLLM, Ollama with OpenAI compat).

**Model ID format**: `openai:<model-name>`
- `openai:gpt-4o` → OpenAI `gpt-4o`
- `openai:gpt-4o-mini` → OpenAI `gpt-4o-mini`
- `openai:local/llama3` → local vLLM/Ollama (via `OPENAI_BASE_URL`)

**Predict flow**: Nearly identical to AnthropicBackend but uses `openai.OpenAI()` client.

**Structured output**: OpenAI supports `response_format={"type": "json_schema", "json_schema": {...}}` for guaranteed JSON output.

**Dependencies**: `openai` (optional)
**Auth**: `OPENAI_API_KEY` environment variable

---

### 4. ONNXBackend (`onnx:` prefix) — NEW

**File**: `src/sigil/neural/onnx_backend.py`

**Handles**: Pre-exported ONNX models for fast, dependency-light inference. No PyTorch/TensorFlow needed at runtime.

**Why ONNX**:
- 10-100x faster inference than HuggingFace pipeline (no Python overhead)
- Works on CPU, GPU, edge devices
- Single runtime dependency (`onnxruntime`)
- Models exported once, deployed anywhere
- Perfect for production where you don't want `torch` in the dependency tree

**Model ID format**: `onnx:<path-to-model>`
- `onnx:models/classifier.onnx` → local ONNX file
- `onnx:https://huggingface.co/.../model.onnx` → remote ONNX model

**Predict flow**:
```python
import onnxruntime as ort

class ONNXBackend(ModelBackend):
    def __init__(self):
        self._sessions: dict[str, ort.InferenceSession] = {}

    def load(self, model_id, config):
        path = model_id.removeprefix("onnx:")
        self._sessions[model_id] = ort.InferenceSession(path)

    def predict(self, model_id, input_data, config):
        session = self._sessions[model_id]
        # Input marshaling depends on model (text → tokenized, image → tensor)
        inputs = self._prepare_inputs(session, input_data, config)
        outputs = session.run(None, inputs)
        return self._marshal_outputs(outputs, config)
```

**Limitation**: Requires a tokenizer/preprocessor alongside the ONNX model. For text models, this means either:
- Bundle tokenizer config with the ONNX file
- Use `onnxruntime-extensions` for built-in tokenization
- Require a Python preprocessing step

**Dependencies**: `onnxruntime` (optional)

---

### 5. PythonCallableBackend (`python:` prefix) — NEW

**File**: `src/sigil/neural/python_callable.py`

**Handles**: Any Python function or class method used as a model. Bridges scikit-learn, PyTorch, custom logic.

**Model ID format**: `python:<dotted.path.to.callable>`
- `python:models.churn.predict` → imports `models.churn`, calls `.predict()`
- `python:sklearn_wrapper.classify` → imports `sklearn_wrapper`, calls `.classify()`

**Predict flow**:
```python
class PythonCallableBackend(ModelBackend):
    def __init__(self):
        self._callables: dict[str, Callable] = {}

    def load(self, model_id, config):
        path = model_id.removeprefix("python:")
        module_path, func_name = path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        self._callables[model_id] = getattr(module, func_name)

    def predict(self, model_id, input_data, config):
        func = self._callables[model_id]
        py_input = sigil_to_python(input_data)
        raw_result = func(py_input)

        # Convention: function returns (value, confidence) or just value
        if isinstance(raw_result, tuple) and len(raw_result) == 2:
            value, confidence = raw_result
        else:
            value, confidence = raw_result, 1.0

        return ModelResult(
            value=python_to_sigil(value),
            confidence=float(confidence),
            ...
        )
```

**Convention**: Python callables can return:
- `value` → confidence defaults to 1.0
- `(value, confidence)` → explicit confidence
- `{"value": ..., "confidence": ...}` → dict format

**Dependencies**: None (uses Python stdlib `importlib`)

---

### 6. MockBackend (`mock:` prefix) — NEW

**File**: `src/sigil/neural/mock_backend.py`

**Handles**: Deterministic, repeatable results for testing. No network, no models, no randomness.

**Model ID format**: `mock:<behavior>`
- `mock:echo` → returns input as output (confidence 1.0)
- `mock:fail` → always throws error (tests fallback path)
- `mock:low_confidence` → returns result with confidence 0.1 (tests threshold)
- `mock:slow` → sleeps for timeout duration (tests timeout)

**Predict flow**:
```python
class MockBackend(ModelBackend):
    def predict(self, model_id, input_data, config):
        behavior = model_id.removeprefix("mock:")
        if behavior == "echo":
            return ModelResult(value=input_data, confidence=1.0, ...)
        elif behavior == "fail":
            raise RuntimeError("Mock failure")
        elif behavior == "low_confidence":
            return ModelResult(value=Symbol("mock_result"), confidence=0.1, ...)
        elif behavior == "slow":
            time.sleep(config.timeout_seconds + 1)
            return ModelResult(...)
```

**Why this matters**: Every neural test should use `mock:` backend. No flaky CI from network calls or model downloads.

---

## How Parameters Flow Through the System

```
.sigil source                  Parser                    Evaluator
─────────────                  ──────                    ─────────
neural classify from text: Text:
  model "hf:bart-large-mnli"   → NeuralDecl              → _call_neural()
  returns Symbol                  name="classify"            │
  labels :tri, :rect, :circ      fields=[                   │ 1. Extract all fields
  hypothesis "..."                  NeuralField("model",     │    into NeuralConfig
  confidence_threshold 0.7          NeuralField("labels",    │
  fallback to :unknown              NeuralField("hypothesis",│ 2. Registry routes
                                    ...                      │    "hf:" → HuggingFaceBackend
                                  ]                          │
                                                             │ 3. backend.predict(
                                                             │      model_id, input, config
                                                             │    )
                                                             │
                                                             │ 4. Check confidence
                                                             │    ≥ threshold → use result
                                                             │    < threshold → use fallback
                                                             │
                                                             │ 5. Record NeuralTrace
                                                             ▼
                                                          Value returned to env
```

---

## Implementation Plan

### Sprint A: Enhanced Parameters + Zero-Shot (~20 tests) — COMPLETE

**Goal**: `labels` and `hypothesis` work. The theorem solver demo runs with a real model.

| # | Task | File | Tests |
|---|------|------|-------|
| 1 | Add `NeuralConfig` dataclass | `src/sigil/neural/backend.py` | 3 |
| 2 | Add `CandidateResult` to `ModelResult` | `src/sigil/neural/backend.py` | 2 |
| 3 | Extract neural fields → `NeuralConfig` in evaluator | `src/sigil/interpreter/evaluator.py` | 3 |
| 4 | Pass `NeuralConfig` to `backend.predict()` | `src/sigil/neural/registry.py` | 2 |
| 5 | HuggingFace: zero-shot-classification when `labels` present | `src/sigil/neural/huggingface.py` | 5 |
| 6 | Add `MockBackend` for testing | `src/sigil/neural/mock_backend.py` | 3 |
| 7 | Update theorem_solver.sigil with real zero-shot model | `examples/neuro_symbolic/theorem_solver.sigil` | 2 |

**Exit criteria**:
```sigil
neural parse_problem_type from text: Text:
  model "hf:facebook/bart-large-mnli"
  returns Symbol
  labels :triangle, :rectangle, :circle
  confidence_threshold 0.7
  fallback to :unknown

main:
  given ptype as parse_problem_type("Find side c of a triangle")
  print(ptype)  -- :triangle (from real model!)
```

### Sprint B: LLM Backends (~25 tests) — COMPLETE

**Goal**: Claude and OpenAI APIs work as neural backends. Structured output returns Records.

| # | Task | File | Tests |
|---|------|------|-------|
| 1 | Implement `AnthropicBackend` | `src/sigil/neural/anthropic_backend.py` | 6 |
| 2 | Implement `OpenAIBackend` | `src/sigil/neural/openai_backend.py` | 6 |
| 3 | Register `claude:` and `openai:` prefixes | `src/sigil/neural/registry.py` | 2 |
| 4 | LLM → Record marshaling (JSON parse → Sigil Record) | `src/sigil/ffi/marshal.py` | 4 |
| 5 | Structured output via `output_schema` | evaluator + backends | 3 |
| 6 | LLM confidence strategy (self-reported) | backends | 2 |
| 7 | Update examples: LLM-powered theorem solver | `examples/neuro_symbolic/theorem_solver_llm.sigil` | 2 |

**Exit criteria**:
```sigil
neural suggest_strategy from problem: Text:
  model "claude:claude-haiku-4-5-20251001"
  returns record:
    strategy: Symbol
    reasoning: Text
    confidence: Number
  system_prompt "Given a geometry problem, return JSON: {strategy, reasoning, confidence}"
  temperature 0.2
  max_tokens 200
  confidence_threshold 0.5
  fallback to {strategy: :unknown, reasoning: "Model unavailable", confidence: 0.0}

main:
  given plan as suggest_strategy("Find side c of triangle where a=10 b=8 C=60")
  print(plan)  -- record(strategy: :law_of_cosines, reasoning: "...", confidence: 0.92)
```

### Sprint C: ONNX + Python Callable + Timeout (~15 tests) — COMPLETE

**Goal**: Edge inference and custom models work. Timeout enforcement.

| # | Task | File | Tests |
|---|------|------|-------|
| 1 | Implement `ONNXBackend` | `src/sigil/neural/onnx_backend.py` | 4 |
| 2 | Implement `PythonCallableBackend` | `src/sigil/neural/python_callable.py` | 4 |
| 3 | Register `onnx:` and `python:` prefixes | `src/sigil/neural/registry.py` | 2 |
| 4 | Timeout enforcement (threading.Timer or signal) | `src/sigil/neural/registry.py` | 3 |
| 5 | Examples and integration tests | `examples/` | 2 |

**Exit criteria**:
```sigil
-- Custom Python scikit-learn model
neural predict_risk from features: Record:
  model "python:risk_model.predict"
  returns Number
  confidence_threshold 0.6
  timeout 5 seconds
  fallback to 0.5
```

---

## File Map

```
NEW:  src/sigil/neural/mock_backend.py          — deterministic testing backend
NEW:  src/sigil/neural/anthropic_backend.py      — Claude API backend
NEW:  src/sigil/neural/openai_backend.py         — OpenAI API backend
NEW:  src/sigil/neural/onnx_backend.py           — ONNX Runtime backend
NEW:  src/sigil/neural/python_callable.py        — Custom Python function backend
MOD:  src/sigil/neural/backend.py                — NeuralConfig, CandidateResult, enhanced ModelResult
MOD:  src/sigil/neural/registry.py               — register all new backends, timeout enforcement
MOD:  src/sigil/neural/huggingface.py            — zero-shot classification support
MOD:  src/sigil/interpreter/evaluator.py         — extract NeuralConfig from NeuralDecl fields
MOD:  src/sigil/ffi/marshal.py                   — JSON → Record marshaling for LLM output
NEW:  tests/neural/test_mock_backend.py          — 5+ tests
NEW:  tests/neural/test_anthropic_backend.py     — 6+ tests (mocked API)
NEW:  tests/neural/test_openai_backend.py        — 6+ tests (mocked API)
NEW:  tests/neural/test_onnx_backend.py          — 4+ tests (mocked runtime)
NEW:  tests/neural/test_python_callable.py       — 4+ tests
NEW:  tests/neural/test_neural_config.py         — 5+ tests
MOD:  tests/neural/test_huggingface.py           — add zero-shot tests
MOD:  tests/neural/test_integration.py           — add multi-backend integration tests
NEW:  examples/neuro_symbolic/theorem_solver_llm.sigil
MOD:  examples/neuro_symbolic/theorem_solver.sigil  — use zero-shot with labels
```

---

## Dependency Strategy

All ML/API dependencies are **optional**. Sigil core has zero ML dependencies.

| Backend | Dependency | Install Command | Fallback |
|---------|-----------|-----------------|----------|
| HuggingFace | `transformers` | `pip install sigil-lang[hf]` | Returns fallback value |
| Claude | `anthropic` | `pip install sigil-lang[claude]` | Returns fallback value |
| OpenAI | `openai` | `pip install sigil-lang[openai]` | Returns fallback value |
| ONNX | `onnxruntime` | `pip install sigil-lang[onnx]` | Returns fallback value |
| Python callable | (none) | built-in | N/A |
| Mock | (none) | built-in | N/A |
| All backends | all of above | `pip install sigil-lang[all]` | N/A |

**pyproject.toml extras**:
```toml
[project.optional-dependencies]
hf = ["transformers>=4.30", "torch>=2.0"]
claude = ["anthropic>=0.40"]
openai = ["openai>=1.0"]
onnx = ["onnxruntime>=1.16"]
all = ["sigil-lang[hf,claude,openai,onnx]"]
```

---

## Security Model

| Concern | Mitigation |
|---------|------------|
| API keys in source | Backend reads from env vars only (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`). Never from .sigil files. |
| Arbitrary Python execution | `python:` backend requires explicit model path. No `eval()` or `exec()`. |
| Network calls | All backends log the model ID in trace. `mock:` backend never makes network calls. |
| Cost control | `max_tokens` limits LLM output. `timeout` kills long-running inference. No retry loops. |
| ONNX model loading | Local paths only by default. Remote URLs require explicit opt-in. |

---

## Testing Strategy

| Test Type | Approach |
|-----------|----------|
| Unit tests | Each backend tested in isolation with mocks |
| Integration tests | End-to-end `.sigil` programs using `mock:` backend |
| Real model tests | Marked `@pytest.mark.slow`, run manually or in nightly CI |
| API tests | Mock HTTP responses (no real API calls in CI) |

**Target**: 60+ new tests → 824+ total

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Anthropic/OpenAI SDK breaking changes | Backend fails | Pin SDK versions in extras; backends catch generic exceptions |
| LLM returns invalid JSON | Structured output fails | JSON parse error → fallback. Add retry-once option later. |
| ONNX model requires specific tokenizer | Can't run model | Document tokenizer requirement; support tokenizer config files |
| API rate limits | Slow execution | Cache results per (model, input) pair; document rate limit behavior |
| Large model downloads in CI | CI timeout | All CI tests use `mock:` backend; real models in `@pytest.mark.slow` |
| Python callable imports unsafe code | Security risk | Document: `python:` backend trusts the imported code. Same as `import python`. |

---

## How This Fixes the Theorem Solver

### Before (broken demo with wrong model):
```sigil
neural parse_problem_type from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"  -- WRONG: sentiment model
  returns Symbol
  confidence_threshold 0.99  -- HACK: force fallback
  fallback to :triangle
```

### After Sprint A (real zero-shot classification):
```sigil
neural parse_problem_type from text: Text:
  model "hf:facebook/bart-large-mnli"  -- RIGHT: zero-shot classifier
  returns Symbol
  labels :triangle, :rectangle, :circle, :algebra
  hypothesis "This math problem involves a {}."
  confidence_threshold 0.7
  fallback to :unknown
```

### After Sprint B (LLM returns full plan):
```sigil
neural suggest_proof_plan from problem: Text:
  model "claude:claude-haiku-4-5-20251001"
  returns record:
    strategy: Symbol
    steps: list
    reasoning: Text
    confidence: Number
  system_prompt "Analyze this geometry problem. Return JSON with: strategy (law_of_cosines, law_of_sines, pythagorean), steps (list of computation steps), reasoning (why this strategy), confidence (0-1)."
  temperature 0.1
  max_tokens 300
  confidence_threshold 0.5
  fallback to {strategy: :unknown, steps: [], reasoning: "unavailable", confidence: 0.0}

main:
  given plan as suggest_proof_plan("Find side c of triangle where a=10 b=8 C=60")
  -- plan.strategy = :law_of_cosines (from Claude)
  -- plan.reasoning = "Triangle with two sides and included angle → Law of Cosines"
  -- plan.confidence = 0.95
  -- The symbolic engine now EXECUTES this plan deterministically
  evaluate all rules with {strategy: plan.strategy, problem_type: :triangle}
  given result as solve_cosines(a, b, angle_C)
  -- Symbolic verification: same as before
```

This is the real AlphaGeometry pattern: **neural suggests, symbolic executes and verifies.**
