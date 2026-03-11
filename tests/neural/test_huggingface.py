"""Tests for the HuggingFace backend (mocked — no real model downloads)."""

import sys
from unittest.mock import MagicMock

import pytest

from sigil.interpreter.values import Symbol
from sigil.neural.huggingface import HuggingFaceBackend


@pytest.fixture
def mock_transformers():
    """Mock the transformers module to avoid real model downloads."""
    mock_pipe_instance = MagicMock()
    mock_pipe_instance.return_value = [{"label": "POSITIVE", "score": 0.95}]

    mock_module = MagicMock()
    mock_module.pipeline.return_value = mock_pipe_instance

    original = sys.modules.get("transformers")
    sys.modules["transformers"] = mock_module
    yield mock_module, mock_pipe_instance
    if original is not None:
        sys.modules["transformers"] = original
    else:
        del sys.modules["transformers"]


def test_load_creates_pipeline(mock_transformers):
    mock_module, _ = mock_transformers
    backend = HuggingFaceBackend()
    backend.load("hf:distilbert-base-uncased-finetuned-sst-2-english")
    mock_module.pipeline.assert_called_once_with(
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )


def test_predict_returns_model_result(mock_transformers):
    _, mock_pipe = mock_transformers
    backend = HuggingFaceBackend()
    backend.load("hf:test-model")
    result = backend.predict("hf:test-model", "This is great!")
    assert result.value == Symbol("positive")
    assert result.confidence == 0.95
    assert result.model_id == "hf:test-model"
    assert result.latency_ms > 0


def test_predict_normalizes_label(mock_transformers):
    _, mock_pipe = mock_transformers
    mock_pipe.return_value = [{"label": "VERY NEGATIVE", "score": 0.8}]
    backend = HuggingFaceBackend()
    backend.load("hf:test-model")
    result = backend.predict("hf:test-model", "text")
    assert result.value == Symbol("very_negative")


def test_predict_unloaded_model():
    backend = HuggingFaceBackend()
    with pytest.raises(RuntimeError, match="not loaded"):
        backend.predict("hf:missing", "text")


def test_predict_non_list_result(mock_transformers):
    _, mock_pipe = mock_transformers
    mock_pipe.return_value = "raw string output"
    backend = HuggingFaceBackend()
    backend.load("hf:test-model")
    result = backend.predict("hf:test-model", "text")
    assert result.confidence == 0.0
    assert isinstance(result.value, str)
