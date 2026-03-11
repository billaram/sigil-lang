"""OpenAI backend for the Sigil neural bridge."""

from __future__ import annotations

import json
import time

from sigil.interpreter.values import Symbol, Value
from sigil.neural.backend import ModelResult, NeuralConfig


class OpenAIBackend:
    """Backend that uses the OpenAI SDK for GPT models.

    Handles ``openai:`` prefix model IDs (e.g., ``openai:gpt-4o``).
    Requires the ``openai`` package and ``OPENAI_API_KEY`` env var.
    """

    def __init__(self) -> None:
        self._client: object | None = None

    def load(self, model_id: str) -> None:
        """Lazy-init the OpenAI client."""
        if self._client is None:
            import openai  # type: ignore[import-untyped]
            self._client = openai.OpenAI()

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        """Run inference through the OpenAI Chat Completions API."""
        if self._client is None:
            self.load(model_id)

        openai_model = model_id.removeprefix("openai:")

        # Build messages
        messages: list[dict[str, str]] = []
        if config.system_prompt is not None:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": self._format_input(input_data)})

        # Build API kwargs
        kwargs: dict[str, object] = {
            "model": openai_model,
            "messages": messages,
        }

        if config.max_tokens is not None:
            kwargs["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.stop_sequences is not None:
            kwargs["stop"] = list(config.stop_sequences)

        # Request JSON output for structured responses
        if config.return_type == "Record":
            kwargs["response_format"] = {"type": "json_object"}

        start = time.perf_counter_ns()
        response = self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
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
        """Convert OpenAI API response to ModelResult."""
        # Extract text from response
        text = ""
        choices = getattr(response, "choices", [])
        if choices:
            message = getattr(choices[0], "message", None)
            if message:
                text = getattr(message, "content", "") or ""

        # If return type is Record, try to parse JSON
        if config.return_type == "Record":
            return self._parse_structured(model_id, text, latency_ms)

        # Default: return as Symbol
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

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
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
