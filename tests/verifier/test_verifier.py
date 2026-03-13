"""Integration tests for the BDD-based formal verifier."""

from pathlib import Path

import pytest

from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.verifier.wrapper import verify_program, verify_file, VerificationReport


def _parse(source: str):
    tokens = tokenize(source)
    return parse(tokens)


# --- Completeness tests ---


class TestCompleteness:
    def test_complete_rules(self):
        """Two rules that cover the entire input space."""
        source = """\
rule high:
  when x exceeds 50
  then result is "high"

rule low:
  when x is at most 50
  then result is "low"
"""
        report = verify_program(_parse(source))
        assert report.completeness_ok
        assert report.coverage_percent == 100.0
        assert report.completeness_witness is None

    def test_incomplete_rules(self):
        """Single rule leaves uncovered inputs."""
        source = """\
rule high:
  when x exceeds 50
  then result is "high"
"""
        report = verify_program(_parse(source))
        assert not report.completeness_ok
        assert report.coverage_percent < 100.0
        assert report.completeness_witness is not None

    def test_three_way_split(self):
        """Three rules covering low/mid/high."""
        source = """\
rule low:
  when x is below 30
  then category is "low"

rule mid:
  when x is between 30 and 70
  then category is "mid"

rule high:
  when x exceeds 70
  then category is "high"
"""
        report = verify_program(_parse(source))
        assert report.completeness_ok

    def test_no_rules(self):
        """Program with no rules is trivially complete."""
        source = """\
define MAX as 100
"""
        report = verify_program(_parse(source))
        assert report.completeness_ok
        assert report.rule_count == 0


# --- Dead rule tests ---


class TestDeadRules:
    def test_no_dead_rules(self):
        source = """\
rule r1:
  when x exceeds 50
  then result is "high"
"""
        report = verify_program(_parse(source))
        assert report.dead_rules == []

    def test_dead_rule_contradictory_conditions(self):
        """Rule with x > 100 AND x < 50 is unsatisfiable."""
        source = """\
rule alive:
  when x exceeds 10
  then result is "ok"

rule dead:
  when x exceeds 100
  and x is below 50
  then result is "impossible"
"""
        report = verify_program(_parse(source))
        assert "dead" in report.dead_rules

    def test_dead_rule_from_symbol_exclusion(self):
        """Rule requiring status = :active AND status = :inactive is dead."""
        source = """\
rule dead:
  when status is :active
  and status is :inactive
  then result is "impossible"
"""
        report = verify_program(_parse(source))
        assert "dead" in report.dead_rules


# --- Conflict tests ---


class TestConflicts:
    def test_no_conflicts(self):
        """Non-overlapping rules don't conflict."""
        source = """\
rule low:
  when x is below 50
  then result is "low"

rule high:
  when x exceeds 50
  then result is "high"
"""
        report = verify_program(_parse(source))
        assert report.conflicts == []

    def test_conflict_same_target_different_value(self):
        """Two rules writing different values to same variable."""
        source = """\
rule r1:
  when x exceeds 50
  then result is "a"

rule r2:
  when x exceeds 50
  then result is "b"
"""
        report = verify_program(_parse(source))
        assert len(report.conflicts) == 1
        assert report.conflicts[0]["rule_a"] == "r1"
        assert report.conflicts[0]["rule_b"] == "r2"

    def test_no_conflict_different_targets(self):
        """Rules writing to different variables don't conflict."""
        source = """\
rule r1:
  when x exceeds 50
  then a is "yes"

rule r2:
  when x exceeds 50
  then b is "yes"
"""
        report = verify_program(_parse(source))
        assert report.conflicts == []

    def test_no_conflict_different_priority(self):
        """Rules at different priorities are resolved, not conflicting."""
        source = """\
rule r1 with priority 10:
  when x exceeds 50
  then result is "a"

rule r2 with priority 5:
  when x exceeds 50
  then result is "b"
"""
        report = verify_program(_parse(source))
        assert report.conflicts == []


# --- Termination tests ---


class TestTermination:
    def test_terminates_no_writes(self):
        """Rules that only read variables always terminate."""
        source = """\
rule r1:
  when x exceeds 50
  then trigger alert
"""
        report = verify_program(_parse(source))
        assert report.terminates

    def test_terminates_write_read_no_cycle(self):
        """Read x → write y → no cycle."""
        source = """\
rule r1:
  when x exceeds 50
  then y is true
"""
        report = verify_program(_parse(source))
        assert report.terminates


# --- Boolean condition tests ---


class TestBooleanConditions:
    def test_boolean_rules_complete(self):
        """flag is true OR flag is false covers everything."""
        source = """\
rule flag_on:
  when flag is true
  then result is "on"

rule flag_off:
  when flag is false
  then result is "off"
"""
        report = verify_program(_parse(source))
        assert report.completeness_ok

    def test_boolean_only_true(self):
        """Only checking is true leaves is false uncovered."""
        source = """\
rule flag_on:
  when flag is true
  then result is "on"
"""
        report = verify_program(_parse(source))
        assert not report.completeness_ok


# --- Symbol condition tests ---


class TestSymbolConditions:
    def test_symbol_mutual_exclusion(self):
        """status = :a AND status = :b is impossible."""
        source = """\
rule a:
  when status is :active
  then result is "a"

rule b:
  when status is :inactive
  then result is "b"
"""
        report = verify_program(_parse(source))
        # These don't conflict because they set the same target with different values,
        # but they CAN'T overlap due to mutual exclusion — so no conflict
        assert report.conflicts == []


# --- Compound condition tests ---


class TestCompoundConditions:
    def test_compound_and(self):
        source = """\
rule r1:
  when x exceeds 10
  and x is below 50
  then result is "mid"
"""
        report = verify_program(_parse(source))
        assert report.dead_rules == []

    def test_compound_dead(self):
        """x > 100 AND x < 50 via compound."""
        source = """\
rule r1:
  when x exceeds 100
  and x is below 50
  then result is "dead"
"""
        report = verify_program(_parse(source))
        assert "r1" in report.dead_rules


# --- Report structure tests ---


class TestReportStructure:
    def test_report_counts(self):
        source = """\
rule r1:
  when x exceeds 50
  then result is "high"

rule r2:
  when x is at most 50
  then result is "low"
"""
        report = verify_program(_parse(source))
        assert report.rule_count == 2
        assert report.variable_count >= 1
        assert report.bdd_variable_count >= 1

    def test_is_sound_property(self):
        source = """\
rule r1:
  when x exceeds 50
  then result is "high"

rule r2:
  when x is at most 50
  then result is "low"
"""
        report = verify_program(_parse(source))
        assert report.is_sound


# --- File-based tests ---


class TestVerifyFile:
    def test_verify_temperature_example(self):
        path = Path(__file__).parent.parent.parent / "examples" / "basics" / "temperature.sigil"
        if not path.exists():
            pytest.skip("Example file not found")
        report = verify_file(path)
        assert report.rule_count == 4
        assert report.is_sound

    def test_verify_loan_eligibility(self):
        path = Path(__file__).parent.parent.parent / "examples" / "rules" / "loan_eligibility.sigil"
        if not path.exists():
            pytest.skip("Example file not found")
        report = verify_file(path)
        assert report.rule_count == 8
        assert report.dead_rules == []


# --- Rust core direct tests ---


class TestRustCoreDirect:
    def test_rust_function_importable(self):
        from sigil._sigil_core import verify_program as rust_verify
        assert callable(rust_verify)

    def test_rust_empty_rules(self):
        import json
        from sigil._sigil_core import verify_program as rust_verify
        result = json.loads(rust_verify([]))
        assert result["completeness"]["is_complete"] is True
        assert result["rule_count"] == 0

    def test_rust_single_rule(self):
        import json
        from sigil._sigil_core import verify_program as rust_verify
        rules = [{
            "name": "test",
            "priority": 0,
            "conditions": [{
                "kind": "comparison",
                "variable": "x",
                "operator": "exceeds",
                "value": 50.0,
            }],
            "action": {
                "kind": "set",
                "target": "result",
                "value": "high",
            },
            "read_vars": ["x"],
            "write_vars": ["result"],
        }]
        result = json.loads(rust_verify(rules))
        assert result["rule_count"] == 1
        assert result["completeness"]["is_complete"] is False
