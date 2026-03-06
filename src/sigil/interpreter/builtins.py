"""Built-in functions and actions for the Sigil interpreter."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from sigil.interpreter.values import Value, format_value

if TYPE_CHECKING:
    from sigil.interpreter.trace import ProgramTrace

BuiltinFn = Callable[["list[Value]", "ProgramTrace"], Value]


def builtin_print(args: list[Value], trace: ProgramTrace) -> Value:
    """Print a value to stdout."""
    text = " ".join(format_value(a) if not isinstance(a, str) else a for a in args)
    trace.output_lines.append(text)
    return None


def builtin_max(args: list[Value], _trace: ProgramTrace) -> Value:
    """Return the maximum of two numbers."""
    if len(args) != 2:
        msg = f"math.max expects 2 arguments, got {len(args)}"
        raise RuntimeError(msg)
    a, b = args
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        msg = f"math.max expects numbers, got {type(a).__name__} and {type(b).__name__}"
        raise RuntimeError(msg)
    return max(a, b)


def builtin_min(args: list[Value], _trace: ProgramTrace) -> Value:
    """Return the minimum of two numbers."""
    if len(args) != 2:
        msg = f"math.min expects 2 arguments, got {len(args)}"
        raise RuntimeError(msg)
    a, b = args
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        msg = f"math.min expects numbers, got {type(a).__name__} and {type(b).__name__}"
        raise RuntimeError(msg)
    return min(a, b)


def builtin_len(args: list[Value], _trace: ProgramTrace) -> Value:
    """Return the length of a list or string."""
    if len(args) != 1:
        msg = f"len expects 1 argument, got {len(args)}"
        raise RuntimeError(msg)
    v = args[0]
    if isinstance(v, (list, str)):
        return len(v)
    msg = f"len expects a list or text, got {type(v).__name__}"
    raise RuntimeError(msg)


# Registry of built-in functions
BUILTINS: dict[str, BuiltinFn] = {
    "print": builtin_print,
    "max": builtin_max,
    "min": builtin_min,
    "len": builtin_len,
}

# Dotted path builtins (e.g. math.max)
DOTTED_BUILTINS: dict[str, BuiltinFn] = {
    "math.max": builtin_max,
    "math.min": builtin_min,
    "math.len": builtin_len,
}
