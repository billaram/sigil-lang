"""Tests for the Sigil type checker."""

from pathlib import Path

import pytest

from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.types.checker import CheckResult, Severity, check

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def check_source(source: str) -> CheckResult:
    """Helper: lex -> parse -> check."""
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return check(program)


# ============================================================
# Check #5: Duplicate declarations
# ============================================================


class TestDuplicateDeclarations:
    def test_duplicate_constants(self):
        result = check_source("define X as 10\ndefine X as 20\n")
        assert result.has_errors
        assert result.error_count == 1
        assert "Duplicate declaration" in result.diagnostics[0].message
        assert "'X'" in result.diagnostics[0].message

    def test_duplicate_rules(self):
        result = check_source(
            "rule foo:\n  when true\n  then x is 1\n\n"
            "rule foo:\n  when true\n  then y is 2\n"
        )
        assert result.has_errors
        assert "Duplicate declaration" in result.diagnostics[0].message

    def test_duplicate_compute(self):
        result = check_source(
            "compute add from a: Number, b: Number returns Number:\n  return a + b\n\n"
            "compute add from x: Number returns Number:\n  return x\n"
        )
        assert result.has_errors

    def test_no_duplicates(self):
        result = check_source("define X as 10\ndefine Y as 20\n")
        assert not result.has_errors


# ============================================================
# Check #1: Undefined variables
# ============================================================


class TestUndefinedVariables:
    def test_undefined_in_compute_body(self):
        result = check_source(
            "compute f from x: Number returns Number:\n  return x + unknown_var\n"
        )
        assert result.has_errors
        assert any("unknown_var" in d.message for d in result.diagnostics)

    def test_defined_param(self):
        result = check_source(
            "compute f from x: Number returns Number:\n  return x + 1\n"
        )
        assert not result.has_errors

    def test_given_stmt_introduces_name(self):
        result = check_source(
            "compute f from x: Number returns Number:\n"
            "  given y as x + 1\n"
            "  return y\n"
        )
        assert not result.has_errors

    def test_constant_in_scope(self):
        result = check_source(
            "define MAX as 100\n\n"
            "rule check:\n  when reading value exceeds MAX\n  then alert is true\n"
        )
        assert not result.has_errors

    def test_settable_name_in_scope(self):
        """SetAction targets are in scope for other rules (forward chaining)."""
        result = check_source(
            "rule r1:\n  when true\n  then eligible is true\n\n"
            "rule r2:\n  when eligible is true\n  then approved is true\n"
        )
        assert not result.has_errors

    def test_field_access_base_in_scope(self):
        """Identifiers used as field-access bases are in scope (input data)."""
        result = check_source(
            "rule r:\n  when reading temperature exceeds 100\n  then alert is true\n"
        )
        assert not result.has_errors

    def test_given_clause_in_scope(self):
        result = check_source(
            "main:\n  given x as 42\n  given y as x + 1\n"
        )
        assert not result.has_errors

    def test_for_loop_var_in_scope(self):
        result = check_source(
            "main:\n  given items as [1, 2, 3]\n  for each item in items:\n    print(item)\n"
        )
        assert not result.has_errors

    def test_quantified_var_in_scope(self):
        result = check_source(
            "define ITEMS as [1, 2, 3]\n\n"
            "rule r:\n  when any x in ITEMS is true\n  then found is true\n"
        )
        assert not result.has_errors

    def test_func_call_target_not_checked(self):
        """Unknown function names should not trigger undefined variable errors."""
        result = check_source(
            "main:\n  given x as unknown_function(42)\n"
        )
        assert not result.has_errors

    def test_undefined_in_main_block(self):
        result = check_source(
            "main:\n  given y as totally_undefined + 1\n"
        )
        assert result.has_errors
        assert any("totally_undefined" in d.message for d in result.diagnostics)


# ============================================================
# Check #2: Undefined fields
# ============================================================


class TestUndefinedFields:
    def test_known_field_passes(self):
        result = check_source(
            "type Person is record:\n  name: Text\n  age: Number\n\n"
            "compute greet from p: Person returns Text:\n  return p.name\n"
        )
        assert not result.has_errors

    def test_unknown_field_fails(self):
        result = check_source(
            "type Person is record:\n  name: Text\n  age: Number\n\n"
            "compute greet from p: Person returns Text:\n  return p.email\n"
        )
        assert result.has_errors
        assert any("email" in d.message for d in result.diagnostics)
        assert any(d.suggestion and "name" in d.suggestion for d in result.diagnostics)

    def test_field_on_untyped_param_not_checked(self):
        """Field access on params without type annotations is not checked."""
        result = check_source(
            "compute f from x: Number returns Number:\n  return x + 1\n"
        )
        assert not result.has_errors

    def test_field_on_input_variable_not_checked(self):
        """Field access on input variables (not typed params) is not checked."""
        result = check_source(
            "rule r:\n  when user email is \"test\"\n  then found is true\n"
        )
        assert not result.has_errors


# ============================================================
# Check #3: Comparison type mismatches
# ============================================================


class TestComparisonTypeMismatch:
    def test_string_in_numeric_comparison(self):
        result = check_source(
            "rule r:\n  when x exceeds \"hello\"\n  then alert is true\n"
        )
        assert result.has_errors
        assert any("string" in d.message.lower() for d in result.diagnostics)

    def test_symbol_in_numeric_comparison(self):
        result = check_source(
            "rule r:\n  when x exceeds :active\n  then alert is true\n"
        )
        assert result.has_errors
        assert any("symbol" in d.message.lower() for d in result.diagnostics)

    def test_boolean_in_numeric_comparison(self):
        result = check_source(
            "rule r:\n  when x exceeds true\n  then alert is true\n"
        )
        assert result.has_errors
        assert any("boolean" in d.message.lower() for d in result.diagnostics)

    def test_list_in_numeric_comparison(self):
        result = check_source(
            "rule r:\n  when x exceeds [1, 2]\n  then alert is true\n"
        )
        assert result.has_errors
        assert any("list" in d.message.lower() for d in result.diagnostics)

    def test_number_literal_ok(self):
        result = check_source(
            "rule r:\n  when reading value exceeds 100\n  then alert is true\n"
        )
        assert not result.has_errors

    def test_identifier_ok(self):
        """Identifiers might be numbers -- don't flag them."""
        result = check_source(
            "define THRESHOLD as 100\n\n"
            "rule r:\n  when reading value exceeds THRESHOLD\n  then alert is true\n"
        )
        assert not result.has_errors

    def test_is_between_with_bad_type(self):
        result = check_source(
            "rule r:\n  when x is between \"a\" and 100\n  then alert is true\n"
        )
        assert result.has_errors


# ============================================================
# Check #4: Function arity
# ============================================================


class TestFunctionArity:
    def test_compute_wrong_arity(self):
        result = check_source(
            "compute add from a: Number, b: Number returns Number:\n  return a + b\n\n"
            "main:\n  given result as add(1)\n"
        )
        assert result.has_errors
        assert any("expects 2" in d.message for d in result.diagnostics)

    def test_compute_correct_arity(self):
        result = check_source(
            "compute add from a: Number, b: Number returns Number:\n  return a + b\n\n"
            "main:\n  given result as add(1, 2)\n"
        )
        assert not result.has_errors

    def test_neural_wrong_arity(self):
        result = check_source(
            "neural classify from text: Text:\n"
            "  model \"v1\"\n"
            "  returns Symbol\n"
            "  confidence_threshold 0.85\n"
            "  fallback to :unknown\n\n"
            "main:\n  given r as classify(\"a\", \"b\")\n"
        )
        assert result.has_errors
        assert any("expects 1" in d.message for d in result.diagnostics)

    def test_builtin_wrong_arity(self):
        result = check_source(
            "main:\n  given r as len(1, 2)\n"
        )
        assert result.has_errors

    def test_unknown_function_not_checked(self):
        result = check_source(
            "main:\n  given r as unknown_func(1, 2, 3)\n"
        )
        assert not result.has_errors

    def test_zero_arg_compute(self):
        result = check_source(
            "compute get_value returns Number:\n  return 42\n\n"
            "main:\n  given v as get_value()\n"
        )
        assert not result.has_errors


# ============================================================
# CheckResult properties
# ============================================================


class TestCheckResult:
    def test_empty_result(self):
        result = check_source("define X as 42\n")
        assert not result.has_errors
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_multiple_errors(self):
        result = check_source(
            "define X as 10\ndefine X as 20\ndefine X as 30\n"
        )
        assert result.has_errors
        assert result.error_count == 2  # 2nd and 3rd are duplicates


# ============================================================
# Integration: all 5 examples must pass
# ============================================================


class TestExampleIntegration:
    @pytest.fixture(autouse=True)
    def _load_examples(self):
        self.examples = {
            "hello": (EXAMPLES_DIR / "basics" / "hello.sigil").read_text(),
            "temperature": (EXAMPLES_DIR / "basics" / "temperature.sigil").read_text(),
            "loan": (EXAMPLES_DIR / "rules" / "loan_eligibility.sigil").read_text(),
            "triage": (EXAMPLES_DIR / "neuro_symbolic" / "medical_triage.sigil").read_text(),
            "compliance": (
                EXAMPLES_DIR / "neuro_symbolic" / "compliance_checker.sigil"
            ).read_text(),
        }

    def test_hello_no_errors(self):
        result = check_source(self.examples["hello"])
        assert not result.has_errors, _format_errors(result)

    def test_temperature_no_errors(self):
        result = check_source(self.examples["temperature"])
        assert not result.has_errors, _format_errors(result)

    def test_loan_no_errors(self):
        result = check_source(self.examples["loan"])
        assert not result.has_errors, _format_errors(result)

    def test_triage_no_errors(self):
        result = check_source(self.examples["triage"])
        assert not result.has_errors, _format_errors(result)

    def test_compliance_no_errors(self):
        result = check_source(self.examples["compliance"])
        assert not result.has_errors, _format_errors(result)


def _format_errors(result: CheckResult) -> str:
    """Format errors for assertion messages."""
    errors = [d for d in result.diagnostics if d.severity == Severity.ERROR]
    return "\n".join(f"  {d.location}: {d.message}" for d in errors)
