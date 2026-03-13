"""Tests for Sigil Code agent tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sigil.agent.tools import ToolRegistry


@pytest.fixture()
def registry(tmp_path: Path) -> ToolRegistry:
    return ToolRegistry(tmp_path)


# --- validate tool ---


class TestValidateTool:
    def test_valid_code(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("validate", {
            "code": "define X as 42\n",
        }))
        assert result["valid"] is True
        assert result["parse_errors"] == []

    def test_invalid_code(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("validate", {
            "code": "this is not valid sigil code!!!",
        }))
        assert result["valid"] is False
        assert len(result["parse_errors"]) > 0

    def test_valid_rule(self, registry: ToolRegistry) -> None:
        code = (
            "rule test with priority 1:\n"
            "  given x from input\n"
            "  when x exceeds 10\n"
            '  then trigger alert\n'
            '  explain "x is high"\n'
        )
        result = json.loads(registry.execute("validate", {"code": code}))
        assert result["valid"] is True

    def test_valid_compute(self, registry: ToolRegistry) -> None:
        code = (
            "compute add from a: Number, b: Number returns Number:\n"
            "  return a + b\n"
        )
        result = json.loads(registry.execute("validate", {"code": code}))
        assert result["valid"] is True

    def test_type_errors_reported(self, registry: ToolRegistry) -> None:
        code = (
            "compute foo from x: Number returns Number:\n"
            "  return undefined_var\n"
        )
        result = json.loads(registry.execute("validate", {"code": code}))
        # Type checker should flag undefined variable
        assert len(result["type_errors"]) > 0 or len(result["warnings"]) > 0


# --- execute tool ---


class TestExecuteTool:
    def test_execute_simple(self, registry: ToolRegistry) -> None:
        code = 'main:\n  print("hello")\n'
        result = json.loads(registry.execute("execute", {"code": code}))
        assert "hello" in result["output"]

    def test_execute_with_input(self, registry: ToolRegistry) -> None:
        code = (
            "main:\n"
            "  given x from input\n"
            "  given doubled as x * 2\n"
            "  print(doubled)\n"
        )
        result = json.loads(registry.execute("execute", {
            "code": code,
            "input_data": '{"x": 21}',
        }))
        assert "42" in " ".join(result["output"])

    def test_execute_runtime_error(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("execute", {
            "code": "this is broken!!!",
        }))
        assert "error" in result

    def test_execute_define_and_rule(self, registry: ToolRegistry) -> None:
        code = (
            "define LIMIT as 100\n\n"
            "rule check with priority 1:\n"
            "  when value exceeds LIMIT\n"
            '  then trigger alert\n'
            '  explain "over limit"\n'
        )
        result = json.loads(registry.execute("execute", {
            "code": code,
            "input_data": '{"value": 150}',
        }))
        assert "error" not in result or result["error"] is None


# --- format_code tool ---


class TestFormatTool:
    def test_format_valid(self, registry: ToolRegistry) -> None:
        code = "define X as 42\n"
        result = json.loads(registry.execute("format_code", {"code": code}))
        assert "formatted" in result
        assert "42" in result["formatted"]

    def test_format_invalid(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("format_code", {
            "code": "not valid!!!",
        }))
        assert "error" in result


# --- write_file tool ---


class TestWriteFileTool:
    def test_write_sigil_file(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        result = json.loads(registry.execute("write_file", {
            "path": "test.sigil",
            "content": "define X as 42\n",
        }))
        assert "written" in result
        assert (tmp_path / "test.sigil").exists()

    def test_write_json_file(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        result = json.loads(registry.execute("write_file", {
            "path": "data.json",
            "content": '{"key": "value"}',
        }))
        assert "written" in result

    def test_reject_bad_extension(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("write_file", {
            "path": "script.py",
            "content": "print('hi')",
        }))
        assert "error" in result

    def test_reject_path_traversal(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("write_file", {
            "path": "../../etc/passwd",
            "content": "nope",
        }))
        assert "error" in result

    def test_write_validates_sigil(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        result = json.loads(registry.execute("write_file", {
            "path": "test.sigil",
            "content": "define X as 42\n",
        }))
        assert result["validation"]["valid"] is True

    def test_write_subdirectory(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        result = json.loads(registry.execute("write_file", {
            "path": "sub/test.sigil",
            "content": "define X as 42\n",
        }))
        assert "written" in result
        assert (tmp_path / "sub" / "test.sigil").exists()


# --- read_file tool ---


class TestReadFileTool:
    def test_read_existing(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        (tmp_path / "hello.sigil").write_text("define X as 1\n")
        result = json.loads(registry.execute("read_file", {
            "path": "hello.sigil",
        }))
        assert "define X as 1" in result["content"]

    def test_read_missing(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("read_file", {
            "path": "nope.sigil",
        }))
        assert "error" in result


# --- list_project tool ---


class TestListProjectTool:
    def test_empty_dir(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("list_project", {}))
        assert result["files"] == []

    def test_with_files(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        (tmp_path / "a.sigil").write_text("define A as 1\n")
        (tmp_path / "b.sigil").write_text("define B as 2\n")
        result = json.loads(registry.execute("list_project", {}))
        paths = [f["path"] for f in result["files"]]
        assert "a.sigil" in paths
        assert "b.sigil" in paths


# --- scaffold tool ---


class TestScaffoldTool:
    def test_basic_template(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        result = json.loads(registry.execute("scaffold", {
            "template": "basic",
            "name": "my-project",
        }))
        assert result["template"] == "basic"
        assert (tmp_path / "my-project" / "main.sigil").exists()

    def test_full_template(
        self, registry: ToolRegistry, tmp_path: Path,
    ) -> None:
        result = json.loads(registry.execute("scaffold", {
            "template": "full",
            "name": "full-proj",
        }))
        files = result["files"]
        assert any("main.sigil" in f for f in files)
        assert any("types.sigil" in f for f in files)
        assert any("input.json" in f for f in files)

    def test_unknown_template(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("scaffold", {
            "template": "nonexistent",
            "name": "proj",
        }))
        assert "error" in result


# --- unknown tool ---


class TestUnknownTool:
    def test_unknown_tool(self, registry: ToolRegistry) -> None:
        result = json.loads(registry.execute("unknown_tool", {}))
        assert "error" in result
