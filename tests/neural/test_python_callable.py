"""Tests for the PythonCallableBackend (real Python functions)."""

from __future__ import annotations

import pytest

from sigil.interpreter.values import Record
from sigil.neural.backend import NeuralConfig
from sigil.neural.python_callable import PythonCallableBackend


def _config(**kwargs) -> NeuralConfig:
    defaults = {"model_id": "python:math.sqrt"}
    defaults.update(kwargs)
    return NeuralConfig(**defaults)


def test_call_math_sqrt():
    backend = PythonCallableBackend()
    config = _config(model_id="python:math.sqrt")
    result = backend.predict("python:math.sqrt", 25.0, config)
    assert result.value == 5.0
    assert result.confidence == 1.0


def test_call_returns_tuple_with_confidence():
    """Python callable returning (value, confidence) tuple."""
    backend = PythonCallableBackend()

    # Register a function that returns (value, confidence)
    def classifier(text):
        return ("positive", 0.85)

    backend._callables["python:test.classify"] = classifier
    config = _config(model_id="python:test.classify")
    result = backend.predict("python:test.classify", "great!", config)

    assert result.value == "positive"
    assert result.confidence == 0.85


def test_call_returns_dict_as_record():
    """Python callable returning a dict → Sigil Record."""
    backend = PythonCallableBackend()

    def analyzer(text):
        return {"sentiment": "positive", "score": 0.9}

    backend._callables["python:test.analyze"] = analyzer
    config = _config(model_id="python:test.analyze")
    result = backend.predict("python:test.analyze", "hello", config)

    assert isinstance(result.value, Record)
    assert result.value.fields["sentiment"] == "positive"


def test_call_invalid_path():
    backend = PythonCallableBackend()
    with pytest.raises(ImportError, match="Invalid python callable path"):
        backend.load("python:no_dots")


def test_call_nonexistent_function():
    backend = PythonCallableBackend()
    with pytest.raises(ImportError, match="not found"):
        backend.load("python:math.nonexistent_function_xyz")


def test_call_with_string_input():
    backend = PythonCallableBackend()

    def echo(text):
        return text.upper()

    backend._callables["python:test.echo"] = echo
    config = _config(model_id="python:test.echo")
    result = backend.predict("python:test.echo", "hello", config)
    assert result.value == "HELLO"
