"""Tests for sigil.trace standard library module."""

from __future__ import annotations

import json

import pytest

from sigil.interpreter.trace import ProgramTrace, RuleTrace
from sigil.stdlib._builtins import (
    stdlib_fired_rules,
    stdlib_rule_count,
    stdlib_trace_duration_ms,
    stdlib_trace_to_json,
)


@pytest.fixture()
def empty_trace():
    return ProgramTrace()


@pytest.fixture()
def populated_trace():
    trace = ProgramTrace()
    trace.add_rule_trace(RuleTrace(
        rule_name="rule_a", priority=10, fired=True, duration_ms=1.5,
    ))
    trace.add_rule_trace(RuleTrace(
        rule_name="rule_b", priority=5, fired=False, duration_ms=0.3,
    ))
    trace.add_rule_trace(RuleTrace(
        rule_name="rule_c", priority=1, fired=True, duration_ms=2.0,
    ))
    trace.total_duration_ms = 5.0
    return trace


class TestTraceToJson:
    def test_empty_trace_json(self, empty_trace):
        result = stdlib_trace_to_json([], empty_trace)
        data = json.loads(result)
        assert data["rules"] == []

    def test_populated_trace_json(self, populated_trace):
        result = stdlib_trace_to_json([], populated_trace)
        data = json.loads(result)
        assert len(data["rules"]) == 3
        assert data["rules"][0]["name"] == "rule_a"
        assert data["rules"][0]["fired"] is True


class TestFiredRules:
    def test_fired_rules_empty(self, empty_trace):
        result = stdlib_fired_rules([], empty_trace)
        assert result == []

    def test_fired_rules_returns_names(self, populated_trace):
        result = stdlib_fired_rules([], populated_trace)
        assert result == ["rule_a", "rule_c"]


class TestRuleCount:
    def test_rule_count_empty(self, empty_trace):
        result = stdlib_rule_count([], empty_trace)
        assert result == 0

    def test_rule_count_populated(self, populated_trace):
        result = stdlib_rule_count([], populated_trace)
        assert result == 3


class TestTraceDurationMs:
    def test_duration_ms(self, populated_trace):
        result = stdlib_trace_duration_ms([], populated_trace)
        assert result == 5.0
