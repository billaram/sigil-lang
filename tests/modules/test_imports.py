"""Tests for import evaluation in the interpreter."""

from __future__ import annotations

from sigil.interpreter.evaluator import Evaluator
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data=None):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    evaluator = Evaluator()
    return evaluator.eval_program(program, input_data)


class TestStdlibImports:
    """Test importing stdlib modules end-to-end."""

    def test_import_math_sqrt(self):
        src = """\
import sigil.math

main:
  given result as sqrt(16)
  print(result)
"""
        _, trace = run(src)
        assert trace.output_lines == ["4.0"]

    def test_import_math_pi(self):
        src = """\
import sigil.math

main:
  print(PI)
"""
        _, trace = run(src)
        assert "3.14159" in trace.output_lines[0]

    def test_import_text_uppercase(self):
        src = """\
import sigil.text

main:
  given result as uppercase("hello")
  print(result)
"""
        _, trace = run(src)
        assert trace.output_lines == ["HELLO"]

    def test_import_text_length(self):
        src = """\
import sigil.text

main:
  given result as length("hello")
  print(result)
"""
        _, trace = run(src)
        assert trace.output_lines == ["5"]

    def test_import_list_range(self):
        src = """\
import sigil.list

main:
  given nums as range(5)
  print(nums)
"""
        _, trace = run(src)
        assert trace.output_lines == ["[0, 1, 2, 3, 4]"]

    def test_import_list_reverse(self):
        src = """\
import sigil.list

main:
  given nums as reverse([3, 1, 2])
  print(nums)
"""
        _, trace = run(src)
        assert trace.output_lines == ["[2, 1, 3]"]

    def test_import_logic_type_of(self):
        src = """\
import sigil.logic

main:
  given t as type_of(42)
  print(t)
"""
        _, trace = run(src)
        assert trace.output_lines == [":Number"]


class TestSelectiveImports:
    """Test 'from X import a, b' syntax."""

    def test_selective_import(self):
        src = """\
from sigil.math import sqrt, abs

main:
  given a as sqrt(25)
  given b as abs(-10)
  print(a)
  print(b)
"""
        _, trace = run(src)
        assert trace.output_lines == ["5.0", "10"]

    def test_selective_import_not_exported(self):
        """Importing a name that's not exported should raise an error."""
        src = """\
from sigil.math import nonexistent_func

main:
  print("hello")
"""
        import pytest

        from sigil.errors import SigilRuntimeError
        with pytest.raises(SigilRuntimeError, match="not exported"):
            run(src)


    def test_selective_import_from_list(self):
        """Test selective import from sigil.list (keyword module name)."""
        src = """\
from sigil.list import reverse, sum

main:
  given nums as reverse([3, 1, 2])
  given total as sum([10, 20, 30])
  print(nums)
  print(total)
"""
        _, trace = run(src)
        assert trace.output_lines == ["[2, 1, 3]", "60"]


class TestAliasedImports:
    """Test 'import X as Y' syntax."""

    def test_aliased_import(self):
        src = """\
import sigil.math as m

main:
  given result as m.sqrt(16)
  print(result)
"""
        _, trace = run(src)
        assert trace.output_lines == ["4.0"]


class TestMultipleImports:
    """Test importing multiple modules."""

    def test_multiple_stdlib_imports(self):
        src = """\
import sigil.math
import sigil.text

main:
  given a as sqrt(9)
  given b as uppercase("hello")
  print(a)
  print(b)
"""
        _, trace = run(src)
        assert trace.output_lines == ["3.0", "HELLO"]


class TestExportDeclaration:
    """Test export parsing and AST generation."""

    def test_export_parsed(self):
        src = """\
compute add from a: Number, b: Number returns Number:
  return a + b

export add
"""
        tokens = tokenize(src, "<test>")
        program = parse(tokens, "<test>")
        from sigil.ast.nodes import ExportDecl
        export_decls = [d for d in program.declarations if isinstance(d, ExportDecl)]
        assert len(export_decls) == 1
        assert "add" in export_decls[0].names

    def test_export_multiple_names(self):
        src = """\
compute add from a: Number, b: Number returns Number:
  return a + b

compute sub from a: Number, b: Number returns Number:
  return a - b

export add, sub
"""
        tokens = tokenize(src, "<test>")
        program = parse(tokens, "<test>")
        from sigil.ast.nodes import ExportDecl
        export_decls = [d for d in program.declarations if isinstance(d, ExportDecl)]
        assert len(export_decls) == 1
        assert set(export_decls[0].names) == {"add", "sub"}
