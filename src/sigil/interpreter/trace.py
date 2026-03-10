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
    proof_trees: list[object] = field(default_factory=list)  # list[ProofNode]

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


def _format_proof_node(node: object, indent: int = 0) -> list[str]:
    """Format a ProofNode tree for display."""
    from sigil.interpreter.backward import ProofNode

    if not isinstance(node, ProofNode):
        return []

    lines: list[str] = []
    prefix = "  " * indent
    status = "PROVED" if node.result else "FAILED"
    if node.rule:
        rule_info = f" via {node.rule}"
    elif node.result:
        rule_info = " (from environment)"
    else:
        rule_info = " (no matching rule)"
    lines.append(f"{prefix}[query {node.goal}] {status}{rule_info}")

    if node.bindings:
        bindings_str = ", ".join(
            f"{k} = {format_value(v)}" for k, v in node.bindings.items()
        )
        lines.append(f"{prefix}  bindings: {bindings_str}")

    for sub in node.subgoals:
        lines.extend(_format_proof_node(sub, indent + 1))

    return lines


def format_trace(trace: ProgramTrace, verbose: bool = True) -> str:
    """Format a program trace for display."""
    lines: list[str] = []

    # Forward chaining rule traces
    if trace.rule_traces:
        lines.append("── Forward Chaining ──")
        lines.append("")

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

            if rt.metadata:
                for k, v in rt.metadata.items():
                    if not k.startswith("_"):
                        continue
                    lines.append(f"  {k.lstrip('_')}: {v}")

        lines.append("")

    # Backward chaining proof trees
    if trace.proof_trees:
        lines.append("── Backward Chaining ──")
        lines.append("")
        for tree in trace.proof_trees:
            lines.extend(_format_proof_node(tree))
            lines.append("")

    if trace.final_result is not None:
        lines.append(f"Result: {format_value(trace.final_result)}")

    # Program output
    if trace.output_lines:
        lines.append("── Output ──")
        for line in trace.output_lines:
            lines.append(line)

    return "\n".join(lines)
