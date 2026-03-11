"""Tests for the MockBackend."""

import pytest

from sigil.interpreter.values import Symbol
from sigil.neural.backend import NeuralConfig
from sigil.neural.mock_backend import MockBackend


def _config(**kwargs) -> NeuralConfig:
    defaults = {"model_id": "mock:echo"}
    defaults.update(kwargs)
    return NeuralConfig(**defaults)


def test_echo_returns_input_as_symbol():
    backend = MockBackend()
    result = backend.predict("mock:echo", "hello world", _config())
    assert result.value == Symbol("hello_world")
    assert result.confidence == 1.0
    assert result.model_id == "mock:echo"


def test_fail_raises_runtime_error():
    backend = MockBackend()
    with pytest.raises(RuntimeError, match="intentionally failed"):
        backend.predict("mock:fail", "input", _config(model_id="mock:fail"))


def test_low_confidence_returns_low_score():
    backend = MockBackend()
    config = _config(model_id="mock:low_confidence")
    result = backend.predict("mock:low_confidence", "input", config)
    assert result.value == Symbol("low_conf_result")
    assert result.confidence == 0.1


def test_fixed_value():
    backend = MockBackend()
    config = _config(model_id="mock:fixed:positive")
    result = backend.predict("mock:fixed:positive", "input", config)
    assert result.value == Symbol("positive")
    assert result.confidence == 1.0


def test_echo_with_candidates():
    backend = MockBackend()
    config = _config(num_candidates=3)
    result = backend.predict("mock:echo", "test", config)
    assert result.candidates is not None
    assert len(result.candidates) == 3
    assert result.candidates[0].value == Symbol("test_0")


def test_load_is_noop():
    backend = MockBackend()
    backend.load("mock:echo")  # Should not raise
