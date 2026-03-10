"""Sigil standard library."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sigil.modules.loader import Module


def get_stdlib_module(name: str) -> Module:
    """Get a stdlib module by name."""
    from sigil.modules.loader import Module, SigilImportError
    from sigil.stdlib._builtins import (
        STDLIB_IO,
        STDLIB_LIST,
        STDLIB_LOGIC,
        STDLIB_MATH,
        STDLIB_TEXT,
        STDLIB_TIME,
        STDLIB_TRACE,
    )

    registry = {
        "math": STDLIB_MATH,
        "text": STDLIB_TEXT,
        "list": STDLIB_LIST,
        "logic": STDLIB_LOGIC,
        "time": STDLIB_TIME,
        "trace": STDLIB_TRACE,
        "io": STDLIB_IO,
    }
    if name not in registry:
        msg = f"Unknown stdlib module: sigil.{name}"
        raise SigilImportError(msg)
    return Module.from_builtins(name, registry[name])
