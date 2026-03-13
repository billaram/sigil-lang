"""ONNX Runtime backend for the Sigil neural bridge."""

from __future__ import annotations

import time

from sigil.interpreter.values import Symbol, Value
from sigil.neural.backend import ModelResult, NeuralConfig


class ONNXBackend:
    """Backend that uses ONNX Runtime for local model inference.

    Handles ``onnx:`` prefix model IDs where the suffix is a path to an .onnx file.
    Requires the ``onnxruntime`` package.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, object] = {}

    def load(self, model_id: str) -> None:
        """Load an ONNX model file into an InferenceSession."""
        import onnxruntime as ort  # type: ignore[import-untyped]

        model_path = model_id.removeprefix("onnx:")
        self._sessions[model_id] = ort.InferenceSession(model_path)

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        """Run inference through ONNX Runtime."""
        import numpy as np  # type: ignore[import-untyped]

        session = self._sessions.get(model_id)
        if session is None:
            self.load(model_id)
            session = self._sessions[model_id]

        # Marshal input to numpy array
        if isinstance(input_data, (list, tuple)):
            input_array = np.array(input_data, dtype=np.float32)
        elif isinstance(input_data, (int, float)):
            input_array = np.array([input_data], dtype=np.float32)
        elif isinstance(input_data, str):
            input_array = np.array([input_data])
        else:
            input_array = np.array([str(input_data)])

        # Get input name from model
        input_name = session.get_inputs()[0].name  # type: ignore[union-attr]
        input_array = input_array.reshape(1, -1)

        start = time.perf_counter_ns()
        outputs = session.run(None, {input_name: input_array})  # type: ignore[union-attr]
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        # Marshal output
        if outputs and len(outputs) > 0:
            raw = outputs[0]
            if hasattr(raw, "tolist"):
                raw = raw.tolist()

            # If it's a classification output (list of scores), take argmax
            if isinstance(raw, list) and raw and isinstance(raw[0], list):
                scores = raw[0]
                idx = scores.index(max(scores))
                confidence = float(max(scores))
                if config.labels and idx < len(config.labels):
                    label = config.labels[idx]
                else:
                    label = str(idx)
                return ModelResult(
                    value=Symbol(label),
                    confidence=confidence,
                    model_id=model_id,
                    latency_ms=latency_ms,
                )

            # Single value output
            if isinstance(raw, list) and len(raw) == 1:
                raw = raw[0]

            return ModelResult(
                value=raw if isinstance(raw, (int, float, str)) else str(raw),
                confidence=1.0,
                model_id=model_id,
                latency_ms=latency_ms,
            )

        return ModelResult(
            value=None,
            confidence=0.0,
            model_id=model_id,
            latency_ms=latency_ms,
        )
