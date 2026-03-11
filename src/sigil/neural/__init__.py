"""Sigil Neural Bridge — pluggable model backends for neural declarations."""

from sigil.neural.backend import ModelBackend, ModelResult
from sigil.neural.registry import ModelRegistry

__all__ = [
    "ModelBackend",
    "ModelRegistry",
    "ModelResult",
]
