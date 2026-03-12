"""Tests for the Sigil semantic linter."""

from __future__ import annotations

from sigil.ast import nodes as ast
from sigil.lexer import tokenize
from sigil.linter import lint
from sigil.parser import parse
from sigil.types.checker import Severity


def lint_source(source: str):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return lint(program)


_LOC = ast.SourceLocation(file="<test>", line=1, column=1)


class TestRuleLinting:
    def test_empty_rule_body_warning(self):
        """Empty BlockAction body triggers warning (constructed via AST)."""
        rule = ast.RuleDecl(
            location=_LOC, name="empty",
            conditions=(
                ast.ComparisonCond(
                    _LOC,
                    left=ast.Identifier(_LOC, "x"),
                    operator="exceeds",
                    right=ast.Literal(_LOC, 100, "number"),
                ),
            ),
            action=ast.BlockAction(location=_LOC, body=()),
            priority=0, given_clauses=(), explain=None,
            temporal=None,
        )
        program = ast.Program(
            location=_LOC, module=None, imports=(), declarations=(rule,),
        )
        result = lint(program)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        msgs = [d.message for d in warnings]
        assert any("empty action block" in m for m in msgs)

    def test_duplicate_condition_warning(self):
        """Duplicate conditions in the list trigger warning (constructed via AST)."""
        cond = ast.ComparisonCond(
            _LOC,
            left=ast.Identifier(_LOC, "x"),
            operator="exceeds",
            right=ast.Literal(_LOC, 100, "number"),
        )
        rule = ast.RuleDecl(
            location=_LOC, name="dup",
            conditions=(cond, cond),
            action=ast.SimpleAction(
                location=_LOC, name="alert",
            ),
            priority=0, given_clauses=(), explain=None,
            temporal=None,
        )
        program = ast.Program(
            location=_LOC, module=None, imports=(), declarations=(rule,),
        )
        result = lint(program)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        msgs = [d.message for d in warnings]
        assert any("Duplicate condition" in m for m in msgs)

    def test_no_warning_on_distinct_conditions(self):
        """Distinct conditions should not trigger duplicate warning."""
        cond1 = ast.ComparisonCond(
            _LOC,
            left=ast.Identifier(_LOC, "x"),
            operator="exceeds",
            right=ast.Literal(_LOC, 100, "number"),
        )
        cond2 = ast.ComparisonCond(
            _LOC,
            left=ast.Identifier(_LOC, "y"),
            operator="exceeds",
            right=ast.Literal(_LOC, 200, "number"),
        )
        rule = ast.RuleDecl(
            location=_LOC, name="distinct",
            conditions=(cond1, cond2),
            action=ast.SimpleAction(
                location=_LOC, name="alert",
            ),
            priority=0, given_clauses=(), explain=None,
            temporal=None,
        )
        program = ast.Program(
            location=_LOC, module=None, imports=(), declarations=(rule,),
        )
        result = lint(program)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        lint_warnings = [w for w in warnings if "Duplicate" in w.message]
        assert len(lint_warnings) == 0

    def test_normal_rule_no_lint_warning(self):
        source = (
            "rule ok:\n"
            "  when x exceeds 100\n"
            "  then alert\n"
        )
        result = lint_source(source)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        lint_warnings = [
            w for w in warnings
            if "empty action" in w.message or "Duplicate" in w.message
        ]
        assert len(lint_warnings) == 0


class TestNeuralLinting:
    def test_confidence_threshold_too_high(self):
        source = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 1.5\n"
            "  fallback to :unknown\n"
        )
        result = lint_source(source)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        msgs = [d.message for d in warnings]
        assert any("out of range" in m for m in msgs)

    def test_confidence_threshold_too_high_integer(self):
        source = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 5\n"
            "  fallback to :unknown\n"
        )
        result = lint_source(source)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        msgs = [d.message for d in warnings]
        assert any("out of range" in m for m in msgs)

    def test_valid_confidence_threshold_no_warning(self):
        source = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 0.8\n"
            "  fallback to :unknown\n"
        )
        result = lint_source(source)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        lint_warnings = [w for w in warnings if "out of range" in w.message]
        assert len(lint_warnings) == 0

    def test_boundary_confidence_threshold_ok(self):
        """0.0 and 1.0 should not trigger warning."""
        source = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 1.0\n"
            "  fallback to :unknown\n"
        )
        result = lint_source(source)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        lint_warnings = [w for w in warnings if "out of range" in w.message]
        assert len(lint_warnings) == 0


class TestLintSuggestions:
    def test_empty_rule_has_suggestion(self):
        """Empty rule warning includes actionable suggestion."""
        rule = ast.RuleDecl(
            location=_LOC, name="empty",
            conditions=(
                ast.ComparisonCond(
                    _LOC,
                    left=ast.Identifier(_LOC, "x"),
                    operator="exceeds",
                    right=ast.Literal(_LOC, 100, "number"),
                ),
            ),
            action=ast.BlockAction(location=_LOC, body=()),
            priority=0, given_clauses=(), explain=None,
            temporal=None,
        )
        program = ast.Program(
            location=_LOC, module=None, imports=(), declarations=(rule,),
        )
        result = lint(program)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        rule_warnings = [w for w in warnings if "empty action" in w.message]
        assert len(rule_warnings) > 0
        assert rule_warnings[0].suggestion is not None

    def test_confidence_warning_has_suggestion(self):
        source = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 2.0\n"
            "  fallback to :unknown\n"
        )
        result = lint_source(source)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        conf_warnings = [w for w in warnings if "out of range" in w.message]
        assert len(conf_warnings) > 0
        assert "between" in conf_warnings[0].suggestion


class TestLintIntegration:
    def test_lint_includes_type_checker_diagnostics(self):
        """lint() runs the type checker too — undefined var should appear."""
        source = (
            "rule test:\n"
            "  when undefined_var exceeds 100\n"
            "  then alert\n"
        )
        result = lint_source(source)
        assert len(result.diagnostics) > 0
