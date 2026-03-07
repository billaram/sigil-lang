"""Tests for module loading, caching, and circular dependency detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from sigil.modules.loader import Module, ModuleLoader, SigilImportError
from sigil.modules.resolver import ModuleResolver


@pytest.fixture()
def tmp_project(tmp_path):
    """Create a temporary project with module files."""
    # math_utils.sigil — exports a compute function
    (tmp_path / "math_utils.sigil").write_text("""\
compute double from x: Number returns Number:
  return x * 2

compute triple from x: Number returns Number:
  return x * 3

export double, triple
""")

    # greeter.sigil — exports a compute function (no explicit export)
    (tmp_path / "greeter.sigil").write_text("""\
compute greet from name: Text returns Text:
  return "Hello, " + name
""")

    # constants.sigil — exports constants
    (tmp_path / "constants.sigil").write_text("""\
define MAX as 100
define MIN as 0

export MAX, MIN
""")

    return tmp_path


@pytest.fixture()
def loader(tmp_project):
    stdlib_root = Path(__file__).parent.parent.parent / "src" / "sigil" / "stdlib"
    resolver = ModuleResolver(tmp_project, stdlib_root)
    return ModuleLoader(resolver)


class TestModuleLoading:
    def test_load_sigil_module(self, loader, tmp_project):
        """Load a .sigil file as a module."""
        module = loader.load("math_utils", tmp_project / "main.sigil")
        assert isinstance(module, Module)
        assert "double" in module.exports
        assert "triple" in module.exports

    def test_load_module_without_explicit_exports(self, loader, tmp_project):
        """Module without export declaration exports all compute functions."""
        module = loader.load("greeter", tmp_project / "main.sigil")
        assert "greet" in module.exports

    def test_load_constants_module(self, loader, tmp_project):
        """Module with constant definitions."""
        module = loader.load("constants", tmp_project / "main.sigil")
        assert "MAX" in module.exports
        assert "MIN" in module.exports

    def test_module_caching(self, loader, tmp_project):
        """Loading the same module twice returns cached instance."""
        m1 = loader.load("math_utils", tmp_project / "main.sigil")
        m2 = loader.load("math_utils", tmp_project / "main.sigil")
        assert m1 is m2


class TestCircularDependency:
    def test_circular_import_detected(self, tmp_path):
        """Circular imports should raise SigilImportError."""
        (tmp_path / "a.sigil").write_text("""\
import b

compute fa from x: Number returns Number:
  return x
""")
        (tmp_path / "b.sigil").write_text("""\
import a

compute fb from x: Number returns Number:
  return x
""")
        stdlib_root = Path(__file__).parent.parent.parent / "src" / "sigil" / "stdlib"
        resolver = ModuleResolver(tmp_path, stdlib_root)
        loader = ModuleLoader(resolver)
        with pytest.raises(SigilImportError, match="Circular dependency"):
            loader.load("a", tmp_path / "main.sigil")


class TestStdlibLoading:
    def test_load_stdlib_math(self, loader, tmp_project):
        """Loading sigil.math should return stdlib builtins."""
        module = loader.load("sigil.math", tmp_project / "main.sigil")
        assert "sqrt" in module.exports
        assert "PI" in module.exports

    def test_load_stdlib_text(self, loader, tmp_project):
        module = loader.load("sigil.text", tmp_project / "main.sigil")
        assert "length" in module.exports
        assert "uppercase" in module.exports

    def test_load_stdlib_list(self, loader, tmp_project):
        module = loader.load("sigil.list", tmp_project / "main.sigil")
        assert "range" in module.exports
        assert "reverse" in module.exports

    def test_load_stdlib_logic(self, loader, tmp_project):
        module = loader.load("sigil.logic", tmp_project / "main.sigil")
        assert "xor" in module.exports
        assert "type_of" in module.exports

    def test_unknown_stdlib_module(self, loader, tmp_project):
        with pytest.raises(SigilImportError, match="Unknown stdlib module"):
            loader.load("sigil.nonexistent", tmp_project / "main.sigil")


class TestPythonModuleLoading:
    def test_load_python_math(self, loader, tmp_project):
        """Loading a Python module should wrap its callables."""
        module = loader.load("python math", tmp_project / "main.sigil")
        assert "sqrt" in module.exports
        assert "pi" in module.exports

    def test_python_module_not_found(self, loader, tmp_project):
        with pytest.raises(SigilImportError, match="Python module not found"):
            loader.load("python nonexistent_module_xyz", tmp_project / "main.sigil")


class TestModuleFromBuiltins:
    def test_from_builtins(self):
        """Module.from_builtins creates a module from Python functions."""
        def my_func(args, _trace):
            return args[0] + 1

        bindings = {"my_func": my_func, "MY_CONST": 42}
        module = Module.from_builtins("test", bindings)
        assert "my_func" in module.exports
        assert "MY_CONST" in module.exports
        assert module.path is None
