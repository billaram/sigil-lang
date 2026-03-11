"""Tests for the Rust trace serialization."""

import json

from sigil._sigil_core import serialize_trace_compact, serialize_trace_json

from sigil.interpreter.trace import (
    ConditionTrace,
    NeuralTrace,
    ProgramTrace,
    RuleTrace,
)


def _make_trace():
    """Create a sample ProgramTrace for testing."""
    trace = ProgramTrace()
    trace.rule_traces.append(
        RuleTrace(
            rule_name="test_rule",
            priority=10,
            fired=True,
            conditions=[
                ConditionTrace(description="x exceeds 100", result=True),
                ConditionTrace(description="status is active", result=True),
            ],
            action_description="trigger alert",
            explain="temperature too high",
            duration_ms=1.5,
        )
    )
    trace.neural_traces.append(
        NeuralTrace(
            function_name="classify",
            model_id="hf:test-model",
            confidence=0.95,
            threshold=0.8,
            used_fallback=False,
            latency_ms=42.0,
        )
    )
    trace.output_lines.append("alert triggered")
    trace.total_duration_ms = 5.0
    return trace


def _trace_to_dict(trace):
    """Convert ProgramTrace to dict for Rust serializer."""
    return {
        "rule_traces": trace.rule_traces,
        "neural_traces": trace.neural_traces,
        "output_lines": trace.output_lines,
        "total_duration_ms": trace.total_duration_ms,
    }


def test_serialize_json():
    trace = _make_trace()
    result = serialize_trace_json(_trace_to_dict(trace))
    data = json.loads(result)
    assert data["rule_traces"][0]["rule_name"] == "test_rule"
    assert data["rule_traces"][0]["fired"] is True
    assert len(data["rule_traces"][0]["conditions"]) == 2
    assert data["neural_traces"][0]["function_name"] == "classify"
    assert data["output_lines"] == ["alert triggered"]


def test_serialize_compact():
    trace = _make_trace()
    result = serialize_trace_compact(_trace_to_dict(trace))
    # Compact should have no indentation
    assert "\n" not in result
    data = json.loads(result)
    assert data["rule_traces"][0]["rule_name"] == "test_rule"


def test_serialize_empty_trace():
    trace = ProgramTrace()
    result = serialize_trace_json(_trace_to_dict(trace))
    data = json.loads(result)
    assert data["rule_traces"] == []
    assert data["neural_traces"] == []
    assert data["output_lines"] == []


def test_serialize_neural_with_error():
    trace = ProgramTrace()
    trace.neural_traces.append(
        NeuralTrace(
            function_name="classify",
            model_id="hf:model",
            confidence=0.0,
            threshold=0.8,
            used_fallback=True,
            error="Model not found",
        )
    )
    result = serialize_trace_json(_trace_to_dict(trace))
    data = json.loads(result)
    assert data["neural_traces"][0]["error"] == "Model not found"
    assert data["neural_traces"][0]["used_fallback"] is True


def test_serialize_preserves_duration():
    trace = _make_trace()
    result = serialize_trace_json(_trace_to_dict(trace))
    data = json.loads(result)
    assert data["total_duration_ms"] == 5.0
    assert data["rule_traces"][0]["duration_ms"] == 1.5
