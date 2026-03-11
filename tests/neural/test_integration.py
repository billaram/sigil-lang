"""End-to-end neural bridge integration tests."""

from unittest.mock import MagicMock

from sigil.interpreter.values import Symbol
from sigil.lexer.lexer import tokenize
from sigil.neural.backend import ModelResult
from sigil.neural.registry import ModelRegistry
from sigil.parser.parser import parse


def run(source, input_data=None, registry=None):
    """Helper: tokenize → parse → evaluate with optional model registry."""
    from sigil.interpreter.evaluator import Evaluator
    tokens = tokenize(source)
    program = parse(tokens)
    evaluator = Evaluator()

    # Inject a custom registry if provided
    if registry is not None:
        import sigil.neural.registry as reg_mod
        original = reg_mod._global_registry
        reg_mod._global_registry = registry
        try:
            return evaluator.eval_program(program, input_data or {})
        finally:
            reg_mod._global_registry = original
    return evaluator.eval_program(program, input_data or {})


# ------------------------------------------------------------------
# Fallback behavior (no backend)
# ------------------------------------------------------------------


def test_neural_returns_fallback_when_no_backend():
    source = """
neural classify from text: Text:
  model "test:model"
  returns Symbol
  confidence_threshold 0.8
  fallback to :unknown

main:
  given result as classify("hello")
  print(result)
"""
    result, trace = run(source)
    assert ":unknown" in trace.output_lines


def test_neural_fallback_numeric():
    source = """
neural score from text: Text:
  model "test:model"
  returns Number
  confidence_threshold 0.5
  fallback to 0

main:
  given result as score("hello")
  print(result)
"""
    result, trace = run(source)
    assert "0" in trace.output_lines


def test_neural_trace_recorded_on_fallback():
    source = """
neural classify from text: Text:
  model "test:absent-model"
  returns Symbol
  confidence_threshold 0.8
  fallback to :unknown

main:
  given result as classify("hello")
"""
    _, trace = run(source)
    assert len(trace.neural_traces) == 1
    nt = trace.neural_traces[0]
    assert nt.function_name == "classify"
    assert nt.used_fallback is True


# ------------------------------------------------------------------
# With mock backend
# ------------------------------------------------------------------


def _make_mock_registry(result_value, confidence):
    """Create a registry with a mock backend."""
    registry = ModelRegistry()
    backend = MagicMock()
    backend.predict.return_value = ModelResult(
        value=result_value,
        confidence=confidence,
        model_id="mock:test",
        latency_ms=5.0,
    )
    registry.register_backend("mock:", backend)
    return registry


def test_neural_uses_model_when_above_threshold():
    source = """
neural classify from text: Text:
  model "mock:test"
  returns Symbol
  confidence_threshold 0.7
  fallback to :unknown

main:
  given result as classify("great product!")
  print(result)
"""
    registry = _make_mock_registry(Symbol("positive"), 0.95)
    _, trace = run(source, registry=registry)
    assert ":positive" in trace.output_lines
    assert len(trace.neural_traces) == 1
    assert trace.neural_traces[0].used_fallback is False
    assert trace.neural_traces[0].confidence == 0.95


def test_neural_uses_fallback_when_below_threshold():
    source = """
neural classify from text: Text:
  model "mock:test"
  returns Symbol
  confidence_threshold 0.9
  fallback to :unknown

main:
  given result as classify("ambiguous text")
  print(result)
"""
    registry = _make_mock_registry(Symbol("positive"), 0.5)
    _, trace = run(source, registry=registry)
    assert ":unknown" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is True


def test_neural_uses_fallback_on_backend_error():
    source = """
neural classify from text: Text:
  model "mock:test"
  returns Symbol
  confidence_threshold 0.5
  fallback to :error_fallback

main:
  given result as classify("text")
  print(result)
"""
    registry = ModelRegistry()
    backend = MagicMock()
    backend.predict.side_effect = RuntimeError("Model crashed")
    registry.register_backend("mock:", backend)

    _, trace = run(source, registry=registry)
    assert ":error_fallback" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is True
    assert trace.neural_traces[0].error == "Model crashed"


def test_neural_trace_has_latency():
    source = """
neural classify from text: Text:
  model "mock:test"
  returns Symbol
  confidence_threshold 0.5
  fallback to :unknown

main:
  given result as classify("test")
"""
    registry = _make_mock_registry(Symbol("positive"), 0.95)
    _, trace = run(source, registry=registry)
    assert trace.neural_traces[0].latency_ms == 5.0


def test_multiple_neural_calls():
    source = """
neural classify from text: Text:
  model "mock:test"
  returns Symbol
  confidence_threshold 0.5
  fallback to :unknown

main:
  given a as classify("first")
  given b as classify("second")
  print(a)
  print(b)
"""
    registry = _make_mock_registry(Symbol("result"), 0.9)
    _, trace = run(source, registry=registry)
    assert len(trace.neural_traces) == 2


# ------------------------------------------------------------------
# Existing examples still work
# ------------------------------------------------------------------


def test_medical_triage_still_works(triage_source):
    """The medical triage example uses neural stubs — should still produce fallbacks."""
    from sigil.interpreter.evaluator import evaluate
    from sigil.interpreter.values import Record
    tokens = tokenize(triage_source)
    program = parse(tokens)
    patient = Record(type_name=None, fields={
        "name": "Test",
        "age": 40,
        "chief_complaint": "cardiac_arrest",
        "vital_signs": Record(type_name=None, fields={
            "heart_rate": 80,
            "blood_pressure_systolic": 120,
            "temperature": 98.6,
            "oxygen_saturation": 98,
        }),
        "symptoms": ["cardiac_arrest"],
        "medical_history": [],
    })
    result, trace = evaluate(program, {"patient": patient})
    # Should run without error (neural functions return fallbacks)
    assert result is not None


# ------------------------------------------------------------------
# MockBackend (built-in mock: prefix)
# ------------------------------------------------------------------


def test_mock_echo_backend():
    source = """
neural classify from text: Text:
  model "mock:echo"
  returns Symbol
  confidence_threshold 0.5
  fallback to :unknown

main:
  given result as classify("hello world")
  print(result)
"""
    _, trace = run(source)
    assert ":hello_world" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is False


def test_mock_fixed_backend():
    source = """
neural classify from text: Text:
  model "mock:fixed:positive"
  returns Symbol
  confidence_threshold 0.5
  fallback to :unknown

main:
  given result as classify("anything")
  print(result)
"""
    _, trace = run(source)
    assert ":positive" in trace.output_lines


def test_mock_fail_triggers_fallback():
    source = """
neural classify from text: Text:
  model "mock:fail"
  returns Symbol
  confidence_threshold 0.5
  fallback to :error_result

main:
  given result as classify("test")
  print(result)
"""
    _, trace = run(source)
    assert ":error_result" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is True
    assert trace.neural_traces[0].error is not None


def test_mock_low_confidence_uses_fallback():
    source = """
neural classify from text: Text:
  model "mock:low_confidence"
  returns Symbol
  confidence_threshold 0.5
  fallback to :fallback_val

main:
  given result as classify("test")
  print(result)
"""
    _, trace = run(source)
    assert ":fallback_val" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is True


# ------------------------------------------------------------------
# LLM backends (Claude/OpenAI) via mock registry
# ------------------------------------------------------------------


def test_claude_backend_in_sigil():
    """Claude model ID routes through registry and returns fallback when no SDK."""
    source = """
neural solve from text: Text:
  model "claude:claude-sonnet-4-20250514"
  returns Symbol
  system_prompt "You are a math solver."
  temperature 0.3
  confidence_threshold 0.5
  fallback to :no_model

main:
  given result as solve("Find x in 2x+3=7")
  print(result)
"""
    # Without anthropic SDK installed, falls back
    _, trace = run(source)
    # Either the model returned a result or we got fallback
    assert len(trace.neural_traces) == 1


def test_openai_backend_in_sigil():
    """OpenAI model ID routes through registry and returns fallback when no SDK."""
    source = """
neural classify from text: Text:
  model "openai:gpt-4o"
  returns Symbol
  system_prompt "Classify sentiment."
  temperature 0.0
  confidence_threshold 0.5
  fallback to :no_model

main:
  given result as classify("Great product!")
  print(result)
"""
    _, trace = run(source)
    assert len(trace.neural_traces) == 1


def test_structured_output_with_mock():
    """Structured output (Record return type) via mock backend."""
    source = """
neural analyze from text: Text:
  model "mock:fixed:result"
  returns Symbol
  confidence_threshold 0.5
  fallback to :error

main:
  given result as analyze("test")
  print(result)
"""
    _, trace = run(source)
    assert ":result" in trace.output_lines


def test_neural_with_temperature_and_system_prompt():
    """Config parameters are parsed without errors."""
    source = """
neural solve from text: Text:
  model "mock:echo"
  returns Symbol
  system_prompt "Be precise."
  temperature 0.5
  max_tokens 100
  confidence_threshold 0.5
  fallback to :fallback

main:
  given result as solve("test input")
  print(result)
"""
    _, trace = run(source)
    assert ":test_input" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is False


# ------------------------------------------------------------------
# Timeout enforcement
# ------------------------------------------------------------------


def test_timeout_triggers_fallback():
    """Slow backend exceeding timeout triggers fallback."""
    import time as _time

    registry = ModelRegistry()
    backend = MagicMock()

    def slow_predict(model_id, input_data, config):
        _time.sleep(5)  # will exceed timeout
        return ModelResult(value=Symbol("late"), confidence=1.0, model_id=model_id, latency_ms=5000)

    backend.predict.side_effect = slow_predict
    registry.register_backend("slow:", backend)

    source = """
neural classify from text: Text:
  model "slow:model"
  returns Symbol
  timeout 0.1
  confidence_threshold 0.5
  fallback to :timed_out

main:
  given result as classify("test")
  print(result)
"""
    _, trace = run(source, registry=registry)
    # Should have hit fallback due to timeout
    assert trace.neural_traces[0].used_fallback is True


# ------------------------------------------------------------------
# Python callable backend
# ------------------------------------------------------------------


def test_python_callable_in_sigil():
    """Python callable backend via python: prefix in Sigil source."""
    source = """
neural compute_sqrt from x: Number:
  model "python:math.sqrt"
  returns Number
  confidence_threshold 0.0
  fallback to 0

main:
  given result as compute_sqrt(25)
  print(result)
"""
    _, trace = run(source)
    assert "5.0" in trace.output_lines
    assert trace.neural_traces[0].used_fallback is False
