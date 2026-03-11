"""Python module importer for Sigil FFI.

Handles `import python X` and `from python X import a, b`.
"""

from __future__ import annotations

import importlib
from typing import Any

from sigil.errors import SigilRuntimeError
from sigil.ffi.errors import translate_python_error
from sigil.ffi.marshal import python_to_sigil, wrap_python_callable
from sigil.interpreter.values import Value


def import_python_module(source: str) -> dict[str, Value]:
    """Import a Python module and marshal its public API into Sigil values.

    Args:
        source: Dotted module path, e.g. "math", "json", "sklearn.ensemble"

    Returns:
        Dictionary of name → Sigil value for the module's public attributes.
    """
    try:
        mod = importlib.import_module(source)
    except ImportError as exc:
        raise SigilRuntimeError(
            f"Cannot import Python module '{source}': {exc}"
        ) from exc
    except Exception as exc:
        raise translate_python_error(exc, f"importing '{source}'") from exc

    return _marshal_module(mod)


def import_python_names(source: str, names: tuple[str, ...]) -> dict[str, Value]:
    """Import specific names from a Python module.

    Args:
        source: Dotted module path.
        names: Attribute names to import.

    Returns:
        Dictionary of name → Sigil value for the requested attributes.
    """
    try:
        mod = importlib.import_module(source)
    except ImportError as exc:
        raise SigilRuntimeError(
            f"Cannot import Python module '{source}': {exc}"
        ) from exc
    except Exception as exc:
        raise translate_python_error(exc, f"importing '{source}'") from exc

    result: dict[str, Value] = {}
    for name in names:
        if not hasattr(mod, name):
            msg = f"Python module '{source}' has no attribute '{name}'"
            raise SigilRuntimeError(msg)
        result[name] = _marshal_attr(getattr(mod, name))
    return result


def _marshal_module(mod: Any) -> dict[str, Value]:
    """Marshal a Python module's public API into Sigil values."""
    result: dict[str, Value] = {}
    # Use __all__ if defined, otherwise non-underscore attributes
    names = getattr(mod, "__all__", None)
    if names is None:
        names = [n for n in dir(mod) if not n.startswith("_")]

    for name in names:
        try:
            attr = getattr(mod, name)
        except Exception:
            continue
        result[name] = _marshal_attr(attr)
    return result


def _marshal_attr(attr: Any) -> Value:
    """Marshal a single Python attribute to a Sigil value."""
    if callable(attr):
        return wrap_python_callable(attr)
    return python_to_sigil(attr)
