"""Tests for the OpenAI backend (mocked — no real API calls)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from sigil.interpreter.values import Record, Symbol
from sigil.neural.backend import NeuralConfig


def _config(**kwargs) -> NeuralConfig:
    defaults = {"model_id": "openai:gpt-4o"}
    defaults.update(kwargs)
    return NeuralConfig(**defaults)


@pytest.fixture
def mock_openai():
    """Mock the openai module."""
    mock_client_instance = MagicMock()
    mock_module = MagicMock()
    mock_module.OpenAI.return_value = mock_client_instance

    original = sys.modules.get("openai")
    sys.modules["openai"] = mock_module
    yield mock_module, mock_client_instance
    if original is not None:
        sys.modules["openai"] = original
    else:
        del sys.modules["openai"]


def _mock_response(text: str) -> MagicMock:
    """Create a mock OpenAI response."""
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def test_load_creates_client(mock_openai):
    mock_module, _ = mock_openai
    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    backend.load("openai:gpt-4o")
    mock_module.OpenAI.assert_called_once()


def test_predict_basic_symbol(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.return_value = _mock_response("positive")

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    result = backend.predict("openai:gpt-4o", "great movie!", _config())

    assert result.value == Symbol("positive")
    assert result.confidence == 1.0
    assert result.model_id == "openai:gpt-4o"


def test_predict_structured_record(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.return_value = _mock_response(
        '{"strategy": "law_of_cosines", "confidence": 0.92}'
    )

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    config = _config(return_type="Record")
    result = backend.predict("openai:gpt-4o", "solve triangle", config)

    assert isinstance(result.value, Record)
    assert result.value.fields["strategy"] == "law_of_cosines"


def test_predict_with_system_prompt(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.return_value = _mock_response("result")

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    config = _config(system_prompt="You are a math solver.")
    backend.predict("openai:gpt-4o", "input", config)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a math solver."


def test_predict_with_temperature(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.return_value = _mock_response("result")

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    config = _config(temperature=0.7)
    backend.predict("openai:gpt-4o", "input", config)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["temperature"] == 0.7


def test_predict_handles_api_error(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.side_effect = RuntimeError("Rate limit exceeded")

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    with pytest.raises(RuntimeError, match="Rate limit exceeded"):
        backend.predict("openai:gpt-4o", "input", _config())


def test_predict_graceful_without_sdk():
    """Import fails gracefully when openai is not installed."""
    original = sys.modules.get("openai")
    sys.modules["openai"] = None  # type: ignore[assignment]
    try:
        with pytest.raises((ImportError, TypeError)):
            from sigil.neural.openai_backend import OpenAIBackend
            backend = OpenAIBackend()
            backend.load("openai:gpt-4o")
    finally:
        if original is not None:
            sys.modules["openai"] = original
        else:
            sys.modules.pop("openai", None)


def test_predict_with_stop_sequences(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.return_value = _mock_response("answer")

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    config = _config(stop_sequences=("END", "STOP"))
    backend.predict("openai:gpt-4o", "input", config)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["stop"] == ["END", "STOP"]


def test_predict_requests_json_for_record(mock_openai):
    _, mock_client = mock_openai
    mock_client.chat.completions.create.return_value = _mock_response('{"key": "value"}')

    from sigil.neural.openai_backend import OpenAIBackend
    backend = OpenAIBackend()
    config = _config(return_type="Record")
    backend.predict("openai:gpt-4o", "input", config)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["response_format"] == {"type": "json_object"}
