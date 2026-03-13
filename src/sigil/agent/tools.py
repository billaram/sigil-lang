"""Tool implementations for the Sigil Code agent."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ToolDef:
    """Anthropic tool_use API definition."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """Result of executing a tool."""

    content: str
    is_error: bool = False


class ToolRegistry:
    """Registry and executor for agent tools."""

    def __init__(self, working_dir: Path) -> None:
        self._working_dir = working_dir.resolve()

    def api_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions for the Anthropic API."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tool_defs()
        ]

    def execute(self, name: str, args: dict[str, Any]) -> str:
        """Execute a tool by name and return result string."""
        dispatch = {
            "validate": self._tool_validate,
            "execute": self._tool_execute,
            "format_code": self._tool_format,
            "write_file": self._tool_write_file,
            "read_file": self._tool_read_file,
            "list_project": self._tool_list_project,
            "scaffold": self._tool_scaffold,
        }
        handler = dispatch.get(name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = handler(args)
            return result.content
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _tool_defs(self) -> list[ToolDef]:
        return [
            ToolDef(
                name="validate",
                description=(
                    "Validate Sigil source code through lexer, parser, and "
                    "type checker. Returns parse errors, type errors, and "
                    "warnings. Always call this before writing files."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Sigil source code to validate",
                        },
                    },
                    "required": ["code"],
                },
            ),
            ToolDef(
                name="execute",
                description=(
                    "Execute Sigil source code and return output. Optionally "
                    "provide input data as a JSON object."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Sigil source code to execute",
                        },
                        "input_data": {
                            "type": "string",
                            "description": (
                                "Optional JSON object with input variable "
                                "bindings"
                            ),
                        },
                    },
                    "required": ["code"],
                },
            ),
            ToolDef(
                name="format_code",
                description="Format Sigil source code using the AST formatter.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Sigil source code to format",
                        },
                    },
                    "required": ["code"],
                },
            ),
            ToolDef(
                name="write_file",
                description=(
                    "Write a file to disk. Path must be relative and within "
                    "the working directory. Validates .sigil files before "
                    "writing."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "Relative file path (must end in .sigil, "
                                ".json, or .md)"
                            ),
                        },
                        "content": {
                            "type": "string",
                            "description": "File content to write",
                        },
                    },
                    "required": ["path", "content"],
                },
            ),
            ToolDef(
                name="read_file",
                description="Read a file from the working directory.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative file path to read",
                        },
                    },
                    "required": ["path"],
                },
            ),
            ToolDef(
                name="list_project",
                description=(
                    "List .sigil files in the working directory."
                ),
                input_schema={
                    "type": "object",
                    "properties": {},
                },
            ),
            ToolDef(
                name="scaffold",
                description=(
                    "Create a project from a template. Templates: "
                    "basic, rules, neural, full."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "template": {
                            "type": "string",
                            "description": (
                                "Template name: basic, rules, neural, or full"
                            ),
                            "enum": ["basic", "rules", "neural", "full"],
                        },
                        "name": {
                            "type": "string",
                            "description": "Project directory name",
                        },
                    },
                    "required": ["template", "name"],
                },
            ),
        ]

    # --- Tool implementations ---

    def _tool_validate(self, args: dict[str, Any]) -> ToolResult:
        from sigil.generator.validator import validate_generated

        code = args["code"]
        result = validate_generated(code)
        data = {
            "valid": result.valid,
            "parse_errors": list(result.parse_errors),
            "type_errors": list(result.type_errors),
            "warnings": list(result.warnings),
        }
        return ToolResult(content=json.dumps(data))

    def _tool_execute(self, args: dict[str, Any]) -> ToolResult:
        code = args["code"]
        input_json = args.get("input_data")

        output_lines: list[str] = []
        error_msg: str | None = None
        result_val: str | None = None

        def _run() -> None:
            nonlocal output_lines, error_msg, result_val
            try:
                from sigil.errors import SigilError
                from sigil.interpreter.evaluator import Evaluator
                from sigil.interpreter.values import format_value
                from sigil.lexer import tokenize
                from sigil.modules.loader import ModuleLoader
                from sigil.modules.resolver import ModuleResolver
                from sigil.parser import parse

                tokens = tokenize(code, "<agent>")
                program = parse(tokens, "<agent>")

                input_data = None
                if input_json:
                    from sigil.cli import _json_to_sigil

                    raw = json.loads(input_json)
                    if isinstance(raw, dict):
                        input_data = {
                            k: _json_to_sigil(v) for k, v in raw.items()
                        }

                stdlib_root = Path(__file__).parent.parent / "stdlib"
                resolver = ModuleResolver(self._working_dir, stdlib_root)
                loader = ModuleLoader(resolver)

                evaluator = Evaluator()
                evaluator.module_loader = loader
                evaluator.filename = "<agent>"

                result, trace = evaluator.eval_program(program, input_data)
                output_lines.extend(trace.output_lines)
                if result is not None and not trace.output_lines:
                    result_val = format_value(result)

            except SigilError as e:
                error_msg = str(e)
            except Exception as e:
                error_msg = f"Unexpected error: {e}"

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=10)

        if thread.is_alive():
            return ToolResult(
                content=json.dumps({"error": "Execution timed out (10s)"}),
                is_error=True,
            )

        data: dict[str, Any] = {"output": output_lines}
        if result_val is not None:
            data["result"] = result_val
        if error_msg is not None:
            data["error"] = error_msg
        return ToolResult(
            content=json.dumps(data),
            is_error=error_msg is not None,
        )

    def _tool_format(self, args: dict[str, Any]) -> ToolResult:
        from sigil.errors import SigilError
        from sigil.formatter import format_program
        from sigil.lexer import tokenize
        from sigil.parser import parse

        code = args["code"]
        try:
            tokens = tokenize(code, "<format>")
            program = parse(tokens, "<format>")
            formatted = format_program(program)
            return ToolResult(
                content=json.dumps({"formatted": formatted}),
            )
        except SigilError as e:
            return ToolResult(
                content=json.dumps({"error": str(e)}),
                is_error=True,
            )

    def _tool_write_file(self, args: dict[str, Any]) -> ToolResult:
        rel_path = args["path"]
        content = args["content"]

        allowed_exts = {".sigil", ".json", ".md"}
        path = Path(rel_path)
        if path.suffix not in allowed_exts:
            return ToolResult(
                content=json.dumps({
                    "error": (
                        f"File must end in one of: "
                        f"{', '.join(sorted(allowed_exts))}"
                    ),
                }),
                is_error=True,
            )

        # Resolve and check path stays within working dir
        full_path = (self._working_dir / rel_path).resolve()
        if not str(full_path).startswith(str(self._working_dir)):
            return ToolResult(
                content=json.dumps({
                    "error": "Path must be within the working directory",
                }),
                is_error=True,
            )

        # Validate .sigil files before writing
        validation_info: dict[str, Any] = {}
        if path.suffix == ".sigil":
            from sigil.generator.validator import validate_generated

            result = validate_generated(content)
            validation_info = {
                "valid": result.valid,
                "parse_errors": list(result.parse_errors),
                "type_errors": list(result.type_errors),
                "warnings": list(result.warnings),
            }

        # Write regardless (agent may want to iterate)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

        data: dict[str, Any] = {
            "written": str(full_path.relative_to(self._working_dir)),
            "bytes": len(content),
        }
        if validation_info:
            data["validation"] = validation_info
        return ToolResult(content=json.dumps(data))

    def _tool_read_file(self, args: dict[str, Any]) -> ToolResult:
        rel_path = args["path"]
        full_path = (self._working_dir / rel_path).resolve()

        if not str(full_path).startswith(str(self._working_dir)):
            return ToolResult(
                content=json.dumps({
                    "error": "Path must be within the working directory",
                }),
                is_error=True,
            )

        if not full_path.exists():
            return ToolResult(
                content=json.dumps({"error": f"File not found: {rel_path}"}),
                is_error=True,
            )

        content = full_path.read_text()
        return ToolResult(
            content=json.dumps({"path": rel_path, "content": content}),
        )

    def _tool_list_project(self, _args: dict[str, Any]) -> ToolResult:
        files = []
        for f in sorted(self._working_dir.rglob("*.sigil")):
            rel = f.relative_to(self._working_dir)
            files.append({
                "path": str(rel),
                "bytes": f.stat().st_size,
            })
        return ToolResult(content=json.dumps({"files": files}))

    def _tool_scaffold(self, args: dict[str, Any]) -> ToolResult:
        from sigil.agent.templates import get_template

        template_name = args["template"]
        project_name = args["name"]

        template = get_template(template_name)
        if template is None:
            return ToolResult(
                content=json.dumps({
                    "error": f"Unknown template: {template_name}",
                }),
                is_error=True,
            )

        project_dir = (self._working_dir / project_name).resolve()
        if not str(project_dir).startswith(str(self._working_dir)):
            return ToolResult(
                content=json.dumps({
                    "error": "Project name must not escape working directory",
                }),
                is_error=True,
            )

        project_dir.mkdir(parents=True, exist_ok=True)
        created = []
        for tf in template.files:
            file_path = project_dir / tf.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(tf.content)
            created.append(str(Path(project_name) / tf.path))

        return ToolResult(
            content=json.dumps({
                "project": project_name,
                "template": template_name,
                "description": template.description,
                "files": created,
            }),
        )
