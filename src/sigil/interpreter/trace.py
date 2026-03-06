"""Trace infrastructure for Sigil execution.

Traces are a first-class output — every rule evaluation produces an auditable trace.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from sigil.interpreter.values import Value, format_value


@dataclass
class ConditionTrace:
    """Trace for a single condition evaluation."""

    description: str
    result: bool
    skipped: bool = False
    bindings: dict[str, Value] = field(default_factory=dict)


@dataclass
class RuleTrace:
    """Trace for a single rule evaluation."""

    rule_name: str
    priority: int
    fired: bool
    conditions: list[ConditionTrace] = field(default_factory=list)
    action_result: Value | None = None
    action_description: str | None = None
    explain: str | None = None
    metadata: dict[str, Value] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class ProgramTrace:
    """Trace for a full program execution."""

    rule_traces: list[RuleTrace] = field(default_factory=list)
    final_result: Value | None = None
    total_duration_ms: float = 0.0
    output_lines: list[str] = field(default_factory=list)

    def add_rule_trace(self, rt: RuleTrace) -> None:
        self.rule_traces.append(rt)


class TraceTimer:
    """Context manager for timing evaluations."""

    def __init__(self) -> None:
        self.start_ns: int = 0
        self.duration_ms: float = 0.0

    def __enter__(self) -> TraceTimer:
        self.start_ns = time.perf_counter_ns()
        return self

    def __exit__(self, *args: object) -> None:
        elapsed_ns = time.perf_counter_ns() - self.start_ns
        self.duration_ms = elapsed_ns / 1_000_000


def format_trace(trace: ProgramTrace, verbose: bool = True) -> str:
    """Format a program trace for display."""
    lines: list[str] = []

    for rt in trace.rule_traces:
        status = "FIRED" if rt.fired else "NOT FIRED"
        lines.append(f"[rule {rt.rule_name}] {status} (priority {rt.priority})")

        if verbose:
            for ct in rt.conditions:
                if ct.skipped:
                    lines.append(f"  {ct.description} → (skipped)")
                else:
                    result_str = "true" if ct.result else "false"
                    lines.append(f"  {ct.description} → {result_str}")

            if rt.fired and rt.action_description:
                lines.append(f"  then {rt.action_description}")

            if rt.fired and rt.explain:
                lines.append(f"  explain: \"{rt.explain}\"")

        lines.append("")

    if trace.final_result is not None:
        lines.append(f"Result: {format_value(trace.final_result)}")

    for line in trace.output_lines:
        lines.append(line)

    return "\n".join(lines)
