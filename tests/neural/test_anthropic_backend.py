"""Tests for the Anthropic Claude backend (mocked — no real API calls)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from sigil.interpreter.values import Record, Symbol
from sigil.neural.backend import NeuralConfig


def _config(**kwargs) -> NeuralConfig:
    defaults = {"model_id": "claude:claude-sonnet-4-20250514"}
    defaults.update(kwargs)
    return NeuralConfig(**defaults)


@pytest.fixture
def mock_anthropic():
    """Mock the anthropic module."""
    mock_client_instance = MagicMock()
    mock_module = MagicMock()
    mock_module.Anthropic.return_value = mock_client_instance

    original = sys.modules.get("anthropic")
    sys.modules["anthropic"] = mock_module
    yield mock_module, mock_client_instance
    if original is not None:
        sys.modules["anthropic"] = original
    else:
        del sys.modules["anthropic"]


def test_load_creates_client(mock_anthropic):
    mock_module, _ = mock_anthropic
    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    backend.load("claude:claude-sonnet-4-20250514")
    mock_module.Anthropic.assert_called_once()


def test_predict_basic_symbol(mock_anthropic):
    _, mock_client = mock_anthropic
    # Mock response
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "positive"
    mock_client.messages.create.return_value = MagicMock(content=[text_block])

    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    result = backend.predict("claude:claude-sonnet-4-20250514", "great movie!", _config())

    assert result.value == Symbol("positive")
    assert result.confidence == 1.0
    assert result.model_id == "claude:claude-sonnet-4-20250514"
    assert result.latency_ms >= 0


def test_predict_structured_record(mock_anthropic):
    _, mock_client = mock_anthropic
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = '{"strategy": "law_of_cosines", "confidence": 0.92}'
    mock_client.messages.create.return_value = MagicMock(content=[text_block])

    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    config = _config(return_type="Record")
    result = backend.predict("claude:model", "solve triangle", config)

    assert isinstance(result.value, Record)
    assert result.value.fields["strategy"] == "law_of_cosines"
    assert result.value.fields["confidence"] == 0.92


def test_predict_with_system_prompt(mock_anthropic):
    _, mock_client = mock_anthropic
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "result"
    mock_client.messages.create.return_value = MagicMock(content=[text_block])

    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    config = _config(system_prompt="You are a math solver.")
    backend.predict("claude:model", "input", config)

    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["system"] == "You are a math solver."


def test_predict_with_temperature(mock_anthropic):
    _, mock_client = mock_anthropic
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "result"
    mock_client.messages.create.return_value = MagicMock(content=[text_block])

    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    config = _config(temperature=0.7)
    backend.predict("claude:model", "input", config)

    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["temperature"] == 0.7


def test_predict_handles_api_error(mock_anthropic):
    _, mock_client = mock_anthropic
    mock_client.messages.create.side_effect = RuntimeError("API rate limited")

    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    with pytest.raises(RuntimeError, match="API rate limited"):
        backend.predict("claude:model", "input", _config())


def test_predict_graceful_without_sdk():
    """Import fails gracefully when anthropic is not installed."""
    original = sys.modules.get("anthropic")
    sys.modules["anthropic"] = None  # type: ignore[assignment] — simulate missing
    try:
        with pytest.raises((ImportError, TypeError)):
            from sigil.neural.anthropic_backend import AnthropicBackend
            backend = AnthropicBackend()
            backend.load("claude:model")
    finally:
        if original is not None:
            sys.modules["anthropic"] = original
        else:
            sys.modules.pop("anthropic", None)


def test_predict_with_stop_sequences(mock_anthropic):
    _, mock_client = mock_anthropic
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "answer"
    mock_client.messages.create.return_value = MagicMock(content=[text_block])

    from sigil.neural.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend()
    config = _config(stop_sequences=("END", "STOP"))
    backend.predict("claude:model", "input", config)

    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["stop_sequences"] == ["END", "STOP"]
