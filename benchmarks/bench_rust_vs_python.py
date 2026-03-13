"""Benchmark: Rust core vs Python for pattern matching and constraint solving."""

import time


def bench_pattern_matching():
    """Benchmark Rete network matching vs Python dict comparison."""
    from sigil._sigil_core import ReteNetwork

    # Setup: 50 rules with 3 conditions each
    net = ReteNetwork()
    for i in range(50):
        net.add_rule(
            f"rule_{i}",
            i,
            [
                ("temperature", "exceeds", float(50 + i)),
                ("pressure", "below", float(200 - i)),
                ("status", "is", "active"),
            ],
        )

    facts = {"temperature": 120.0, "pressure": 80.0, "status": "active"}
    n_iterations = 10_000

    # Rust: Rete matching
    start = time.perf_counter_ns()
    for _ in range(n_iterations):
        net.match_facts(facts)
    rust_ns = time.perf_counter_ns() - start
    rust_ms = rust_ns / 1_000_000

    # Python: equivalent dict-based matching
    rules = []
    for i in range(50):
        rules.append({
            "name": f"rule_{i}",
            "priority": i,
            "conditions": [
                ("temperature", ">", 50 + i),
                ("pressure", "<", 200 - i),
                ("status", "==", "active"),
            ],
        })

    def python_match(rules, facts):
        matches = []
        for rule in rules:
            all_match = True
            for field, op, val in rule["conditions"]:
                fv = facts.get(field)
                if fv is None:
                    all_match = False
                    break
                if op == ">" and not (fv > val):
                    all_match = False
                    break
                if op == "<" and not (fv < val):
                    all_match = False
                    break
                if op == "==" and fv != val:
                    all_match = False
                    break
            if all_match:
                matches.append((rule["name"], rule["priority"]))
        matches.sort(key=lambda x: -x[1])
        return matches

    start = time.perf_counter_ns()
    for _ in range(n_iterations):
        python_match(rules, facts)
    python_ns = time.perf_counter_ns() - start
    python_ms = python_ns / 1_000_000

    speedup = python_ns / rust_ns if rust_ns > 0 else float("inf")
    print(f"\n--- Pattern Matching ({n_iterations} iterations, 50 rules) ---")
    print(f"  Rust:   {rust_ms:>8.1f} ms")
    print(f"  Python: {python_ms:>8.1f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    return speedup


def bench_constraint_solving():
    """Benchmark Rust constraint solver vs Python equivalents."""
    from sigil._sigil_core import ConstraintSolver

    n_iterations = 10_000

    # Rust solver
    solver = ConstraintSolver()
    solver.add_greater_than("temperature", 100.0)
    solver.add_less_than("temperature", 200.0)
    solver.add_between("pressure", 50.0, 150.0)
    solver.add_equals("status", "active")
    solver.add_not_equals("error", "timeout")

    bindings = {
        "temperature": 150,
        "pressure": 100,
        "status": "active",
        "error": "none",
    }

    start = time.perf_counter_ns()
    for _ in range(n_iterations):
        solver.is_satisfied(bindings)
    rust_ns = time.perf_counter_ns() - start
    rust_ms = rust_ns / 1_000_000

    # Python equivalent
    def python_check(bindings):
        t = bindings["temperature"]
        p = bindings["pressure"]
        s = bindings["status"]
        e = bindings["error"]
        return (
            t > 100
            and t < 200
            and 50 <= p <= 150
            and s == "active"
            and e != "timeout"
        )

    start = time.perf_counter_ns()
    for _ in range(n_iterations):
        python_check(bindings)
    python_ns = time.perf_counter_ns() - start
    python_ms = python_ns / 1_000_000

    speedup = python_ns / rust_ns if rust_ns > 0 else float("inf")
    print(f"\n--- Constraint Solving ({n_iterations} iterations, 5 constraints) ---")
    print(f"  Rust:   {rust_ms:>8.1f} ms")
    print(f"  Python: {python_ms:>8.1f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    return speedup


def bench_trace_serialization():
    """Benchmark Rust JSON trace serialization vs Python json.dumps."""
    import json
    from sigil._sigil_core import serialize_trace_json
    from sigil.interpreter.trace import (
        ConditionTrace,
        NeuralTrace,
        ProgramTrace,
        RuleTrace,
    )

    # Build a realistic trace
    trace = ProgramTrace()
    for i in range(20):
        trace.rule_traces.append(
            RuleTrace(
                rule_name=f"rule_{i}",
                priority=i,
                fired=i % 3 == 0,
                conditions=[
                    ConditionTrace(description=f"cond_{j}", result=j % 2 == 0)
                    for j in range(5)
                ],
                action_description=f"action_{i}",
                explain=f"explanation for rule {i}",
                duration_ms=float(i) * 0.5,
            )
        )
    for i in range(5):
        trace.neural_traces.append(
            NeuralTrace(
                function_name=f"neural_{i}",
                model_id=f"hf:model-{i}",
                confidence=0.8 + i * 0.02,
                threshold=0.7,
                used_fallback=i % 2 == 0,
                latency_ms=float(i) * 10.0,
            )
        )
    trace.output_lines = [f"output line {i}" for i in range(10)]
    trace.total_duration_ms = 100.0

    trace_dict = {
        "rule_traces": trace.rule_traces,
        "neural_traces": trace.neural_traces,
        "output_lines": trace.output_lines,
        "total_duration_ms": trace.total_duration_ms,
    }

    n_iterations = 1_000

    # Rust serialization
    start = time.perf_counter_ns()
    for _ in range(n_iterations):
        serialize_trace_json(trace_dict)
    rust_ns = time.perf_counter_ns() - start
    rust_ms = rust_ns / 1_000_000

    # Python: manually build dict and json.dumps
    def python_serialize(trace):
        data = {
            "rule_traces": [
                {
                    "rule_name": rt.rule_name,
                    "priority": rt.priority,
                    "fired": rt.fired,
                    "conditions": [
                        {"description": c.description, "result": c.result, "skipped": c.skipped}
                        for c in rt.conditions
                    ],
                    "action_description": rt.action_description,
                    "explain": rt.explain,
                    "duration_ms": rt.duration_ms,
                }
                for rt in trace.rule_traces
            ],
            "neural_traces": [
                {
                    "function_name": nt.function_name,
                    "model_id": nt.model_id,
                    "confidence": nt.confidence,
                    "threshold": nt.threshold,
                    "used_fallback": nt.used_fallback,
                    "latency_ms": nt.latency_ms,
                    "error": nt.error,
                }
                for nt in trace.neural_traces
            ],
            "output_lines": trace.output_lines,
            "total_duration_ms": trace.total_duration_ms,
        }
        return json.dumps(data, indent=2)

    start = time.perf_counter_ns()
    for _ in range(n_iterations):
        python_serialize(trace)
    python_ns = time.perf_counter_ns() - start
    python_ms = python_ns / 1_000_000

    speedup = python_ns / rust_ns if rust_ns > 0 else float("inf")
    print(f"\n--- Trace Serialization ({n_iterations} iterations, 20 rules + 5 neural) ---")
    print(f"  Rust:   {rust_ms:>8.1f} ms")
    print(f"  Python: {python_ms:>8.1f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    return speedup


if __name__ == "__main__":
    print("=" * 60)
    print("Sigil Rust Core Benchmarks")
    print("=" * 60)

    s1 = bench_pattern_matching()
    s2 = bench_constraint_solving()
    s3 = bench_trace_serialization()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Pattern matching: {s1:.1f}x speedup")
    print(f"  Constraint solving: {s2:.1f}x speedup")
    print(f"  Trace serialization: {s3:.1f}x speedup")
    print("=" * 60)
