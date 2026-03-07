"""Tests for module path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from sigil.modules.resolver import ModuleNotFoundError, ModuleResolver


@pytest.fixture()
def tmp_project(tmp_path):
    """Create a temporary project structure."""
    # Create project files
    (tmp_path / "main.sigil").write_text("main:\n  print(1)\n")
    (tmp_path / "utils.sigil").write_text(
        "compute double from x: Number returns Number:\n  return x * 2\n"
    )
    # Create subdirectory
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "helpers.sigil").write_text(
        "compute add from a: Number, b: Number returns Number:\n"
        "  return a + b\n"
    )
    return tmp_path


@pytest.fixture()
def stdlib_root(tmp_path):
    """Create a temporary stdlib directory."""
    stdlib = tmp_path / "stdlib"
    stdlib.mkdir()
    (stdlib / "math.sigil").write_text("-- math module\n")
    return stdlib


@pytest.fixture()
def resolver(tmp_project, stdlib_root):
    return ModuleResolver(tmp_project, stdlib_root)


class TestStdlibResolution:
    def test_stdlib_file_exists(self, resolver, stdlib_root):
        """sigil.math should resolve to stdlib file if it exists."""
        result = resolver.resolve("sigil.math", Path("test.sigil"))
        assert result.kind == "stdlib"
        assert result.path == stdlib_root / "math.sigil"

    def test_stdlib_builtin(self, resolver):
        """sigil.text should resolve to builtin when no file exists."""
        result = resolver.resolve("sigil.text", Path("test.sigil"))
        assert result.kind == "stdlib_builtin"
        assert result.name == "text"

    def test_stdlib_unknown(self, resolver):
        """sigil.unknown should resolve to builtin (loader handles the error)."""
        result = resolver.resolve("sigil.unknown", Path("test.sigil"))
        assert result.kind == "stdlib_builtin"
        assert result.name == "unknown"


class TestPythonResolution:
    def test_python_module(self, resolver):
        result = resolver.resolve("python math", Path("test.sigil"))
        assert result.kind == "python"
        assert result.name == "math"

    def test_python_dotted_module(self, resolver):
        result = resolver.resolve("python os.path", Path("test.sigil"))
        assert result.kind == "python"
        assert result.name == "os.path"


class TestRelativeResolution:
    def test_relative_import(self, resolver, tmp_project):
        importing_file = tmp_project / "main.sigil"
        result = resolver.resolve("./utils", importing_file)
        assert result.kind == "sigil"
        assert result.path == (tmp_project / "utils.sigil").resolve()

    def test_relative_import_subdirectory(self, resolver, tmp_project):
        importing_file = tmp_project / "main.sigil"
        result = resolver.resolve("./lib/helpers", importing_file)
        assert result.kind == "sigil"
        assert result.path == (tmp_project / "lib" / "helpers.sigil").resolve()

    def test_relative_import_not_found(self, resolver, tmp_project):
        importing_file = tmp_project / "main.sigil"
        with pytest.raises(ModuleNotFoundError, match="Module not found"):
            resolver.resolve("./nonexistent", importing_file)


class TestProjectRelativeResolution:
    def test_dotted_path(self, resolver, tmp_project):
        result = resolver.resolve("lib.helpers", Path("anywhere.sigil"))
        assert result.kind == "sigil"
        assert result.path == (tmp_project / "lib" / "helpers.sigil").resolve()

    def test_simple_name(self, resolver, tmp_project):
        result = resolver.resolve("utils", Path("anywhere.sigil"))
        assert result.kind == "sigil"
        assert result.path == (tmp_project / "utils.sigil").resolve()

    def test_not_found(self, resolver):
        with pytest.raises(ModuleNotFoundError, match="Module not found"):
            resolver.resolve("nonexistent", Path("anywhere.sigil"))


class TestResolutionPriority:
    def test_stdlib_takes_priority(self, resolver, stdlib_root, tmp_project):
        """If both stdlib and project have 'math', stdlib wins."""
        (tmp_project / "math.sigil").write_text("-- project math\n")
        result = resolver.resolve("sigil.math", Path("test.sigil"))
        assert result.kind == "stdlib"
        assert result.path == stdlib_root / "math.sigil"
