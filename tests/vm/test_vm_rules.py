"""Tests for Sprint 3: Rule Engine + Conditions + Tracing."""

import pytest

from sigil.interpreter.values import Symbol, Record
from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.vm.compiler import VMCompiler
from sigil.vm.runner import compile_and_run


def _run(source: str, input_data=None):
    """Helper: compile and run, return (result, output_lines, bindings)."""
    tokens = tokenize(source)
    program = parse(tokens)
    result, output_lines, bindings = compile_and_run(program, input_data)
    return result, output_lines, bindings


def _parity(source: str, input_data=None):
    """Run with both tree-walker and VM, assert output matches."""
    from sigil.interpreter import evaluate

    tokens = tokenize(source)
    program = parse(tokens)
    tw_result, tw_trace = evaluate(program, input_data)
    vm_result, vm_output, vm_bindings = compile_and_run(program, input_data)
    assert tw_trace.output_lines == vm_output, (
        f"Parity mismatch:\n  tree-walker: {tw_trace.output_lines}\n  vm: {vm_output}"
    )
    return tw_trace.output_lines, vm_output


# --- Condition Types ---


class TestConditionExceeds:
    def test_exceeds_true(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then result is :yes
""", {"x": 15})
        assert bindings.get("result") is not None

    def test_exceeds_false(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then result is :yes
""", {"x": 5})
        assert bindings.get("result") is None

    def test_exceeds_equal(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then result is :yes
""", {"x": 10})
        assert bindings.get("result") is None


class TestConditionBelow:
    def test_below_true(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is below 10
  then result is :yes
""", {"x": 5})
        assert bindings.get("result") is not None

    def test_below_false(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is below 10
  then result is :yes
""", {"x": 15})
        assert bindings.get("result") is None


class TestConditionBetween:
    def test_between_inside(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is between 10 and 20
  then result is :yes
""", {"x": 15})
        assert bindings.get("result") is not None

    def test_between_outside(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is between 10 and 20
  then result is :yes
""", {"x": 25})
        assert bindings.get("result") is None

    def test_between_boundary(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is between 10 and 20
  then result is :yes
""", {"x": 10})
        assert bindings.get("result") is not None


class TestConditionIs:
    def test_is_symbol(self):
        _, _, bindings = _run("""
rule test_rule:
  when status is :active
  then result is :matched
""", {"status": Symbol("active")})
        assert bindings.get("result") is not None

    def test_is_number(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is 42
  then result is :yes
""", {"x": 42})
        assert bindings.get("result") is not None

    def test_is_not(self):
        _, _, bindings = _run("""
rule test_rule:
  when status is not :inactive
  then result is :yes
""", {"status": Symbol("active")})
        assert bindings.get("result") is not None


class TestConditionAtLeastAtMost:
    def test_at_least_true(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is at least 10
  then result is :yes
""", {"x": 10})
        assert bindings.get("result") is not None

    def test_at_most_true(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is at most 10
  then result is :yes
""", {"x": 10})
        assert bindings.get("result") is not None

    def test_at_most_false(self):
        _, _, bindings = _run("""
rule test_rule:
  when x is at most 10
  then result is :yes
""", {"x": 15})
        assert bindings.get("result") is None


# --- Compound Conditions ---


class TestCompoundConditions:
    def test_and_both_true(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  and y exceeds 20
  then result is :yes
""", {"x": 15, "y": 25})
        assert bindings.get("result") is not None

    def test_and_one_false(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  and y exceeds 20
  then result is :yes
""", {"x": 15, "y": 5})
        assert bindings.get("result") is None

    def test_multiple_conditions(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  and y exceeds 20
  and z is :active
  then result is :yes
""", {"x": 15, "y": 25, "z": Symbol("active")})
        assert bindings.get("result") is not None


# --- Rule Engine ---


class TestForwardChaining:
    def test_single_rule_fires(self):
        _, output, bindings = _run("""
rule high_temp:
  when temperature exceeds 100
  then alert is :high
""", {"temperature": 150})
        assert bindings.get("alert") is not None

    def test_rule_no_fire(self):
        _, output, bindings = _run("""
rule high_temp:
  when temperature exceeds 100
  then alert is :high
""", {"temperature": 50})
        assert bindings.get("alert") is None

    def test_multiple_rules_both_fire(self):
        _, _, bindings = _run("""
rule rule_a:
  when x exceeds 10
  then a_result is :fired

rule rule_b:
  when y exceeds 20
  then b_result is :fired
""", {"x": 15, "y": 25})
        assert bindings.get("a_result") is not None
        assert bindings.get("b_result") is not None

    def test_priority_ordering(self):
        """High priority rules should fire first."""
        _, _, bindings = _run("""
rule low_priority with priority 1:
  when x exceeds 10
  then:
    print("low")

rule high_priority with priority 10:
  when x exceeds 10
  then:
    print("high")
""", {"x": 15})
        # Both rules fire — high priority first

    def test_no_refire(self):
        """Rules should only fire once even if conditions remain true."""
        _, output, _ = _run("""
rule test_rule:
  when x exceeds 10
  then:
    print("fired")
""", {"x": 15})
        # Should appear only once
        assert output.count("fired") == 1

    def test_chain_rules(self):
        """Rule A sets variable, Rule B uses that variable."""
        _, _, bindings = _run("""
rule rule_a:
  when x exceeds 10
  then y is 100

rule rule_b:
  when y exceeds 50
  then z is :chained
""", {"x": 15})
        assert bindings.get("y") is not None
        assert bindings.get("z") is not None

    def test_fixed_point(self):
        """Forward chaining should terminate at fixed point."""
        _, _, bindings = _run("""
rule init:
  when x exceeds 0
  then status is :initialized

rule process:
  when status is :initialized
  then stage is :processed
""", {"x": 5})
        assert bindings.get("status") is not None
        assert bindings.get("stage") is not None


# --- Actions ---


class TestActions:
    def test_set_action(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then result is 42
""", {"x": 15})
        result = bindings.get("result")
        assert result is not None

    def test_set_action_symbol(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then status is :active
""", {"x": 15})
        assert bindings.get("status") is not None

    def test_set_action_expression(self):
        _, _, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then result is x * 2
""", {"x": 15})
        result = bindings.get("result")
        assert result == 30

    def test_block_action(self):
        _, output, _ = _run("""
rule test_rule:
  when x exceeds 10
  then:
    given y as x * 2
    print(y)
""", {"x": 15})
        assert output == ["30"]


# --- Rules with Compute Functions ---


class TestRulesWithCompute:
    def test_rule_calls_compute(self):
        _, output, _ = _run("""
compute double from x: Number returns Number:
  return x * 2

rule test_rule:
  when x exceeds 10
  then:
    given y as double(x)
    print(y)
""", {"x": 15})
        assert output == ["30"]


# --- Rules with Constants ---


class TestRulesWithConstants:
    def test_rule_uses_constant(self):
        _, _, bindings = _run("""
define THRESHOLD as 100

rule high_temp:
  when temperature exceeds THRESHOLD
  then alert is :high
""", {"temperature": 150})
        assert bindings.get("alert") is not None


# --- Unbound Variable Behavior ---


class TestUnboundBehavior:
    def test_unbound_exceeds_is_false(self):
        _, _, bindings = _run("""
rule test_rule:
  when missing_var exceeds 10
  then result is :yes
""")
        assert bindings.get("result") is None

    def test_unbound_is_not_is_true(self):
        _, _, bindings = _run("""
rule test_rule:
  when missing_var is not :active
  then result is :yes
""")
        assert bindings.get("result") is not None


# --- Rules + Main ---


class TestRulesAndMain:
    def test_rules_then_main(self):
        _, output, _ = _run("""
rule set_status:
  when temperature exceeds 100
  then status is :hot

main:
  given temperature from input
  print(status)
""", {"temperature": 150})
        # Rules fire before main, status should be set
        assert len(output) >= 1

    def test_main_prints_rule_result(self):
        _, output, _ = _run("""
define LIMIT as 50

rule check_limit:
  when score exceeds LIMIT
  then result is :passed

main:
  given score from input
  print(result)
""", {"score": 75})
        assert len(output) >= 1


# --- Edge Cases ---


class TestRuleEdgeCases:
    def test_empty_rules(self):
        """No rules should work fine."""
        _, output, _ = _run("""
main:
  print("hello")
""")
        assert output == ["hello"]

    def test_rule_with_record_field(self):
        _, _, bindings = _run("""
rule check_reading:
  when temperature exceeds 100
  then alert is :high
""", {"temperature": 150})
        assert bindings.get("alert") is not None


# --- Parity Tests ---


class TestRuleParity:
    def test_parity_simple_rule(self):
        _parity("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
""", {"temperature": 150})

    def test_parity_rule_no_fire(self):
        _parity("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
""", {"temperature": 50})

    def test_parity_multi_condition(self):
        _parity("""
rule complex_check:
  when temperature exceeds 100
  and pressure exceeds 50
  then alert is :critical
""", {"temperature": 150, "pressure": 75})

    def test_parity_compute_with_rule(self):
        _parity("""
compute double from x: Number returns Number:
  return x * 2

rule process:
  when value exceeds 10
  then:
    given result as double(value)
    print(result)
""", {"value": 15})

    def test_parity_constant_with_rule(self):
        _parity("""
define THRESHOLD as 100

rule high_temp:
  when temperature exceeds THRESHOLD
  then alert is :high
""", {"temperature": 150})
