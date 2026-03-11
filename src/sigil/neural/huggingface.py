"""HuggingFace Transformers backend for the Sigil neural bridge."""

from __future__ import annotations

import time

from sigil.interpreter.values import Symbol, Value
from sigil.neural.backend import ModelBackend, ModelResult


class HuggingFaceBackend(ModelBackend):
    """Backend that uses HuggingFace transformers.pipeline() for inference."""

    def __init__(self) -> None:
        self._pipelines: dict[str, object] = {}

    def load(self, model_id: str) -> None:
        """Load a HuggingFace model via pipeline()."""
        from transformers import pipeline  # type: ignore[import-untyped]

        hf_model = model_id.removeprefix("hf:")
        # Auto-detect task from model config
        pipe = pipeline(model=hf_model)
        self._pipelines[model_id] = pipe

    def predict(self, model_id: str, input_data: Value) -> ModelResult:
        """Run inference through the HuggingFace pipeline."""
        pipe = self._pipelines.get(model_id)
        if pipe is None:
            msg = f"Model '{model_id}' not loaded. Call load() first."
            raise RuntimeError(msg)

        # Marshal input: Sigil value → Python string for text models
        text_input = str(input_data) if not isinstance(input_data, str) else input_data

        start = time.perf_counter_ns()
        raw_result = pipe(text_input)  # type: ignore[operator]
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        return self._marshal_result(model_id, raw_result, latency_ms)

    def _marshal_result(
        self, model_id: str, raw_result: object, latency_ms: float,
    ) -> ModelResult:
        """Convert HuggingFace pipeline output to ModelResult."""
        # pipeline() returns list[dict] for classification tasks
        if isinstance(raw_result, list) and raw_result:
            top = raw_result[0]
            if isinstance(top, dict):
                label = top.get("label", "unknown")
                score = float(top.get("score", 0.0))
                return ModelResult(
                    value=Symbol(label.lower().replace(" ", "_")),
                    confidence=score,
                    model_id=model_id,
                    latency_ms=latency_ms,
                )

        # Fallback: wrap raw output
        return ModelResult(
            value=str(raw_result),
            confidence=0.0,
            model_id=model_id,
            latency_ms=latency_ms,
        )
