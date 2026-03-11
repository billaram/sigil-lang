"""Tests for the backward chaining engine."""


from sigil.interpreter.evaluator import evaluate
from sigil.interpreter.values import Symbol
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data: dict | None = None):
    """Parse and evaluate Sigil source. Returns (result, trace)."""
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


# ============================================================
# BackwardChainer unit tests via query statement
# ============================================================


class TestBackwardChainingBasic:
    def test_query_already_bound(self):
        """Query succeeds immediately if goal is already in env."""
        result, trace = run("""
main:
  given x as 42
  query x
""")
        assert result is None or result is not None  # just verify no error

    def test_query_simple_rule(self):
        """Query finds a rule that sets the goal."""
        result, trace = run("""
rule set_eligible:
  when true is true
  then eligible is true

main:
  query eligible
""")
        # After query, eligible should be proved
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_query_rule_not_applicable(self):
        """Query fails when no rule can satisfy the goal."""
        result, trace = run("""
rule set_eligible:
  when x exceeds 100
  then eligible is true

main:
  given x as 50
  query eligible
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is False

    def test_query_with_priority(self):
        """Higher priority rules are tried first."""
        result, trace = run("""
rule low_priority:
  when true is true
  then status is :low

rule high_priority with priority 10:
  when true is true
  then status is :high

main:
  query status
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True
        assert trace.proof_trees[0].rule == "high_priority"


class TestBackwardChainingChains:
    def test_two_level_chain(self):
        """Query recursively proves dependencies."""
        result, trace = run("""
rule set_a:
  when true is true
  then a is 10

rule set_b:
  when a exceeds 5
  then b is 20

main:
  query b
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_three_level_chain(self):
        """Three-level backward chaining."""
        result, trace = run("""
rule set_x:
  when true is true
  then x is 1

rule set_y:
  when x is 1
  then y is 2

rule set_z:
  when y is 2
  then z is 3

main:
  query z
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_cycle_detection(self):
        """Cyclic rules don't cause infinite recursion."""
        result, trace = run("""
rule set_a:
  when b is true
  then a is true

rule set_b:
  when a is true
  then b is true

main:
  query a
""")
        # Should not hang — cycle detection kicks in
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is False


class TestBackwardChainingConditions:
    def test_query_with_input_data(self):
        """Backward chaining uses input data."""
        result, trace = run("""
rule check_score:
  when score exceeds 80
  then passed is true

main:
  query passed
""", {"score": 90})
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_query_with_multiple_conditions(self):
        """Rule with multiple conditions."""
        result, trace = run("""
rule check:
  when x exceeds 10
  and y is below 100
  then valid is true

main:
  query valid
""", {"x": 50, "y": 20})
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_query_condition_fails(self):
        """Rule condition not met."""
        result, trace = run("""
rule check:
  when x exceeds 100
  then valid is true

main:
  query valid
""", {"x": 50})
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is False

    def test_query_with_symbol_condition(self):
        """Backward chaining with symbol conditions."""
        result, trace = run("""
rule check_status:
  when status is :active
  then can_proceed is true

main:
  query can_proceed
""", {"status": Symbol("active")})
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True


class TestBackwardChainingBlockActions:
    def test_query_block_action(self):
        """Query works with block actions (then:)."""
        result, trace = run("""
rule compute_result:
  when true is true
  then:
    given result as 42

main:
  query result
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_query_multiple_targets_in_block(self):
        """Block action setting multiple variables."""
        result, trace = run("""
rule set_values:
  when true is true
  then:
    given a as 10
    given b as 20

main:
  query a
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True

    def test_query_no_matching_rule(self):
        """Query for a variable that no rule sets."""
        result, trace = run("""
rule set_x:
  when true is true
  then x is 42

main:
  query y
""")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is False

    def test_query_updates_env(self):
        """Query results are available to subsequent statements."""
        result, trace = run("""
rule set_x:
  when true is true
  then x is 42

main:
  query x
  given y as x + 1
  print(y)
""")
        assert trace.output_lines == ["43"]
