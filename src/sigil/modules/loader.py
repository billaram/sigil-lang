"""Module loading, caching, and circular dependency detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sigil.errors import SigilRuntimeError
from sigil.modules.resolver import ModuleResolver

if TYPE_CHECKING:
    from sigil.interpreter.environment import Environment
    from sigil.interpreter.values import Value


class SigilImportError(SigilRuntimeError):
    """Error during module import."""


@dataclass
class Module:
    """A loaded Sigil module."""

    path: Path | None
    env: Environment
    exports: set[str]
    compute_funcs: dict[str, Any] = field(default_factory=dict)
    type_defs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_builtins(cls, name: str, bindings: dict[str, Any]) -> Module:
        """Create a module from Python builtin functions."""
        from sigil.interpreter.environment import Environment

        env = Environment(bindings)
        return cls(
            path=None,
            env=env,
            exports=set(bindings.keys()),
        )


class ModuleLoader:
    """Loads and caches Sigil modules."""

    def __init__(self, resolver: ModuleResolver) -> None:
        self.resolver = resolver
        self._cache: dict[Path, Module] = {}
        self._loading: set[Path] = set()  # cycle detection

    def load(self, module_path: str, importing_file: Path) -> Module:
        """Load a module by path. Returns cached if already loaded."""
        resolved = self.resolver.resolve(module_path, importing_file)

        if resolved.kind == "python":
            assert resolved.name is not None
            return self._load_python_module(resolved.name)

        if resolved.kind == "stdlib_builtin":
            assert resolved.name is not None
            return self._load_stdlib_builtin(resolved.name)

        # File-based module (sigil or stdlib)
        assert resolved.path is not None
        if resolved.path in self._cache:
            return self._cache[resolved.path]

        if resolved.path in self._loading:
            cycle = " -> ".join(str(p) for p in self._loading)
            msg = f"Circular dependency detected: {cycle} -> {resolved.path}"
            raise SigilImportError(msg)

        return self._load_sigil_file(resolved.path)

    def _load_sigil_file(self, path: Path) -> Module:
        """Load a .sigil file as a module."""
        from sigil.interpreter.environment import Environment
        from sigil.interpreter.evaluator import Evaluator
        from sigil.lexer import tokenize
        from sigil.parser import parse

        self._loading.add(path)
        try:
            source = path.read_text()
            tokens = tokenize(source, str(path))
            program = parse(tokens, str(path))

            # Evaluate the module (creates environment with declarations)
            evaluator = Evaluator()
            evaluator.module_loader = self  # for nested imports
            _, trace = evaluator.eval_program(program)

            # Collect exported names
            exports = evaluator._exports if evaluator._exports else set()

            # If no explicit exports, export all top-level names
            if not exports:
                exports = set(evaluator._compute_funcs.keys())
                for decl in program.declarations:
                    from sigil.ast import nodes as ast
                    if isinstance(decl, ast.ConstDecl):
                        exports.add(decl.name)

            # Build module environment from compute functions + constants
            env = Environment()
            for name in exports:
                if name in evaluator._compute_funcs:
                    from sigil.interpreter.values import Closure
                    decl = evaluator._compute_funcs[name]
                    closure = Closure(
                        params=tuple(p.name for p in decl.params),
                        body=decl.body,
                        env=env,
                        name=name,
                    )
                    env = env.set(name, closure)

            # Also export constants
            module_env = evaluator._module_env
            for name in exports:
                val = module_env.get(name)
                from sigil.interpreter.values import _UNBOUND
                if val is not _UNBOUND:
                    env = env.set(name, val)

            module = Module(
                path=path,
                env=env,
                exports=exports,
                compute_funcs=evaluator._compute_funcs,
                type_defs=evaluator._type_defs,
            )

            self._cache[path] = module
            return module
        finally:
            self._loading.discard(path)

    def _load_python_module(self, name: str) -> Module:
        """Load a Python module and wrap its functions."""
        import importlib

        from sigil.interpreter.environment import Environment

        try:
            py_mod = importlib.import_module(name)
        except ImportError as e:
            msg = f"Python module not found: {name}"
            raise SigilImportError(msg) from e

        bindings: dict[str, Value] = {}
        for attr_name in dir(py_mod):
            if attr_name.startswith("_"):
                continue
            attr = getattr(py_mod, attr_name)
            if callable(attr):
                bindings[attr_name] = _wrap_python_callable(attr)
            elif isinstance(attr, (int, float, str, bool)):
                bindings[attr_name] = attr

        return Module(
            path=None,
            env=Environment(bindings),
            exports=set(bindings.keys()),
        )

    def _load_stdlib_builtin(self, name: str) -> Module:
        """Load a Python-backed stdlib module."""
        from sigil.stdlib import get_stdlib_module
        return get_stdlib_module(name)


def _wrap_python_callable(func: Any) -> Any:
    """Wrap a Python callable for use in Sigil."""
    def wrapper(args: list[Value], _trace: Any) -> Value:
        return func(*args)  # type: ignore[no-any-return]
    return wrapper
