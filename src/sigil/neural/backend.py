"""Model backend protocol and result types for the neural bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sigil.interpreter.values import Value


@dataclass(frozen=True)
class NeuralConfig:
    """Configuration extracted from a neural declaration's fields."""

    model_id: str
    return_type: str = "Symbol"
    confidence_threshold: float = 0.5
    # Zero-shot classification
    labels: tuple[str, ...] | None = None
    hypothesis_template: str | None = None
    # LLM generation
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: tuple[str, ...] | None = None
    output_schema: str | None = None
    # Candidate generation
    num_candidates: int = 1
    beam_size: int | None = None
    # Timeout
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class CandidateResult:
    """A single candidate from multi-candidate generation."""

    value: Value
    score: float


@dataclass(frozen=True)
class ModelResult:
    """Result from a neural model inference."""

    value: Value
    confidence: float
    model_id: str
    latency_ms: float
    candidates: tuple[CandidateResult, ...] | None = None


class ModelBackend(Protocol):
    """Protocol for pluggable neural model backends."""

    def load(self, model_id: str) -> None:
        """Load/initialize a model by its identifier."""
        ...

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        """Run inference and return the result with confidence."""
        ...
