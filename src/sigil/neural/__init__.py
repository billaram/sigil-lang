"""Sigil Neural Bridge — pluggable model backends for neural declarations."""

from sigil.neural.backend import CandidateResult, ModelBackend, ModelResult, NeuralConfig
from sigil.neural.mock_backend import MockBackend
from sigil.neural.registry import ModelRegistry

__all__ = [
    "CandidateResult",
    "MockBackend",
    "ModelBackend",
    "ModelRegistry",
    "ModelResult",
    "NeuralConfig",
]
