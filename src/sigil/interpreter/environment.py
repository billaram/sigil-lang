"""Immutable environment (scope chain) for the Sigil interpreter."""

from __future__ import annotations

from sigil.interpreter.values import _UNBOUND, Value


class Environment:
    """An immutable binding environment with parent scope chain.

    Lookup walks up the chain. Setting creates a new environment.
    """

    def __init__(
        self,
        bindings: dict[str, Value] | None = None,
        parent: Environment | None = None,
    ) -> None:
        self._bindings: dict[str, Value] = dict(bindings or {})
        self._parent = parent

    def get(self, name: str) -> Value:
        """Look up a name, walking the scope chain. Returns _UNBOUND if not found."""
        if name in self._bindings:
            return self._bindings[name]
        if self._parent is not None:
            return self._parent.get(name)
        return _UNBOUND  # type: ignore[return-value]

    def has(self, name: str) -> bool:
        """Check if a name is bound anywhere in the scope chain."""
        if name in self._bindings:
            return True
        if self._parent is not None:
            return self._parent.has(name)
        return False

    def set(self, name: str, value: Value) -> Environment:
        """Return a NEW environment with this binding added/updated."""
        new_bindings = dict(self._bindings)
        new_bindings[name] = value
        return Environment(new_bindings, self._parent)

    def extend(self, bindings: dict[str, Value]) -> Environment:
        """Return a NEW child environment with the given bindings."""
        return Environment(bindings, parent=self)

    def mutate(self, name: str, value: Value) -> None:
        """Mutate a binding in-place. ONLY for 'becomes' statements in compute blocks."""
        if name in self._bindings:
            self._bindings[name] = value
        elif self._parent is not None:
            self._parent.mutate(name, value)
        else:
            self._bindings[name] = value

    def all_bindings(self) -> dict[str, Value]:
        """Collect all visible bindings (for trace/debugging)."""
        result: dict[str, Value] = {}
        if self._parent is not None:
            result.update(self._parent.all_bindings())
        result.update(self._bindings)
        return result
