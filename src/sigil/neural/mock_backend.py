"""Deterministic mock backend for testing neural declarations."""

from __future__ import annotations

from sigil.interpreter.values import Symbol, Value
from sigil.neural.backend import CandidateResult, ModelResult, NeuralConfig


class MockBackend:
    """Mock backend for testing — always available, no optional deps.

    Model ID patterns:
    - ``mock:echo``          — returns input as Symbol, confidence 1.0
    - ``mock:fail``          — raises RuntimeError
    - ``mock:low_confidence`` — returns result with confidence 0.1
    - ``mock:fixed:<value>`` — returns specified value as Symbol, confidence 1.0
    """

    def load(self, model_id: str) -> None:
        pass

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        suffix = model_id.removeprefix("mock:")

        if suffix == "fail":
            msg = "Mock model intentionally failed"
            raise RuntimeError(msg)

        if suffix == "low_confidence":
            return ModelResult(
                value=Symbol("low_conf_result"),
                confidence=0.1,
                model_id=model_id,
                latency_ms=0.0,
            )

        if suffix.startswith("fixed:"):
            fixed_value = suffix.removeprefix("fixed:")
            return ModelResult(
                value=Symbol(fixed_value),
                confidence=1.0,
                model_id=model_id,
                latency_ms=0.0,
            )

        # Default: echo — return input as symbol
        text = str(input_data) if not isinstance(input_data, str) else input_data
        label = text.lower().replace(" ", "_")

        candidates = None
        if config.num_candidates > 1:
            candidates = tuple(
                CandidateResult(value=Symbol(f"{label}_{i}"), score=1.0 - i * 0.1)
                for i in range(config.num_candidates)
            )

        return ModelResult(
            value=Symbol(label),
            confidence=1.0,
            model_id=model_id,
            latency_ms=0.0,
            candidates=candidates,
        )
