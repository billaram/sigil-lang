"""Tests for type checker warning system — unused declarations, etc."""

from __future__ import annotations

from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.types.checker import Severity, check


def check_source(source: str):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return check(program)


class TestUnusedComputeWarning:
    def test_unused_compute_warns(self):
        result = check_source(
            "compute add from a: Number, b: Number returns Number:\n"
            "  return a + b\n"
        )
        warnings = [
            d for d in result.diagnostics if d.severity == Severity.WARNING
        ]
        assert len(warnings) == 1
        assert "Unused compute function" in warnings[0].message
        assert "'add'" in warnings[0].message

    def test_used_compute_no_warning(self):
        result = check_source(
            "compute add from a: Number, b: Number returns Number:\n"
            "  return a + b\n"
            "main:\n"
            "  given result as add(1, 2)\n"
            "  print(result)\n"
        )
        warnings = [
            d for d in result.diagnostics
            if d.severity == Severity.WARNING
            and "Unused compute" in d.message
        ]
        assert len(warnings) == 0


class TestUnusedConstantWarning:
    def test_unused_constant_warns(self):
        result = check_source("define X as 42\n")
        warnings = [
            d for d in result.diagnostics if d.severity == Severity.WARNING
        ]
        assert len(warnings) == 1
        assert "Unused constant" in warnings[0].message

    def test_used_constant_no_warning(self):
        result = check_source(
            "define MAX as 100\n"
            "rule check:\n"
            "  when MAX exceeds 50\n"
            "  then alert\n"
        )
        warnings = [
            d for d in result.diagnostics
            if d.severity == Severity.WARNING
            and "Unused constant" in d.message
        ]
        assert len(warnings) == 0


class TestWarningHasSuggestion:
    def test_unused_compute_has_suggestion(self):
        result = check_source(
            "compute noop from x: Number returns Number:\n"
            "  return x\n"
        )
        warnings = [
            d for d in result.diagnostics if d.severity == Severity.WARNING
        ]
        assert len(warnings) == 1
        assert warnings[0].suggestion is not None
        assert "remove" in warnings[0].suggestion

    def test_unused_constant_has_suggestion(self):
        result = check_source("define UNUSED as 99\n")
        warnings = [
            d for d in result.diagnostics if d.severity == Severity.WARNING
        ]
        assert len(warnings) == 1
        assert warnings[0].suggestion is not None
