"""Integration tests for Phase 2 Sprint 1 example programs."""

from __future__ import annotations

from pathlib import Path

from sigil.interpreter.evaluator import evaluate
from sigil.lexer import tokenize
from sigil.parser import parse

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def run_example(name: str, input_data=None):
    path = EXAMPLES_DIR / name
    source = path.read_text()
    tokens = tokenize(source, str(path))
    program = parse(tokens, str(path))
    return evaluate(program, input_data)


class TestPhase2Examples:
    """Test that all Phase 2 Sprint 1 example programs run correctly."""

    def test_pattern_matching_example(self):
        result, trace = run_example("features/pattern_matching.sigil")
        assert "HIGH - Action required within 1 hour" in trace.output_lines
        assert "75" in trace.output_lines

    def test_pipeline_example(self):
        result, trace = run_example("features/pipeline.sigil")
        # Should produce high scores, top 3, and doubled scores
        assert len(trace.output_lines) == 3

    def test_higher_order_example(self):
        result, trace = run_example("features/higher_order.sigil")
        assert trace.output_lines == ["10", "6", "12", "11"]

    def test_data_processing_example(self):
        result, trace = run_example("features/data_processing.sigil")
        # Should produce count of senior engineers, salary list, and bonus rate
        assert len(trace.output_lines) == 3

    def test_match_rules_example(self):
        result, trace = run_example("features/match_rules.sigil")
        assert "Maximum Risk" in trace.output_lines

    def test_functional_pipeline_example(self):
        result, trace = run_example("features/functional_pipeline.sigil")
        assert len(trace.output_lines) == 3


class TestPhase1ExamplesStillWork:
    """Regression tests: Phase 1 examples must still work."""

    def test_hello_example(self):
        result, trace = run_example("basics/hello.sigil")
        # Should produce some output
        assert trace.output_lines or result is not None

    def test_temperature_example(self):
        """Temperature example runs without errors (no input = no rules fire)."""
        from sigil.interpreter.values import Record, Symbol
        result, trace = run_example(
            "basics/temperature.sigil",
            input_data={
                "reading": Record(
                    type_name="SensorReading",
                    fields={"sensor_id": "S001", "temperature": 120, "status": Symbol("active")},
                ),
            },
        )
        # With temperature 120, the temperature_alert rule should fire
        assert any(rt.fired for rt in trace.rule_traces)
