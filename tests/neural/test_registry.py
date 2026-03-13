"""Tests for the neural model registry."""

import pytest

from sigil.interpreter.values import Symbol
from sigil.neural.backend import ModelResult, NeuralConfig
from sigil.neural.registry import ModelRegistry


class MockBackend:
    """Mock backend for testing."""

    def __init__(self, result_value="mock_result", confidence=0.9):
        self.result_value = result_value
        self.confidence = confidence
        self.loaded: list[str] = []
        self.predict_calls: list[tuple[str, object, NeuralConfig]] = []

    def load(self, model_id: str) -> None:
        self.loaded.append(model_id)

    def predict(self, model_id: str, input_data, config: NeuralConfig) -> ModelResult:
        self.predict_calls.append((model_id, input_data, config))
        return ModelResult(
            value=(
                Symbol(self.result_value)
                if isinstance(self.result_value, str)
                else self.result_value
            ),
            confidence=self.confidence,
            model_id=model_id,
            latency_ms=1.0,
        )


def test_register_and_predict():
    registry = ModelRegistry()
    backend = MockBackend()
    registry.register_backend("test:", backend)

    result = registry.predict("test:my-model", "hello")
    assert result.confidence == 0.9
    assert "test:my-model" in backend.loaded


def test_predict_caches_load():
    registry = ModelRegistry()
    backend = MockBackend()
    registry.register_backend("test:", backend)

    registry.predict("test:model", "a")
    registry.predict("test:model", "b")
    # load() called once, predict() called twice
    assert len(backend.loaded) == 1
    assert len(backend.predict_calls) == 2


def test_no_backend_raises():
    registry = ModelRegistry()
    with pytest.raises(LookupError, match="No backend registered"):
        registry.predict("unknown:model", "data")


def test_has_backend():
    registry = ModelRegistry()
    backend = MockBackend()
    registry.register_backend("hf:", backend)
    assert registry.has_backend("hf:some-model")
    assert not registry.has_backend("other:model")


def test_multiple_backends():
    registry = ModelRegistry()
    hf_backend = MockBackend(result_value="hf_result")
    custom_backend = MockBackend(result_value="custom_result")

    registry.register_backend("hf:", hf_backend)
    registry.register_backend("custom:", custom_backend)

    r1 = registry.predict("hf:model-a", "input")
    r2 = registry.predict("custom:model-b", "input")

    assert r1.value == Symbol("hf_result")
    assert r2.value == Symbol("custom_result")


def test_config_passthrough():
    """Config is forwarded to the backend's predict method."""
    registry = ModelRegistry()
    backend = MockBackend()
    registry.register_backend("test:", backend)

    config = NeuralConfig(
        model_id="test:model",
        labels=("a", "b"),
        temperature=0.7,
    )
    registry.predict("test:model", "input", config)

    assert len(backend.predict_calls) == 1
    _, _, received_config = backend.predict_calls[0]
    assert received_config.labels == ("a", "b")
    assert received_config.temperature == 0.7


def test_default_config_when_none():
    """Registry creates a default NeuralConfig when none is provided."""
    registry = ModelRegistry()
    backend = MockBackend()
    registry.register_backend("test:", backend)

    registry.predict("test:model", "input")  # no config arg

    _, _, received_config = backend.predict_calls[0]
    assert received_config.model_id == "test:model"
    assert received_config.confidence_threshold == 0.5
