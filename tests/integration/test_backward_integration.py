"""Integration tests for backward chaining with complex scenarios."""

from sigil.interpreter.evaluator import evaluate
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data: dict | None = None):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


class TestBackwardForwardCombined:
    def test_backward_then_forward(self):
        """Backward chaining proves a value, then forward chaining uses it."""
        result, trace = run("""
rule compute_base:
  when true is true
  then base_rate is 0.05

rule apply_bonus with priority 5:
  when base_rate exceeds 0.01
  then final_rate is 0.1

main:
  query base_rate
  evaluate all rules with {base_rate: base_rate}
  print(final_rate)
""")
        assert "0.1" in trace.output_lines[0]


class TestDeepChains:
    def test_five_level_chain(self):
        """Five levels of backward chaining."""
        result, trace = run("""
rule level1:
  when true is true
  then a is 1

rule level2:
  when a is 1
  then b is 2

rule level3:
  when b is 2
  then c is 3

rule level4:
  when c is 3
  then d is 4

rule level5:
  when d is 4
  then e is 5

main:
  query e
  print(e)
""")
        assert trace.output_lines == ["5"]

    def test_chain_with_computation(self):
        """Backward chaining where rules do arithmetic."""
        result, trace = run("""
rule set_base:
  when true is true
  then:
    given base as 10

rule set_doubled:
  when base exceeds 5
  then:
    given doubled as base * 2

main:
  query doubled
  print(doubled)
""")
        assert trace.output_lines == ["20"]


class TestBackwardWithRecords:
    def test_backward_with_record_input(self):
        """Backward chaining using record fields from input."""
        result, trace = run("""
rule check_age:
  when age exceeds 18
  then adult is true

rule check_income:
  when income exceeds 50000
  then high_earner is true

main:
  query adult
  query high_earner
  print(adult)
  print(high_earner)
""", {"age": 25, "income": 75000})
        assert trace.output_lines == ["true", "true"]
