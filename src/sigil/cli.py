"""Sigil command-line interface."""

import argparse
import sys
from pathlib import Path


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


def _cmd_check(file: Path) -> None:
    """Type-check a .sigil file."""
    from sigil.errors import SigilError
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
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = check(program)

    for diag in result.diagnostics:
        severity = "error" if diag.severity == Severity.ERROR else "warning"
        print(f"{diag.location}: {severity}: {diag.message}")
        if diag.suggestion:
            print(f"  hint: {diag.suggestion}")

    if result.has_errors:
        print(f"\n{result.error_count} error(s), {result.warning_count} warning(s)")
        sys.exit(1)
    elif result.warning_count > 0:
        print(f"\n{result.warning_count} warning(s)")
    else:
        print(f"[sigil] {file}: no issues found")


def _cmd_run(file: Path, *, trace: bool = False, input_json: str | None = None) -> None:
    """Run a .sigil program."""
    import json

    from sigil.errors import SigilError
    from sigil.interpreter.evaluator import evaluate
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
    except SigilError as e:
        print(f"[sigil] Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse input data — top-level must be a dict of variable bindings
    input_data: dict | None = None
    if input_json:
        raw = json.loads(input_json)
        if not isinstance(raw, dict):
            print("[sigil] Error: --input must be a JSON object", file=sys.stderr)
            sys.exit(1)
        input_data = {k: _json_to_sigil(v) for k, v in raw.items()}

    try:
        result, program_trace = evaluate(program, input_data)
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


def _json_to_sigil(obj: object) -> object:
    """Convert JSON-parsed data to Sigil values (Record, Symbol, etc.)."""
    from sigil.interpreter.values import Record, Symbol

    if isinstance(obj, dict):
        fields = {k: _json_to_sigil(v) for k, v in obj.items()}
        return Record(type_name=None, fields=fields)
    if isinstance(obj, list):
        return [_json_to_sigil(v) for v in obj]
    if isinstance(obj, str) and obj.startswith(":"):
        return Symbol(obj[1:])
    return obj


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

    # sigil parse
    parse_parser = subparsers.add_parser("parse", help="Parse natural language to Sigil")
    parse_parser.add_argument("text", type=str, help="Natural language description")

    # sigil check
    check_parser = subparsers.add_parser("check", help="Type-check a Sigil program")
    check_parser.add_argument("file", type=Path, help="Path to .sigil file")

    # sigil fmt
    fmt_parser = subparsers.add_parser("fmt", help="Format a Sigil program")
    fmt_parser.add_argument("file", type=Path, help="Path to .sigil file")

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
        print(f'[sigil] Parsing: "{args.text}"')
        print("[sigil] NL→Sigil parser not yet implemented. See docs/ROADMAP.md for Phase 4.")

    elif args.command == "check":
        _cmd_check(args.file)

    elif args.command == "fmt":
        print(f"[sigil] Formatting {args.file}...")
        print("[sigil] Formatter not yet implemented. See docs/ROADMAP.md for Phase 4.")


if __name__ == "__main__":
    main()
