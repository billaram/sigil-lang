"""Tests for the ONNX Runtime backend (mocked — no real models)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from sigil.interpreter.values import Symbol
from sigil.neural.backend import NeuralConfig


def _config(**kwargs) -> NeuralConfig:
    defaults = {"model_id": "onnx:model.onnx"}
    defaults.update(kwargs)
    return NeuralConfig(**defaults)


@pytest.fixture
def mock_onnxruntime():
    """Mock the onnxruntime module."""
    mock_session = MagicMock()
    mock_input = MagicMock()
    mock_input.name = "input"
    mock_session.get_inputs.return_value = [mock_input]

    mock_module = MagicMock()
    mock_module.InferenceSession.return_value = mock_session

    original_ort = sys.modules.get("onnxruntime")
    original_np = sys.modules.get("numpy")
    sys.modules["onnxruntime"] = mock_module

    # Provide a real-ish numpy mock
    np_mock = MagicMock()
    np_mock.float32 = "float32"
    np_mock.array = MagicMock(side_effect=lambda x, dtype=None: MagicMock(
        reshape=MagicMock(return_value=x),
        tolist=MagicMock(return_value=x if isinstance(x, list) else [x]),
    ))
    if original_np is None:
        sys.modules["numpy"] = np_mock

    yield mock_module, mock_session
    if original_ort is not None:
        sys.modules["onnxruntime"] = original_ort
    else:
        del sys.modules["onnxruntime"]
    if original_np is None:
        del sys.modules["numpy"]


def test_load_creates_session(mock_onnxruntime):
    mock_module, _ = mock_onnxruntime
    from sigil.neural.onnx_backend import ONNXBackend
    backend = ONNXBackend()
    backend.load("onnx:path/to/model.onnx")
    mock_module.InferenceSession.assert_called_once_with("path/to/model.onnx")


def test_predict_runs_session(mock_onnxruntime):
    _, mock_session = mock_onnxruntime
    mock_session.run.return_value = [[[0.1, 0.9]]]

    from sigil.neural.onnx_backend import ONNXBackend
    backend = ONNXBackend()
    config = _config(labels=("negative", "positive"))
    result = backend.predict("onnx:model.onnx", 1.0, config)

    assert result.value == Symbol("positive")
    assert result.confidence == 0.9


def test_predict_without_labels(mock_onnxruntime):
    _, mock_session = mock_onnxruntime
    mock_session.run.return_value = [[[0.3, 0.7]]]

    from sigil.neural.onnx_backend import ONNXBackend
    backend = ONNXBackend()
    config = _config()
    result = backend.predict("onnx:model.onnx", 1.0, config)

    # Without labels, returns index as string
    assert result.value == Symbol("1")


def test_predict_single_value(mock_onnxruntime):
    _, mock_session = mock_onnxruntime
    mock_session.run.return_value = [[42.0]]

    from sigil.neural.onnx_backend import ONNXBackend
    backend = ONNXBackend()
    result = backend.predict("onnx:model.onnx", 1.0, _config())

    assert result.value == 42.0
