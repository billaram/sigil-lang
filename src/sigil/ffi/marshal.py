"""Bidirectional type marshaling between Sigil values and Python objects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sigil.errors import SigilRuntimeError
from sigil.interpreter.trace import ProgramTrace
from sigil.interpreter.values import Closure, Record, Symbol, Value


def sigil_to_python(value: Value) -> Any:
    """Convert a Sigil value to a Python object."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, Symbol):
        return value.name
    if isinstance(value, Record):
        return {k: sigil_to_python(v) for k, v in value.fields.items()}
    if isinstance(value, list):
        return [sigil_to_python(item) for item in value]
    if isinstance(value, Closure):
        msg = "Cannot marshal Sigil closures to Python"
        raise SigilRuntimeError(msg)
    return value


def python_to_sigil(obj: Any) -> Value:
    """Convert a Python object to a Sigil value."""
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        fields = {str(k): python_to_sigil(v) for k, v in obj.items()}
        return Record(type_name=None, fields=fields)
    if isinstance(obj, (list, tuple)):
        return [python_to_sigil(item) for item in obj]
    if callable(obj):
        return wrap_python_callable(obj)
    # For other types, convert to string
    return str(obj)


def wrap_python_callable(func: Callable[..., Any]) -> Callable[[list[Value], ProgramTrace], Value]:
    """Wrap a Python function to accept/return Sigil values."""

    def wrapper(args: list[Value], _trace: ProgramTrace) -> Value:
        py_args = [sigil_to_python(a) for a in args]
        try:
            result = func(*py_args)
        except Exception as exc:
            from sigil.ffi.errors import translate_python_error

            name = getattr(func, "__name__", repr(func))
            raise translate_python_error(exc, f"calling {name}") from exc
        return python_to_sigil(result)

    wrapper.__name__ = getattr(func, "__name__", "<python>")
    wrapper._is_python_ffi = True  # type: ignore[attr-defined]
    return wrapper
