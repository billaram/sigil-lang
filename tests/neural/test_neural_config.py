"""Tests for NeuralConfig and CandidateResult data classes."""

from sigil.interpreter.values import Symbol
from sigil.neural.backend import CandidateResult, ModelResult, NeuralConfig


def test_neural_config_defaults():
    config = NeuralConfig(model_id="test:model")
    assert config.model_id == "test:model"
    assert config.return_type == "Symbol"
    assert config.confidence_threshold == 0.5
    assert config.labels is None
    assert config.temperature is None
    assert config.num_candidates == 1
    assert config.timeout_seconds == 60.0


def test_neural_config_with_all_fields():
    config = NeuralConfig(
        model_id="hf:bart-large-mnli",
        return_type="Record",
        confidence_threshold=0.8,
        labels=("triangle", "rectangle"),
        hypothesis_template="This is {}.",
        system_prompt="You are a math solver.",
        temperature=0.7,
        max_tokens=100,
        top_p=0.9,
        top_k=50,
        stop_sequences=("END",),
        output_schema="MathResult",
        num_candidates=3,
        beam_size=5,
        timeout_seconds=30.0,
    )
    assert config.labels == ("triangle", "rectangle")
    assert config.system_prompt == "You are a math solver."
    assert config.beam_size == 5


def test_neural_config_is_frozen():
    import pytest
    config = NeuralConfig(model_id="test")
    with pytest.raises(AttributeError):
        config.model_id = "other"  # type: ignore[misc]


def test_candidate_result_creation():
    c = CandidateResult(value=Symbol("triangle"), score=0.85)
    assert c.value == Symbol("triangle")
    assert c.score == 0.85


def test_model_result_with_candidates():
    candidates = (
        CandidateResult(value=Symbol("triangle"), score=0.85),
        CandidateResult(value=Symbol("rectangle"), score=0.10),
    )
    result = ModelResult(
        value=Symbol("triangle"),
        confidence=0.85,
        model_id="hf:model",
        latency_ms=42.0,
        candidates=candidates,
    )
    assert result.candidates is not None
    assert len(result.candidates) == 2
    assert result.candidates[0].score == 0.85
