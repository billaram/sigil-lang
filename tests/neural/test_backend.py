"""Tests for the neural backend protocol and ModelResult."""

from sigil.interpreter.values import Symbol
from sigil.neural.backend import ModelResult


def test_model_result_creation():
    result = ModelResult(
        value=Symbol("positive"),
        confidence=0.95,
        model_id="test-model",
        latency_ms=42.0,
    )
    assert result.value == Symbol("positive")
    assert result.confidence == 0.95
    assert result.model_id == "test-model"
    assert result.latency_ms == 42.0


def test_model_result_is_frozen():
    result = ModelResult(value="hello", confidence=0.5, model_id="m", latency_ms=1.0)
    import pytest
    with pytest.raises(AttributeError):
        result.confidence = 0.9  # type: ignore[misc]


def test_model_result_with_none_value():
    result = ModelResult(value=None, confidence=0.0, model_id="m", latency_ms=0.0)
    assert result.value is None


def test_model_result_with_list_value():
    result = ModelResult(value=[1, 2, 3], confidence=0.8, model_id="m", latency_ms=5.0)
    assert result.value == [1, 2, 3]


def test_model_result_equality():
    a = ModelResult(value="x", confidence=0.5, model_id="m", latency_ms=1.0)
    b = ModelResult(value="x", confidence=0.5, model_id="m", latency_ms=1.0)
    assert a == b
