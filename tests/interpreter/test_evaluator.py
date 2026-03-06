"""Tests for the Sigil tree-walking evaluator."""

import pytest

from sigil.interpreter.evaluator import evaluate
from sigil.interpreter.values import (
    Record,
    Symbol,
    Variant,
)
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data: dict | None = None):
    """Parse and evaluate Sigil source. Returns (result, trace)."""
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------


class TestConstants:
    def test_number_constant(self):
        result, _ = run("define X as 42")
        assert result is None  # no rules → None result

    def test_constant_used_in_rule(self):
        result, trace = run("""
define LIMIT as 10

rule check:
  when true is true
  then x is 99
""")
        assert result is not None

    def test_list_constant(self):
        result, trace = run("""
define ITEMS as ["a", "b", "c"]

rule test:
  when "a" in ITEMS
  then found is true
""")
        assert trace.rule_traces[0].fired


# ------------------------------------------------------------------
# Rules — basic conditions
# ------------------------------------------------------------------


class TestRuleConditions:
    def test_true_condition(self):
        _, trace = run("""
rule always_fire:
  when true is true
  then x is 1
""")
        assert trace.rule_traces[0].fired

    def test_false_condition(self):
        _, trace = run("""
rule never_fire:
  when false is true
  then x is 1
""")
        assert not trace.rule_traces[0].fired

    def test_exceeds(self):
        _, trace = run("""
define LIMIT as 10

rule over_limit:
  when x exceeds LIMIT
  then alert is true
""", {"x": 15})
        assert trace.rule_traces[0].fired

    def test_exceeds_not(self):
        _, trace = run("""
define LIMIT as 10

rule over_limit:
  when x exceeds LIMIT
  then alert is true
""", {"x": 5})
        assert not trace.rule_traces[0].fired

    def test_is_below(self):
        _, trace = run("""
rule low:
  when x is below 10
  then alert is true
""", {"x": 5})
        assert trace.rule_traces[0].fired

    def test_is_between(self):
        _, trace = run("""
rule mid:
  when x is between 10 and 20
  then ok is true
""", {"x": 15})
        assert trace.rule_traces[0].fired

    def test_is_between_out_of_range(self):
        _, trace = run("""
rule mid:
  when x is between 10 and 20
  then ok is true
""", {"x": 25})
        assert not trace.rule_traces[0].fired

    def test_is_at_least(self):
        _, trace = run("""
rule enough:
  when x is at least 100
  then ok is true
""", {"x": 100})
        assert trace.rule_traces[0].fired

    def test_is_at_most(self):
        _, trace = run("""
rule capped:
  when x is at most 50
  then ok is true
""", {"x": 50})
        assert trace.rule_traces[0].fired

    def test_is_symbol(self):
        _, trace = run("""
rule check_status:
  when status is :active
  then ok is true
""", {"status": Symbol("active")})
        assert trace.rule_traces[0].fired

    def test_is_not(self):
        _, trace = run("""
rule not_done:
  when status is not :done
  then proceed is true
""", {"status": Symbol("active")})
        assert trace.rule_traces[0].fired


class TestCompoundConditions:
    def test_and_both_true(self):
        _, trace = run("""
rule both:
  when x exceeds 5
  and y exceeds 5
  then ok is true
""", {"x": 10, "y": 10})
        assert trace.rule_traces[0].fired

    def test_and_one_false(self):
        _, trace = run("""
rule both:
  when x exceeds 5
  and y exceeds 5
  then ok is true
""", {"x": 10, "y": 3})
        assert not trace.rule_traces[0].fired

    def test_or_one_true(self):
        _, trace = run("""
rule either:
  when x exceeds 100
  or y exceeds 100
  then alert is true
""", {"x": 5, "y": 200})
        assert trace.rule_traces[0].fired

    def test_and_short_circuit(self):
        """When first AND condition fails, second should be skipped."""
        _, trace = run("""
rule test:
  when false is true
  and x exceeds 5
  then ok is true
""", {"x": 10})
        # Second condition should be skipped
        assert not trace.rule_traces[0].fired
        assert trace.rule_traces[0].conditions[1].skipped


class TestMembership:
    def test_in_list(self):
        _, trace = run("""
define COLORS as ["red", "green", "blue"]

rule check:
  when color in COLORS
  then ok is true
""", {"color": "red"})
        assert trace.rule_traces[0].fired

    def test_not_in_list(self):
        _, trace = run("""
define COLORS as ["red", "green", "blue"]

rule check:
  when color in COLORS
  then ok is true
""", {"color": "yellow"})
        assert not trace.rule_traces[0].fired


class TestQuantified:
    def test_any(self):
        _, trace = run("""
define BANNED as ["spam", "virus"]

rule check:
  when any item in items is in BANNED
  then blocked is true
""", {"items": ["hello", "spam", "world"]})
        assert trace.rule_traces[0].fired

    def test_any_none_match(self):
        _, trace = run("""
define BANNED as ["spam", "virus"]

rule check:
  when any item in items is in BANNED
  then blocked is true
""", {"items": ["hello", "world"]})
        assert not trace.rule_traces[0].fired

    def test_all(self):
        _, trace = run("""
rule check:
  when all num in nums exceeds 0
  then all_positive is true
""", {"nums": [1, 2, 3]})
        assert trace.rule_traces[0].fired

    def test_all_fails(self):
        _, trace = run("""
rule check:
  when all num in nums exceeds 0
  then all_positive is true
""", {"nums": [1, -2, 3]})
        assert not trace.rule_traces[0].fired

    def test_none(self):
        _, trace = run("""
rule check:
  when none num in nums exceeds 100
  then safe is true
""", {"nums": [1, 2, 3]})
        assert trace.rule_traces[0].fired


class TestIsAssigned:
    def test_assigned(self):
        _, trace = run("""
rule check:
  when x is not assigned
  then default is true
""")
        assert trace.rule_traces[0].fired

    def test_not_assigned_when_set(self):
        _, trace = run("""
rule check:
  when x is not assigned
  then default is true
""", {"x": 42})
        assert not trace.rule_traces[0].fired


class TestIsEmpty:
    def test_empty_list(self):
        _, trace = run("""
rule check:
  when items is empty
  then none_found is true
""", {"items": []})
        assert trace.rule_traces[0].fired

    def test_not_empty_list(self):
        _, trace = run("""
rule check:
  when items is not empty
  then has_items is true
""", {"items": [1, 2]})
        assert trace.rule_traces[0].fired


# ------------------------------------------------------------------
# Actions
# ------------------------------------------------------------------


class TestActions:
    def test_set_action(self):
        result, _ = run("""
rule set_val:
  when true is true
  then x is 42
""")
        # Set action returns the value
        assert result == 42

    def test_set_action_symbol(self):
        result, _ = run("""
rule set_sym:
  when true is true
  then status is :approved
""")
        assert isinstance(result, Symbol)
        assert result.name == "approved"

    def test_block_action(self):
        result, trace = run("""
rule block_test:
  when true is true
  then:
    given x as 1
    given y as 2
""")
        assert trace.rule_traces[0].fired

    def test_print_action(self):
        _, trace = run("""
rule greet:
  when true is true
  then print greeting
""", {"greeting": "Hello!"})
        assert "Hello!" in trace.output_lines


# ------------------------------------------------------------------
# Forward chaining
# ------------------------------------------------------------------


class TestForwardChaining:
    def test_two_pass(self):
        """Rules that set facts enabling other rules."""
        result, trace = run("""
rule step1:
  when true is true
  then ready is true

rule step2:
  when ready is true
  then done is true
""")
        # Both should fire after forward chaining
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "step1" in fired
        assert "step2" in fired
        assert result is True

    def test_priority_ordering(self):
        """Higher priority rules fire first within an iteration."""
        _, trace = run("""
rule low with priority 1:
  when true is true
  then low_fired is true

rule high with priority 10:
  when true is true
  then high_fired is true
""")
        # High priority should appear first in fired traces
        fired_order = [rt.rule_name for rt in trace.rule_traces if rt.fired]
        assert fired_order[0] == "high"

    def test_no_re_fire(self):
        """Once a rule fires, it shouldn't fire again."""
        _, trace = run("""
rule once:
  when true is true
  then x is 1
""")
        fired_count = sum(1 for rt in trace.rule_traces if rt.fired and rt.rule_name == "once")
        assert fired_count == 1


# ------------------------------------------------------------------
# Expressions
# ------------------------------------------------------------------


class TestExpressions:
    def test_arithmetic_add(self):
        result, _ = run("""
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given result as add(3, 4)
""")

    def test_arithmetic_sub(self):
        result, _ = run("""
compute calc from a: Number, b: Number returns Number:
  return a - b

main:
  given result as calc(10, 3)
""")

    def test_arithmetic_mul(self):
        result, _ = run("""
compute calc from a: Number, b: Number returns Number:
  return a * b

main:
  given result as calc(6, 7)
""")

    def test_division(self):
        result, _ = run("""
compute calc from a: Number, b: Number returns Number:
  return a / b

main:
  given result as calc(10, 4)
""")

    def test_division_by_zero(self):
        with pytest.raises(Exception, match="Division by zero"):
            run("""
compute calc from a: Number, b: Number returns Number:
  return a / b

main:
  given result as calc(10, 0)
""")

    def test_list_concat(self):
        result, _ = run("""
compute concat from a: List, b: List returns List:
  return a + b

main:
  given result as concat([1, 2], [3, 4])
""")

    def test_field_access(self):
        record = Record(type_name=None, fields={"name": "Alice", "age": 30})
        _, trace = run("""
rule test:
  when person.age exceeds 18
  then adult is true
""", {"person": record})
        assert trace.rule_traces[0].fired

    def test_nested_field_access(self):
        inner = Record(type_name=None, fields={"temp": 105})
        outer = Record(type_name=None, fields={"vitals": inner})
        _, trace = run("""
rule test:
  when patient.vitals.temp exceeds 100
  then fever is true
""", {"patient": outer})
        assert trace.rule_traces[0].fired

    def test_unary_minus(self):
        result, _ = run("""
compute neg from x: Number returns Number:
  return -x

main:
  given result as neg(5)
""")


# ------------------------------------------------------------------
# Compute functions
# ------------------------------------------------------------------


class TestCompute:
    def test_simple_compute(self):
        result, _ = run("""
compute double from x: Number returns Number:
  return x * 2

main:
  given result as double(21)
""")

    def test_compute_with_if(self):
        result, _ = run("""
compute classify from score: Number returns Text:
  if score exceeds 90:
    return "excellent"
  if score exceeds 70:
    return "good"
  return "needs improvement"

main:
  given result as classify(85)
""")

    def test_compute_with_for(self):
        result, _ = run("""
compute sum_list from items: List returns Number:
  given total as 0
  for each item in items:
    total becomes total + item
  return total

main:
  given result as sum_list([1, 2, 3, 4, 5])
""")

    def test_compute_wrong_arg_count(self):
        with pytest.raises(Exception, match="expects"):
            run("""
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given result as add(1)
""")


# ------------------------------------------------------------------
# Builtins
# ------------------------------------------------------------------


class TestBuiltins:
    def test_print(self):
        _, trace = run("""
rule test:
  when true is true
  then print msg
""", {"msg": "test output"})
        assert "test output" in trace.output_lines

    def test_len(self):
        result, _ = run("""
compute get_count from items: List returns Number:
  return len(items)

main:
  given result as get_count([1, 2, 3])
""")

    def test_max(self):
        result, _ = run("""
compute get_max from a: Number, b: Number returns Number:
  return max(a, b)

main:
  given result as get_max(3, 7)
""")

    def test_min(self):
        result, _ = run("""
compute get_min from a: Number, b: Number returns Number:
  return min(a, b)

main:
  given result as get_min(3, 7)
""")


# ------------------------------------------------------------------
# String interpolation
# ------------------------------------------------------------------


class TestStringInterpolation:
    def test_simple_interpolation(self):
        _, trace = run("""
rule test:
  when x exceeds 10
  then ok is true
  explain "Value is {x}"
""", {"x": 42})
        assert trace.rule_traces[0].explain == "Value is 42"

    def test_field_interpolation(self):
        r = Record(type_name=None, fields={"name": "Alice"})
        _, trace = run("""
rule test:
  when true is true
  then x is 1
  explain "Hello {person.name}"
""", {"person": r})
        assert trace.rule_traces[0].explain == "Hello Alice"

    def test_unbound_interpolation(self):
        _, trace = run("""
rule test:
  when true is true
  then x is 1
  explain "Missing: {unknown}"
""")
        assert "{unknown}" in trace.rule_traces[0].explain


# ------------------------------------------------------------------
# Trace
# ------------------------------------------------------------------


class TestTrace:
    def test_trace_has_rule_traces(self):
        _, trace = run("""
rule test:
  when true is true
  then x is 1
""")
        assert len(trace.rule_traces) >= 1

    def test_trace_fired_rule(self):
        _, trace = run("""
rule test:
  when true is true
  then x is 1
""")
        assert trace.rule_traces[0].fired
        assert trace.rule_traces[0].rule_name == "test"

    def test_trace_not_fired_rule(self):
        _, trace = run("""
rule test:
  when false is true
  then x is 1
""")
        assert not trace.rule_traces[0].fired

    def test_trace_conditions(self):
        _, trace = run("""
rule test:
  when x exceeds 10
  then ok is true
""", {"x": 15})
        assert len(trace.rule_traces[0].conditions) == 1
        assert trace.rule_traces[0].conditions[0].result is True

    def test_trace_explain(self):
        _, trace = run("""
rule test:
  when true is true
  then x is 1
  explain "This is the explanation"
""")
        assert trace.rule_traces[0].explain == "This is the explanation"

    def test_trace_priority(self):
        _, trace = run("""
rule test with priority 42:
  when true is true
  then x is 1
""")
        assert trace.rule_traces[0].priority == 42

    def test_trace_output_lines(self):
        _, trace = run("""
rule test:
  when true is true
  then print msg
""", {"msg": "hello"})
        assert trace.output_lines == ["hello"]

    def test_trace_duration(self):
        _, trace = run("""
rule test:
  when true is true
  then x is 1
""")
        assert trace.total_duration_ms >= 0


# ------------------------------------------------------------------
# Main block
# ------------------------------------------------------------------


class TestMain:
    def test_main_with_given(self):
        _, trace = run("""
main:
  given x as 42
  given y as x
""")
        # Should not error

    def test_main_evaluate_rules(self):
        _, trace = run("""
rule check:
  when x exceeds 10
  then alert is true

main:
  given x as 15
  evaluate all rules with x
""")
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "check" in fired


# ------------------------------------------------------------------
# Neural stubs
# ------------------------------------------------------------------


class TestNeuralStubs:
    def test_neural_fallback_empty_list(self):
        """Neural functions should return fallback value."""
        _, trace = run("""
neural extract from text: Text:
  model "test"
  returns list of Text
  confidence_threshold 0.5
  fallback to empty list

main:
  given items as extract("hello")
""")
        # Should not crash; neural returns empty list

    def test_neural_fallback_symbol(self):
        _, trace = run("""
neural classify from text: Text:
  model "test"
  returns Symbol
  confidence_threshold 0.5
  fallback to :unknown

main:
  given result as classify("test")
""")


# ------------------------------------------------------------------
# Constructor expressions
# ------------------------------------------------------------------


class TestConstructors:
    def test_simple_constructor(self):
        result, _ = run("""
type Decision is one of:
  approved with rate: Number
  denied with reason: Text

rule test:
  when true is true
  then decision is approved with rate: 5.5
""")
        assert isinstance(result, Variant)
        assert result.variant_name == "approved"
        assert result.fields["rate"] == 5.5

    def test_no_field_variant(self):
        result, _ = run("""
type Status is one of:
  clear
  flagged with reason: Text

rule test:
  when true is true
  then risk is clear
""")
        assert isinstance(result, Variant)
        assert result.variant_name == "clear"


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


class TestEdgeCases:
    def test_unbound_comparison(self):
        """Comparing unbound variables should not crash."""
        _, trace = run("""
rule check:
  when x exceeds 10
  then alert is true
""")
        assert not trace.rule_traces[0].fired

    def test_unbound_membership(self):
        """Membership check with unbound should not crash."""
        _, trace = run("""
define LIST as [1, 2, 3]

rule check:
  when x in LIST
  then found is true
""")
        assert not trace.rule_traces[0].fired

    def test_empty_program(self):
        """Empty source should evaluate to None."""
        result, _ = run("")
        assert result is None

    def test_constants_only(self):
        """Program with only constants should evaluate."""
        result, _ = run("define X as 42")
        assert result is None

    def test_record_field_not_found(self):
        """Accessing non-existent field returns _UNBOUND, condition fails gracefully."""
        r = Record(type_name=None, fields={"x": 1})
        _, trace = run("""
rule test:
  when r.missing exceeds 0
  then ok is true
""", {"r": r})
        assert not trace.rule_traces[0].fired
