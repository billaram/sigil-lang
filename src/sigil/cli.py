"""Sigil command-line interface."""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sigil",
        description="Sigil: A neuro-symbolic programming language",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sigil run
    run_parser = subparsers.add_parser("run", help="Execute a Sigil program")
    run_parser.add_argument("file", type=Path, help="Path to .sigil file")
    run_parser.add_argument("--trace", action="store_true", help="Show execution trace")

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

    if args.command == "run":
        print(f"[sigil] Running {args.file}...")
        print("[sigil] Interpreter not yet implemented. See docs/ROADMAP.md for Phase 1.")

    elif args.command == "repl":
        print("Sigil REPL v0.1.0")
        print("Type 'exit' to quit.\n")
        while True:
            try:
                line = input("sigil> ")
                if line.strip() in ("exit", "quit"):
                    break
                print(f"  [parse] {line}")
                print("  [eval]  Interpreter not yet implemented.")
            except (EOFError, KeyboardInterrupt):
                print()
                break

    elif args.command == "parse":
        print(f'[sigil] Parsing: "{args.text}"')
        print("[sigil] NL→Sigil parser not yet implemented. See docs/ROADMAP.md for Phase 4.")

    elif args.command == "check":
        print(f"[sigil] Type-checking {args.file}...")
        print("[sigil] Type checker not yet implemented. See docs/ROADMAP.md for Phase 1.")

    elif args.command == "fmt":
        print(f"[sigil] Formatting {args.file}...")
        print("[sigil] Formatter not yet implemented. See docs/ROADMAP.md for Phase 4.")


if __name__ == "__main__":
    main()
