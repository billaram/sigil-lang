"""Model registry — maps model IDs to backends."""

from __future__ import annotations

import threading

from sigil.interpreter.values import Value
from sigil.neural.backend import ModelBackend, ModelResult, NeuralConfig


class ModelRegistry:
    """Singleton-style registry mapping model IDs to backends.

    Model ID prefixes route to backends:
    - "hf:*" → HuggingFace backend
    - "mock:*" → Mock backend (always available)
    - Custom backends can be registered for any prefix.
    """

    def __init__(self) -> None:
        self._backends: dict[str, ModelBackend] = {}
        self._loaded: set[str] = set()

    def register_backend(self, prefix: str, backend: ModelBackend) -> None:
        """Register a backend for a model ID prefix."""
        self._backends[prefix] = backend

    def predict(
        self, model_id: str, input_data: Value, config: NeuralConfig | None = None,
    ) -> ModelResult:
        """Look up the backend for a model ID and run inference with timeout."""
        backend = self._get_backend(model_id)

        # Lazy-load the model
        if model_id not in self._loaded:
            backend.load(model_id)
            self._loaded.add(model_id)

        if config is None:
            config = NeuralConfig(model_id=model_id)

        return self._predict_with_timeout(backend, model_id, input_data, config)

    def _predict_with_timeout(
        self,
        backend: ModelBackend,
        model_id: str,
        input_data: Value,
        config: NeuralConfig,
    ) -> ModelResult:
        """Run backend.predict with timeout enforcement."""
        timeout = config.timeout_seconds

        result_holder: list[ModelResult] = []
        exc_holder: list[Exception] = []

        def _run() -> None:
            try:
                result_holder.append(backend.predict(model_id, input_data, config))
            except Exception as e:
                exc_holder.append(e)

        thread = threading.Thread(target=_run)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            msg = f"Neural inference timed out after {timeout}s for model '{model_id}'"
            raise TimeoutError(msg)
        if exc_holder:
            raise exc_holder[0]
        return result_holder[0]

    def _get_backend(self, model_id: str) -> ModelBackend:
        """Find the backend for a model ID by prefix match."""
        for prefix, backend in self._backends.items():
            if model_id.startswith(prefix):
                return backend
        msg = (
            f"No backend registered for model '{model_id}'. "
            "Register a backend with a matching prefix."
        )
        raise LookupError(msg)

    def has_backend(self, model_id: str) -> bool:
        """Check if a backend exists for this model ID."""
        return any(model_id.startswith(prefix) for prefix in self._backends)


# Global registry instance
_global_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get (or create) the global model registry."""
    global _global_registry  # noqa: PLW0603
    if _global_registry is None:
        _global_registry = ModelRegistry()
        _try_register_defaults(_global_registry)
    return _global_registry


def _try_register_defaults(registry: ModelRegistry) -> None:
    """Register default backends if their dependencies are available."""
    # Mock backend — always available
    from sigil.neural.mock_backend import MockBackend
    registry.register_backend("mock:", MockBackend())

    # HuggingFace — requires transformers
    try:
        from sigil.neural.huggingface import HuggingFaceBackend
        registry.register_backend("hf:", HuggingFaceBackend())
    except ImportError:
        pass

    # Anthropic Claude — requires anthropic SDK
    try:
        import anthropic  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        anthropic = None  # type: ignore[assignment]
    if anthropic is not None:
        from sigil.neural.anthropic_backend import AnthropicBackend
        registry.register_backend("claude:", AnthropicBackend())

    # OpenAI — requires openai SDK
    try:
        import openai  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        openai = None  # type: ignore[assignment]
    if openai is not None:
        from sigil.neural.openai_backend import OpenAIBackend
        registry.register_backend("openai:", OpenAIBackend())

    # ONNX Runtime — requires onnxruntime
    try:
        import onnxruntime  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        onnxruntime = None  # type: ignore[assignment]
    if onnxruntime is not None:
        from sigil.neural.onnx_backend import ONNXBackend
        registry.register_backend("onnx:", ONNXBackend())

    # Python callable — always available
    from sigil.neural.python_callable import PythonCallableBackend
    registry.register_backend("python:", PythonCallableBackend())
