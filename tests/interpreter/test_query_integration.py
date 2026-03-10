"""Integration tests for query statements and temporal constraints in evaluator."""

from sigil.interpreter.evaluator import evaluate
from sigil.interpreter.values import Symbol
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data: dict | None = None):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


class TestQueryEvaluatorIntegration:
    def test_query_then_use_result(self):
        """Query proves a value, then subsequent code uses it."""
        result, trace = run("""
rule compute_tax:
  when income exceeds 50000
  then tax_rate is 0.3

main:
  query tax_rate
  given tax as income * tax_rate
  print(tax)
""", {"income": 100000})
        assert trace.output_lines == ["30000.0"]

    def test_query_with_forward_chaining_after(self):
        """Query followed by forward chaining evaluate."""
        result, trace = run("""
rule set_base:
  when true is true
  then base_rate is 0.05

rule apply_rate:
  when base_rate exceeds 0.01
  then final_rate is base_rate + 0.02

main:
  query base_rate
  evaluate all rules with {base_rate: base_rate}
""", {"base_rate": 0.05})
        # Just verify no errors
        assert len(trace.proof_trees) > 0

    def test_multiple_queries(self):
        """Multiple query statements in sequence."""
        result, trace = run("""
rule set_a:
  when true is true
  then a is 10

rule set_b:
  when true is true
  then b is 20

main:
  query a
  query b
  given total as a + b
  print(total)
""")
        assert trace.output_lines == ["30"]
        assert len(trace.proof_trees) == 2


class TestTemporalEvaluatorIntegration:
    def test_temporal_rule_fires(self):
        """Rule with temporal constraint fires normally (constraint recorded in metadata)."""
        result, trace = run("""
rule temp_alert:
  when temperature exceeds 100
  within 30 seconds
  then alert is true
  explain "Temperature too high"
""", {"temperature": 150})
        assert trace.rule_traces[0].fired
        assert "_temporal_constraint" in trace.rule_traces[0].metadata
        assert "30 seconds" in trace.rule_traces[0].metadata["_temporal_constraint"]

    def test_temporal_constraint_recorded(self):
        """Temporal constraint value is correctly recorded."""
        result, trace = run("""
rule monitor:
  when status is :active
  within 5 seconds
  then check is true
""", {"status": Symbol("active")})
        assert trace.rule_traces[0].fired
        assert trace.rule_traces[0].metadata["_temporal_constraint"] == "within 5 seconds"

    def test_temporal_rule_does_not_fire(self):
        """Temporal rule doesn't fire when conditions fail — no metadata."""
        result, trace = run("""
rule monitor:
  when status is :active
  within 10 seconds
  then check is true
""", {"status": Symbol("inactive")})
        assert not trace.rule_traces[0].fired
        assert "_temporal_constraint" not in trace.rule_traces[0].metadata
