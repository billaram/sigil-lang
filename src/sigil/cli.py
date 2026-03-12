"""Sigil command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sigil.interpreter.values import Value


def _cmd_lex(file: Path) -> None:
    """Dump the token stream for a .sigil file."""
    from sigil.errors import SigilError
    from sigil.lexer import tokenize

    if not file.exists():
        print(f"[sigil] Error: file not found: {file}", file=sys.stderr)
        sys.exit(1)

    source = file.read_text()
    try:
        tokens = tokenize(source, str(file))
    except SigilError as e:
        print(f"[sigil] Lex error: {e}", file=sys.stderr)
        sys.exit(1)

    for token in tokens:
        print(f"  {token.line:4d}:{token.column:<3d}  {token.type.name:<14s}  {token.value!r}")


def _cmd_parse_ast(file: Path) -> None:
    """Dump the AST for a .sigil file."""
    from sigil.ast import dump
    from sigil.errors import SigilError
    from sigil.lexer import tokenize
    from sigil.parser import parse

    if not file.exists():
        print(f"[sigil] Error: file not found: {file}", file=sys.stderr)
        sys.exit(1)

    source = file.read_text()
    try:
        tokens = tokenize(source, str(file))
        program = parse(tokens, str(file))
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(dump(program))


def _cmd_check(file: Path, *, warnings_as_errors: bool = False) -> None:
    """Type-check a .sigil file."""
    from sigil.errors import SigilError, SigilParseErrors
    from sigil.lexer import tokenize
    from sigil.parser import parse
    from sigil.types.checker import Severity, check

    if not file.exists():
        print(f"[sigil] Error: file not found: {file}", file=sys.stderr)
        sys.exit(1)

    source = file.read_text()
    try:
        tokens = tokenize(source, str(file))
        program = parse(tokens, str(file))
    except SigilParseErrors as e:
        for err in e.errors:
            print(f"[sigil] Error: {err}", file=sys.stderr)
        print(
            f"\n{len(e.errors)} parse error(s) found",
            file=sys.stderr,
        )
        sys.exit(1)
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = check(program)

    for diag in result.diagnostics:
        severity = "error" if diag.severity == Severity.ERROR else "warning"
        print(f"{diag.location}: {severity}: {diag.message}")
        if diag.suggestion:
            print(f"  hint: {diag.suggestion}")

    has_failure = result.has_errors
    if warnings_as_errors and result.warning_count > 0:
        has_failure = True

    if has_failure:
        total = result.error_count + (
            result.warning_count if warnings_as_errors else 0
        )
        print(
            f"\n{result.error_count} error(s),"
            f" {result.warning_count} warning(s)",
        )
        sys.exit(1 if total > 0 else 0)
    elif result.warning_count > 0:
        print(f"\n{result.warning_count} warning(s)")
    else:
        print(f"[sigil] {file}: no issues found")


def _cmd_lint(file: Path, *, strict: bool = False) -> None:
    """Lint a .sigil file."""
    from sigil.errors import SigilError
    from sigil.lexer import tokenize
    from sigil.linter import lint
    from sigil.parser import parse
    from sigil.types.checker import Severity

    if not file.exists():
        print(f"[sigil] Error: file not found: {file}", file=sys.stderr)
        sys.exit(1)

    source = file.read_text()
    try:
        tokens = tokenize(source, str(file))
        program = parse(tokens, str(file))
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = lint(program)

    for diag in result.diagnostics:
        severity = "error" if diag.severity == Severity.ERROR else "warning"
        print(f"{diag.location}: {severity}: {diag.message}")
        if diag.suggestion:
            print(f"  hint: {diag.suggestion}")

    has_failure = result.has_errors or (strict and result.warning_count > 0)
    total = result.error_count + result.warning_count
    if has_failure:
        print(
            f"\n{result.error_count} error(s),"
            f" {result.warning_count} warning(s)",
        )
        sys.exit(1)
    elif total > 0:
        print(f"\n{result.warning_count} warning(s)")
    else:
        print(f"[sigil] {file}: no issues found")


def _cmd_fmt(file: Path, *, check: bool = False) -> None:
    """Format a .sigil file."""
    from sigil.errors import SigilError
    from sigil.formatter import format_program
    from sigil.lexer import tokenize
    from sigil.parser import parse

    if not file.exists():
        print(f"[sigil] Error: file not found: {file}", file=sys.stderr)
        sys.exit(1)

    source = file.read_text()
    try:
        tokens = tokenize(source, str(file))
        program = parse(tokens, str(file))
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    formatted = format_program(program)

    if check:
        if source.rstrip() != formatted.rstrip():
            print(f"[sigil] {file}: needs formatting")
            sys.exit(1)
        print(f"[sigil] {file}: already formatted")
    else:
        print(formatted, end="")


def _cmd_generate(text: str, *, interactive: bool = False) -> None:
    """Generate Sigil code from a natural language description."""
    try:
        if interactive:
            from sigil.generator.interactive import interactive_generate

            result = interactive_generate(text)
        else:
            from sigil.generator import SigilGenerator

            generator = SigilGenerator()
            result = generator.generate(text)
    except ImportError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[sigil] Generation error: {e}", file=sys.stderr)
        sys.exit(1)

    print(result.code, end="")

    if result.valid:
        print("\n-- [sigil] Generated code is valid.", file=sys.stderr)
    else:
        print("\n-- [sigil] Generated code has issues:", file=sys.stderr)
        for diag in result.diagnostics:
            print(f"--   {diag}", file=sys.stderr)


def _cmd_run(file: Path, *, trace: bool = False, input_json: str | None = None) -> None:
    """Run a .sigil program."""
    import json

    from sigil.errors import SigilError, SigilParseErrors
    from sigil.interpreter.trace import format_trace
    from sigil.lexer import tokenize
    from sigil.parser import parse

    if not file.exists():
        print(f"[sigil] Error: file not found: {file}", file=sys.stderr)
        sys.exit(1)

    source = file.read_text()
    try:
        tokens = tokenize(source, str(file))
        program = parse(tokens, str(file))
    except SigilParseErrors as e:
        for err in e.errors:
            print(f"[sigil] Error: {err}", file=sys.stderr)
        print(
            f"\n{len(e.errors)} parse error(s) found",
            file=sys.stderr,
        )
        sys.exit(1)
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse input data — top-level must be a dict of variable bindings
    input_data: dict[str, Value] | None = None
    if input_json:
        raw = json.loads(input_json)
        if not isinstance(raw, dict):
            print("[sigil] Error: --input must be a JSON object", file=sys.stderr)
            sys.exit(1)
        input_data = {k: _json_to_sigil(v) for k, v in raw.items()}

    # Configure module loader
    from sigil.interpreter.evaluator import Evaluator
    from sigil.modules.loader import ModuleLoader
    from sigil.modules.resolver import ModuleResolver

    project_root = file.resolve().parent
    stdlib_root = Path(__file__).parent / "stdlib"
    resolver = ModuleResolver(project_root, stdlib_root)
    loader = ModuleLoader(resolver)

    evaluator = Evaluator()
    evaluator.module_loader = loader
    evaluator.filename = str(file)

    try:
        result, program_trace = evaluator.eval_program(program, input_data)
    except SigilError as e:
        print(f"[sigil] Runtime error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if trace:
        print(format_trace(program_trace))
    else:
        for line in program_trace.output_lines:
            print(line)
        if result is not None and not program_trace.output_lines:
            from sigil.interpreter.values import format_value
            print(format_value(result))


def _json_to_sigil(obj: object) -> Value:
    """Convert JSON-parsed data to Sigil values (Record, Symbol, etc.)."""
    from sigil.interpreter.values import Record, Symbol

    if isinstance(obj, dict):
        fields: dict[str, Value] = {k: _json_to_sigil(v) for k, v in obj.items()}
        return Record(type_name=None, fields=fields)
    if isinstance(obj, list):
        return [_json_to_sigil(v) for v in obj]
    if isinstance(obj, str) and obj.startswith(":"):
        return Symbol(obj[1:])
    return obj  # type: ignore[return-value]  # JSON primitives (int, float, str, bool, None) are valid Values


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sigil",
        description="Sigil: A neuro-symbolic programming language",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sigil lex
    lex_parser = subparsers.add_parser("lex", help="Dump token stream for a Sigil file")
    lex_parser.add_argument("file", type=Path, help="Path to .sigil file")

    # sigil parse-ast
    ast_parser = subparsers.add_parser("parse-ast", help="Dump AST for a Sigil file")
    ast_parser.add_argument("file", type=Path, help="Path to .sigil file")

    # sigil run
    run_parser = subparsers.add_parser("run", help="Execute a Sigil program")
    run_parser.add_argument("file", type=Path, help="Path to .sigil file")
    run_parser.add_argument("--trace", action="store_true", help="Show execution trace")
    run_parser.add_argument("--input", type=str, default=None, help="Input data as JSON")

    # sigil repl
    subparsers.add_parser("repl", help="Start interactive Sigil REPL")

    # sigil parse (NL-to-Sigil generator)
    parse_parser = subparsers.add_parser("parse", help="Generate Sigil code from natural language")
    parse_parser.add_argument("text", type=str, help="Natural language description")
    parse_parser.add_argument(
        "--interactive", action="store_true",
        help="Auto-refine generated code if validation fails",
    )

    # sigil check
    check_parser = subparsers.add_parser("check", help="Type-check a Sigil program")
    check_parser.add_argument("file", type=Path, help="Path to .sigil file")
    check_parser.add_argument(
        "--warnings-as-errors", action="store_true",
        help="Treat warnings as errors (exit 1 on warnings)",
    )

    # sigil fmt
    fmt_parser = subparsers.add_parser("fmt", help="Format a Sigil program")
    fmt_parser.add_argument("file", type=Path, help="Path to .sigil file")
    fmt_parser.add_argument(
        "--check", action="store_true",
        help="Check if file is formatted (exit 1 if not)",
    )

    # sigil lint
    lint_parser = subparsers.add_parser("lint", help="Lint a Sigil program")
    lint_parser.add_argument("file", type=Path, help="Path to .sigil file")
    lint_parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "lex":
        _cmd_lex(args.file)

    elif args.command == "parse-ast":
        _cmd_parse_ast(args.file)

    elif args.command == "run":
        _cmd_run(args.file, trace=args.trace, input_json=args.input)

    elif args.command == "repl":
        from sigil.interpreter.repl import run_repl

        run_repl()

    elif args.command == "parse":
        _cmd_generate(args.text, interactive=args.interactive)

    elif args.command == "check":
        _cmd_check(
            args.file,
            warnings_as_errors=args.warnings_as_errors,
        )

    elif args.command == "fmt":
        _cmd_fmt(args.file, check=getattr(args, "check", False))

    elif args.command == "lint":
        _cmd_lint(args.file, strict=args.strict)


if __name__ == "__main__":
    main()
