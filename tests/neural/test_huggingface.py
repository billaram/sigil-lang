"""Tests for the HuggingFace backend (mocked — no real model downloads)."""

import sys
from unittest.mock import MagicMock

import pytest

from sigil.interpreter.values import Symbol
from sigil.neural.backend import NeuralConfig
from sigil.neural.huggingface import HuggingFaceBackend


def _config(**kwargs) -> NeuralConfig:
    """Helper to create a NeuralConfig with defaults."""
    defaults = {"model_id": "hf:test-model"}
    defaults.update(kwargs)
    return NeuralConfig(**defaults)


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
    result = backend.predict("hf:test-model", "This is great!", _config())
    assert result.value == Symbol("positive")
    assert result.confidence == 0.95
    assert result.model_id == "hf:test-model"
    assert result.latency_ms > 0


def test_predict_normalizes_label(mock_transformers):
    _, mock_pipe = mock_transformers
    mock_pipe.return_value = [{"label": "VERY NEGATIVE", "score": 0.8}]
    backend = HuggingFaceBackend()
    backend.load("hf:test-model")
    result = backend.predict("hf:test-model", "text", _config())
    assert result.value == Symbol("very_negative")


def test_predict_unloaded_model(mock_transformers):
    """Predict on unloaded model auto-loads via _get_or_create_pipeline."""
    _, mock_pipe = mock_transformers
    backend = HuggingFaceBackend()
    # Don't call load — predict should still work via lazy pipeline creation
    result = backend.predict("hf:test-model", "text", _config())
    assert result.value == Symbol("positive")


def test_predict_non_list_result(mock_transformers):
    _, mock_pipe = mock_transformers
    mock_pipe.return_value = "raw string output"
    backend = HuggingFaceBackend()
    backend.load("hf:test-model")
    result = backend.predict("hf:test-model", "text", _config())
    assert result.confidence == 0.0
    assert isinstance(result.value, str)


def test_zero_shot_with_labels(mock_transformers):
    mock_module, _ = mock_transformers
    zs_pipe = MagicMock()
    zs_pipe.return_value = {
        "sequence": "Find the area",
        "labels": ["triangle", "rectangle", "circle"],
        "scores": [0.85, 0.10, 0.05],
    }
    mock_module.pipeline.return_value = zs_pipe

    backend = HuggingFaceBackend()
    config = _config(labels=("triangle", "rectangle", "circle"))
    result = backend.predict("hf:bart-large-mnli", "Find the area", config)

    assert result.value == Symbol("triangle")
    assert result.confidence == 0.85
    assert result.candidates is not None
    assert len(result.candidates) == 3
    assert result.candidates[0].value == Symbol("triangle")
    assert result.candidates[0].score == 0.85
    mock_module.pipeline.assert_called_with("zero-shot-classification", model="bart-large-mnli")


def test_zero_shot_with_hypothesis_template(mock_transformers):
    mock_module, _ = mock_transformers
    zs_pipe = MagicMock()
    zs_pipe.return_value = {
        "sequence": "text",
        "labels": ["positive"],
        "scores": [0.9],
    }
    mock_module.pipeline.return_value = zs_pipe

    backend = HuggingFaceBackend()
    config = _config(
        labels=("positive", "negative"),
        hypothesis_template="This text is {}.",
    )
    result = backend.predict("hf:model", "text", config)

    zs_pipe.assert_called_once_with(
        "text",
        candidate_labels=["positive", "negative"],
        hypothesis_template="This text is {}.",
    )
    assert result.value == Symbol("positive")


def test_zero_shot_candidates_ordered(mock_transformers):
    mock_module, _ = mock_transformers
    zs_pipe = MagicMock()
    zs_pipe.return_value = {
        "sequence": "text",
        "labels": ["algebra", "geometry", "calculus"],
        "scores": [0.6, 0.3, 0.1],
    }
    mock_module.pipeline.return_value = zs_pipe

    backend = HuggingFaceBackend()
    config = _config(labels=("algebra", "geometry", "calculus"))
    result = backend.predict("hf:model", "text", config)

    assert result.candidates is not None
    scores = [c.score for c in result.candidates]
    assert scores == [0.6, 0.3, 0.1]
