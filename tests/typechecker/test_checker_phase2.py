"""Tests for Phase 2 type checker enhancements."""

from __future__ import annotations

from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.types.checker import Severity, check


def check_source(source: str):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return check(program)


class TestMatchExhaustivenessWarning:
    """Check #6: Match exhaustiveness warnings."""

    def test_match_without_wildcard_warns(self):
        src = """\
compute classify from x: Number returns Text:
  return match x:
    1 -> "one"
    2 -> "two"
    3 -> "three"

main:
  given result as classify(1)
"""
        result = check_source(src)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        assert any("exhaustive" in w.message for w in warnings)

    def test_match_with_wildcard_no_warning(self):
        src = """\
compute classify from x: Number returns Text:
  return match x:
    1 -> "one"
    _ -> "other"

main:
  given result as classify(1)
"""
        result = check_source(src)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        assert not any("exhaustive" in w.message for w in warnings)

    def test_match_with_identifier_catchall_no_warning(self):
        src = """\
compute classify from x: Number returns Text:
  return match x:
    1 -> "one"
    val -> "other"

main:
  given result as classify(1)
"""
        result = check_source(src)
        warnings = [d for d in result.diagnostics if d.severity == Severity.WARNING]
        assert not any("exhaustive" in w.message for w in warnings)


class TestPipelineTypeChecking:
    """Check #7: Pipeline source type checking."""

    def test_pipeline_scalar_source_error(self):
        src = """\
main:
  given result as 42 |> filter where it exceeds 10
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        assert any("Pipeline source must be a list" in e.message for e in errors)

    def test_pipeline_string_source_error(self):
        src = """\
main:
  given result as "hello" |> filter where it exceeds 10
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        assert any("Pipeline source must be a list" in e.message for e in errors)

    def test_pipeline_list_source_no_error(self):
        src = """\
main:
  given nums as [1, 2, 3]
  given result as nums |> filter where it exceeds 1
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        # No error about pipeline source (identifier can be a list)
        assert not any("Pipeline source must be a list" in e.message for e in errors)

    def test_pipeline_list_literal_source_no_error(self):
        src = """\
main:
  given result as [1, 2, 3] |> filter where it exceeds 1
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        assert not any("Pipeline source must be a list" in e.message for e in errors)

    def test_pipeline_ops_have_it_in_scope(self):
        """Pipeline operations should have 'it' in scope."""
        src = """\
main:
  given result as [1, 2, 3] |> map to it + 1
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        # 'it' should not be flagged as undefined
        assert not any("Undefined variable: 'it'" in e.message for e in errors)


class TestLambdaTypeChecking:
    """Type checking for lambda expressions."""

    def test_lambda_params_in_scope(self):
        src = """\
main:
  given fn as compute from x: Number: x + 1
  given result as fn(5)
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        assert not any("Undefined variable: 'x'" in e.message for e in errors)

    def test_lambda_body_checked(self):
        src = """\
main:
  given fn as compute from x: Number: x + undefined_var
"""
        result = check_source(src)
        errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
        assert any("Undefined variable: 'undefined_var'" in e.message for e in errors)


class TestExistingChecksStillWork:
    """Verify existing checks haven't regressed."""

    def test_undefined_variable(self):
        src = """\
main:
  print(undefined_thing)
"""
        result = check_source(src)
        assert any(
            "Undefined variable" in d.message
            for d in result.diagnostics
            if d.severity == Severity.ERROR
        )

    def test_arity_mismatch(self):
        src = """\
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given result as add(1, 2, 3)
"""
        result = check_source(src)
        assert any(
            "Wrong number of arguments" in d.message
            for d in result.diagnostics
            if d.severity == Severity.ERROR
        )
