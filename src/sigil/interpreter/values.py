"""Runtime value types for the Sigil interpreter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sigil.ast import nodes as ast
    from sigil.interpreter.environment import Environment


@dataclass(frozen=True)
class Symbol:
    """A symbolic atom like :active, :critical, :approved."""

    name: str

    def __str__(self) -> str:
        return f":{self.name}"

    def __repr__(self) -> str:
        return f"Symbol({self.name!r})"


@dataclass(frozen=True)
class Record:
    """A record value with named fields."""

    type_name: str | None
    fields: dict[str, Value]

    def __str__(self) -> str:
        name = self.type_name or "record"
        inner = ", ".join(f"{k}: {format_value(v)}" for k, v in self.fields.items())
        return f"{name}({inner})"


@dataclass(frozen=True)
class Variant:
    """A sum type variant like 'approved with rate: 5.5'."""

    type_name: str
    variant_name: str
    fields: dict[str, Value] = field(default_factory=dict)

    def __str__(self) -> str:
        if not self.fields:
            return f"{self.type_name}.{self.variant_name}"
        inner = ", ".join(f"{k}: {format_value(v)}" for k, v in self.fields.items())
        return f"{self.type_name}.{self.variant_name}({inner})"


@dataclass(frozen=True)
class Closure:
    """A function value with captured environment."""

    params: tuple[str, ...]
    body: tuple[ast.Statement, ...]
    env: Environment
    name: str | None = None

    def __str__(self) -> str:
        name = self.name or "<anonymous>"
        params = ", ".join(self.params)
        return f"<closure {name}({params})>"

    def __hash__(self) -> int:
        return id(self)


# The Value union — all possible runtime values in Sigil
Value = int | float | str | bool | None | Symbol | Record | Variant | list[Any] | Closure

# Sentinel for unbound variables
_UNBOUND = object()


def format_value(v: Value) -> str:
    """Format a Sigil value for display."""
    if v is None:
        return "none"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, Symbol):
        return str(v)
    if isinstance(v, Record):
        return str(v)
    if isinstance(v, Variant):
        return str(v)
    if isinstance(v, Closure):
        return str(v)
    if isinstance(v, list):
        inner = ", ".join(format_value(x) for x in v)
        return f"[{inner}]"
    return repr(v)


def values_equal(a: Value, b: Value) -> bool:
    """Structural equality for Sigil values."""
    if isinstance(a, Symbol) and isinstance(b, Symbol):
        return a.name == b.name
    if isinstance(a, Record) and isinstance(b, Record):
        return a.fields == b.fields
    if isinstance(a, Variant) and isinstance(b, Variant):
        return a.variant_name == b.variant_name and a.fields == b.fields
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(values_equal(x, y) for x, y in zip(a, b, strict=True))
    return a == b
