"""Integration tests for module example programs."""

from __future__ import annotations

from pathlib import Path

from sigil.interpreter.evaluator import Evaluator
from sigil.lexer import tokenize
from sigil.modules.loader import ModuleLoader
from sigil.modules.resolver import ModuleResolver
from sigil.parser import parse

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples" / "modules"
STDLIB_ROOT = Path(__file__).parent.parent.parent / "src" / "sigil" / "stdlib"


def run_file(file_path: Path):
    """Run a .sigil file with module loader configured."""
    source = file_path.read_text()
    tokens = tokenize(source, str(file_path))
    program = parse(tokens, str(file_path))

    project_root = file_path.resolve().parent
    resolver = ModuleResolver(project_root, STDLIB_ROOT)
    loader = ModuleLoader(resolver)

    evaluator = Evaluator()
    evaluator.module_loader = loader
    evaluator.filename = str(file_path)

    return evaluator.eval_program(program)


class TestModuleExamples:
    def test_math_demo(self):
        result, trace = run_file(EXAMPLES_DIR / "math_demo.sigil")
        output = "\n".join(trace.output_lines)
        assert "12.0" in output  # sqrt(144)
        assert "42" in output  # abs(-42)
        assert "3.14" in output  # round(3.14159, 2)
        assert "3.14159" in output  # PI

    def test_text_demo(self):
        result, trace = run_file(EXAMPLES_DIR / "text_demo.sigil")
        assert "HELLO, SIGIL WORLD" in trace.output_lines
        assert "hello, sigil world" in trace.output_lines
        assert "18" in trace.output_lines

    def test_multi_import(self):
        result, trace = run_file(EXAMPLES_DIR / "multi_import.sigil")
        output = "\n".join(trace.output_lines)
        assert "5.0" in output  # hypotenuse of 3,4,5
        assert "HELLO FROM SIGIL" in output
        assert "15" in output  # sum of 1..5

    def test_selective_import(self):
        result, trace = run_file(EXAMPLES_DIR / "selective_import.sigil")
        output = "\n".join(trace.output_lines)
        assert "78.5" in output or "78.53" in output  # PI * 25
        assert "RADIUS" in trace.output_lines
