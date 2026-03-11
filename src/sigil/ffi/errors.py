"""Error translation between Python exceptions and Sigil errors."""

from __future__ import annotations

from sigil.errors import SigilRuntimeError


def translate_python_error(exc: Exception, context: str) -> SigilRuntimeError:
    """Wrap a Python exception as a SigilRuntimeError with context."""
    msg = f"Python FFI error {context}: {type(exc).__name__}: {exc}"
    error = SigilRuntimeError(msg)
    error.__cause__ = exc
    return error
