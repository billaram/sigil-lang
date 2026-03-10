"""Integration tests for Sprint 3 example programs."""

from pathlib import Path

from sigil.interpreter.evaluator import evaluate
from sigil.lexer import tokenize
from sigil.parser import parse

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def run_file(filepath: Path, input_data: dict | None = None):
    source = filepath.read_text(encoding="utf-8")
    tokens = tokenize(source, str(filepath))
    program = parse(tokens, str(filepath))
    return evaluate(program, input_data)


class TestBackwardChainingExample:
    def test_backward_chaining_runs(self):
        result, trace = run_file(EXAMPLES_DIR / "rules" / "backward_chaining.sigil")
        assert trace.output_lines == ["true"]

    def test_backward_chaining_proof_tree(self):
        result, trace = run_file(EXAMPLES_DIR / "rules" / "backward_chaining.sigil")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True


class TestTemporalMonitorExample:
    def test_temporal_monitor_high_temp(self):
        result, trace = run_file(
            EXAMPLES_DIR / "advanced" / "temporal_monitor.sigil",
            {"temperature": 160},
        )
        # Should fire rules and produce alert
        assert any(rt.fired for rt in trace.rule_traces)

    def test_temporal_monitor_normal_temp(self):
        result, trace = run_file(
            EXAMPLES_DIR / "advanced" / "temporal_monitor.sigil",
            {"temperature": 50},
        )
        # Normal temperature rule should fire
        fired_names = [rt.rule_name for rt in trace.rule_traces if rt.fired]
        assert "normal_temperature" in fired_names


class TestProofTreeExample:
    def test_proof_tree_runs(self):
        result, trace = run_file(EXAMPLES_DIR / "advanced" / "proof_tree.sigil")
        assert trace.output_lines == [":approved"]

    def test_proof_tree_has_proof(self):
        result, trace = run_file(EXAMPLES_DIR / "advanced" / "proof_tree.sigil")
        assert len(trace.proof_trees) > 0
        assert trace.proof_trees[0].result is True
