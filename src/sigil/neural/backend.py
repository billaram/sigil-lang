"""Model backend protocol and result type for the neural bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sigil.interpreter.values import Value


@dataclass(frozen=True)
class ModelResult:
    """Result from a neural model inference."""

    value: Value
    confidence: float
    model_id: str
    latency_ms: float


class ModelBackend(Protocol):
    """Protocol for pluggable neural model backends."""

    def load(self, model_id: str) -> None:
        """Load/initialize a model by its identifier."""
        ...

    def predict(self, model_id: str, input_data: Value) -> ModelResult:
        """Run inference and return the result with confidence."""
        ...
