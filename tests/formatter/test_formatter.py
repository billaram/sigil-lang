"""Tests for the Sigil AST→source formatter."""

from __future__ import annotations

from sigil.formatter import format_program
from sigil.lexer import tokenize
from sigil.parser import parse


def fmt(source: str) -> str:
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return format_program(program)


class TestConstFormatting:
    def test_simple_define(self):
        result = fmt("define X as 42\n")
        assert "define X as 42" in result

    def test_define_with_unit(self):
        result = fmt("define MAX_TEMP as 100 degrees\n")
        assert "define MAX_TEMP as 100 degrees" in result

    def test_define_string(self):
        result = fmt('define MSG as "hello"\n')
        assert 'define MSG as "hello"' in result


class TestRuleFormatting:
    def test_simple_rule(self):
        source = (
            "rule check:\n"
            "  when x exceeds 100\n"
            "  then alert\n"
        )
        result = fmt(source)
        assert "rule check:" in result
        assert "  when x exceeds 100" in result
        assert "  then alert" in result

    def test_rule_with_priority(self):
        source = (
            "rule important with priority 10:\n"
            "  when x is true\n"
            "  then notify\n"
        )
        result = fmt(source)
        assert "rule important with priority 10:" in result

    def test_rule_with_explain(self):
        source = (
            "rule check:\n"
            "  when x exceeds 100\n"
            "  then alert\n"
            '  explain "temperature too high"\n'
        )
        result = fmt(source)
        assert '  explain "temperature too high"' in result

    def test_rule_with_and_conditions(self):
        source = (
            "rule check:\n"
            "  when x exceeds 100\n"
            "  and y is :active\n"
            "  then alert\n"
        )
        result = fmt(source)
        # Parser merges and-conditions into CompoundCond
        assert "x exceeds 100 and y is :active" in result


class TestComputeFormatting:
    def test_simple_compute(self):
        source = (
            "compute add from a: Number, b: Number returns Number:\n"
            "  return a + b\n"
        )
        result = fmt(source)
        assert "compute add from a: Number, b: Number returns Number:" in result
        assert "  return a + b" in result

    def test_compute_with_if(self):
        source = (
            "compute classify from x: Number returns Symbol:\n"
            "  if x exceeds 100:\n"
            "    return :high\n"
            "  else:\n"
            "    return :low\n"
        )
        result = fmt(source)
        assert "if x exceeds 100:" in result
        assert "return :high" in result


class TestNeuralFormatting:
    def test_neural_declaration(self):
        source = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 0.8\n"
            "  fallback to :unknown\n"
        )
        result = fmt(source)
        assert "neural classify from text: Text:" in result
        assert '  model "hf:model"' in result
        assert "  returns Symbol" in result
        assert "  confidence_threshold 0.8" in result
        assert "  fallback to :unknown" in result


class TestImportFormatting:
    def test_simple_import(self):
        result = fmt("import sigil.math\ndefine X as 1\n")
        assert "import sigil.math" in result

    def test_aliased_import(self):
        result = fmt("import sigil.math as m\ndefine X as 1\n")
        assert "import sigil.math as m" in result

    def test_python_import(self):
        result = fmt("import python pandas as pd\ndefine X as 1\n")
        assert "import python pandas as pd" in result

    def test_selective_import(self):
        result = fmt(
            "from sigil.math import sqrt, floor\ndefine X as 1\n",
        )
        assert "from sigil.math import sqrt, floor" in result


class TestMainFormatting:
    def test_main_block(self):
        source = (
            "main:\n"
            "  given x as 42\n"
            "  print(x)\n"
        )
        result = fmt(source)
        assert "main:" in result
        assert "  given x as 42" in result
        assert "  print(x)" in result


class TestRoundTrip:
    def test_format_is_idempotent(self):
        """Formatting an already-formatted program should be unchanged."""
        source = (
            "define X as 42\n\n"
            "rule check:\n"
            "  when X exceeds 10\n"
            "  then alert\n"
        )
        once = fmt(source)
        twice = fmt(once)
        assert once == twice

    def test_blank_lines_between_declarations(self):
        source = "define A as 1\ndefine B as 2\n"
        result = fmt(source)
        # There should be a blank line between declarations
        assert "\n\n" in result
