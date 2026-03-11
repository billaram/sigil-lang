"""Anthropic Claude backend for the Sigil neural bridge."""

from __future__ import annotations

import json
import time

from sigil.interpreter.values import Symbol, Value
from sigil.neural.backend import ModelResult, NeuralConfig


class AnthropicBackend:
    """Backend that uses the Anthropic SDK for Claude models.

    Handles ``claude:`` prefix model IDs (e.g., ``claude:claude-sonnet-4-20250514``).
    Requires the ``anthropic`` package and ``ANTHROPIC_API_KEY`` env var.
    """

    def __init__(self) -> None:
        self._client: object | None = None

    def load(self, model_id: str) -> None:
        """Lazy-init the Anthropic client."""
        if self._client is None:
            import anthropic  # type: ignore[import-untyped]
            self._client = anthropic.Anthropic()

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        """Run inference through the Anthropic Messages API."""
        if self._client is None:
            self.load(model_id)

        claude_model = model_id.removeprefix("claude:")

        # Build messages
        messages = [{"role": "user", "content": self._format_input(input_data)}]

        # Build API kwargs
        kwargs: dict[str, object] = {
            "model": claude_model,
            "messages": messages,
            "max_tokens": config.max_tokens or 1024,
        }

        if config.system_prompt is not None:
            kwargs["system"] = config.system_prompt
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.top_k is not None:
            kwargs["top_k"] = config.top_k
        if config.stop_sequences is not None:
            kwargs["stop_sequences"] = list(config.stop_sequences)

        start = time.perf_counter_ns()
        response = self._client.messages.create(**kwargs)  # type: ignore[union-attr]
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        return self._marshal_response(model_id, response, config, latency_ms)

    def _format_input(self, input_data: Value) -> str:
        """Convert Sigil value to text for the user message."""
        if isinstance(input_data, str):
            return input_data
        return str(input_data)

    def _marshal_response(
        self, model_id: str, response: object, config: NeuralConfig, latency_ms: float,
    ) -> ModelResult:
        """Convert Anthropic API response to ModelResult."""
        # Extract text content from response
        text = ""
        content_blocks = getattr(response, "content", [])
        for block in content_blocks:
            if getattr(block, "type", None) == "text":
                text = getattr(block, "text", "")
                break

        # If return type is Record, try to parse JSON
        if config.return_type == "Record":
            return self._parse_structured(model_id, text, latency_ms)

        # Default: return as Symbol (strip whitespace, normalize)
        label = text.strip().lower().replace(" ", "_")
        return ModelResult(
            value=Symbol(label) if label else text,
            confidence=1.0,
            model_id=model_id,
            latency_ms=latency_ms,
        )

    def _parse_structured(self, model_id: str, text: str, latency_ms: float) -> ModelResult:
        """Parse JSON response into a Sigil Record."""
        from sigil.ffi.marshal import python_to_sigil

        # Try to extract JSON from the response
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
            else:
                return ModelResult(
                    value=text,
                    confidence=0.0,
                    model_id=model_id,
                    latency_ms=latency_ms,
                )

        return ModelResult(
            value=python_to_sigil(data),
            confidence=1.0,
            model_id=model_id,
            latency_ms=latency_ms,
        )
