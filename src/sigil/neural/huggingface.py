"""HuggingFace Transformers backend for the Sigil neural bridge."""

from __future__ import annotations

import time

from sigil.interpreter.values import Symbol, Value
from sigil.neural.backend import CandidateResult, ModelResult, NeuralConfig


class HuggingFaceBackend:
    """Backend that uses HuggingFace transformers.pipeline() for inference."""

    def __init__(self) -> None:
        # Cache pipelines by (model_id, task_type) to avoid reloading
        self._pipelines: dict[tuple[str, str], object] = {}

    def _get_or_create_pipeline(self, model_id: str, task: str | None = None) -> object:
        """Get a cached pipeline or create a new one."""
        from transformers import pipeline  # type: ignore[import-untyped]

        hf_model = model_id.removeprefix("hf:")
        cache_key = (model_id, task or "auto")

        if cache_key not in self._pipelines:
            pipe = pipeline(task, model=hf_model) if task else pipeline(model=hf_model)
            self._pipelines[cache_key] = pipe

        return self._pipelines[cache_key]

    def load(self, model_id: str) -> None:
        """Load a HuggingFace model via pipeline()."""
        self._get_or_create_pipeline(model_id)

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        """Run inference through the HuggingFace pipeline."""
        # Marshal input: Sigil value -> Python string for text models
        text_input = str(input_data) if not isinstance(input_data, str) else input_data

        if config.labels is not None:
            return self._predict_zero_shot(model_id, text_input, config)
        return self._predict_classification(model_id, text_input, config)

    def _predict_classification(
        self, model_id: str, text: str, config: NeuralConfig,
    ) -> ModelResult:
        """Standard text-classification pipeline."""
        pipe = self._get_or_create_pipeline(model_id)

        start = time.perf_counter_ns()
        raw_result = pipe(text)  # type: ignore[operator]
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        return self._marshal_result(model_id, raw_result, latency_ms)

    def _predict_zero_shot(self, model_id: str, text: str, config: NeuralConfig) -> ModelResult:
        """Zero-shot classification with candidate labels."""
        pipe = self._get_or_create_pipeline(model_id, task="zero-shot-classification")

        candidate_labels = list(config.labels)  # type: ignore[arg-type]
        kwargs: dict[str, object] = {"candidate_labels": candidate_labels}
        if config.hypothesis_template is not None:
            kwargs["hypothesis_template"] = config.hypothesis_template

        start = time.perf_counter_ns()
        raw_result = pipe(text, **kwargs)  # type: ignore[operator]
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        # raw_result: {"sequence": ..., "labels": [...], "scores": [...]}
        if isinstance(raw_result, dict):
            labels = raw_result.get("labels", [])
            scores = raw_result.get("scores", [])
            if labels and scores:
                top_label = str(labels[0]).lower().replace(" ", "_")
                top_score = float(scores[0])

                candidates = tuple(
                    CandidateResult(
                        value=Symbol(str(lbl).lower().replace(" ", "_")),
                        score=float(sc),
                    )
                    for lbl, sc in zip(labels, scores, strict=False)
                )

                return ModelResult(
                    value=Symbol(top_label),
                    confidence=top_score,
                    model_id=model_id,
                    latency_ms=latency_ms,
                    candidates=candidates,
                )

        # Fallback for unexpected format
        return ModelResult(
            value=str(raw_result),
            confidence=0.0,
            model_id=model_id,
            latency_ms=latency_ms,
        )

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
