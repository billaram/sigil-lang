"""Python callable backend for the Sigil neural bridge."""

from __future__ import annotations

import importlib
import time

from sigil.ffi.marshal import python_to_sigil, sigil_to_python
from sigil.interpreter.values import Value
from sigil.neural.backend import ModelResult, NeuralConfig


class PythonCallableBackend:
    """Backend that delegates to arbitrary Python callables.

    Handles ``python:`` prefix model IDs (dotted path to a callable).
    Example: ``python:mypackage.models.classify``

    Convention:
    - The callable receives a single Python argument (marshaled from Sigil).
    - It returns either:
      - A single value (confidence defaults to 1.0)
      - A ``(value, confidence)`` tuple
    """

    def __init__(self) -> None:
        self._callables: dict[str, object] = {}

    def load(self, model_id: str) -> None:
        """Import and resolve the callable."""
        dotted_path = model_id.removeprefix("python:")
        module_path, _, attr_name = dotted_path.rpartition(".")
        if not module_path:
            msg = f"Invalid python callable path: '{dotted_path}'. Expected 'module.function'."
            raise ImportError(msg)

        mod = importlib.import_module(module_path)
        func = getattr(mod, attr_name, None)
        if func is None:
            msg = f"'{attr_name}' not found in module '{module_path}'"
            raise ImportError(msg)
        if not callable(func):
            msg = f"'{dotted_path}' is not callable"
            raise TypeError(msg)

        self._callables[model_id] = func

    def predict(self, model_id: str, input_data: Value, config: NeuralConfig) -> ModelResult:
        """Call the Python function and wrap the result."""
        func = self._callables.get(model_id)
        if func is None:
            self.load(model_id)
            func = self._callables[model_id]

        py_input = sigil_to_python(input_data)

        start = time.perf_counter_ns()
        raw_result = func(py_input)  # type: ignore[operator]
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        # Convention: return (value, confidence) or just value
        if isinstance(raw_result, tuple) and len(raw_result) == 2:
            value, confidence = raw_result
            return ModelResult(
                value=python_to_sigil(value),
                confidence=float(confidence),
                model_id=model_id,
                latency_ms=latency_ms,
            )

        return ModelResult(
            value=python_to_sigil(raw_result),
            confidence=1.0,
            model_id=model_id,
            latency_ms=latency_ms,
        )
