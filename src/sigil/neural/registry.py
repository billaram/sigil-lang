"""Model registry — maps model IDs to backends."""

from __future__ import annotations

from sigil.interpreter.values import Value
from sigil.neural.backend import ModelBackend, ModelResult


class ModelRegistry:
    """Singleton-style registry mapping model IDs to backends.

    Model ID prefixes route to backends:
    - "hf:*" → HuggingFace backend
    - Custom backends can be registered for any prefix.
    """

    def __init__(self) -> None:
        self._backends: dict[str, ModelBackend] = {}
        self._loaded: set[str] = set()

    def register_backend(self, prefix: str, backend: ModelBackend) -> None:
        """Register a backend for a model ID prefix."""
        self._backends[prefix] = backend

    def predict(self, model_id: str, input_data: Value) -> ModelResult:
        """Look up the backend for a model ID and run inference."""
        backend = self._get_backend(model_id)

        # Lazy-load the model
        if model_id not in self._loaded:
            backend.load(model_id)
            self._loaded.add(model_id)

        return backend.predict(model_id, input_data)

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
    try:
        from sigil.neural.huggingface import HuggingFaceBackend
        registry.register_backend("hf:", HuggingFaceBackend())
    except ImportError:
        pass
