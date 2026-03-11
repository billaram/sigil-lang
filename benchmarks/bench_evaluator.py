"""Benchmark: Sigil evaluator speed."""

from __future__ import annotations

import time
from pathlib import Path

from sigil.interpreter.evaluator import evaluate
from sigil.lexer import tokenize
from sigil.parser import parse


def bench_evaluator(filepath: Path, iterations: int = 50) -> dict:
    """Benchmark evaluation of a single file."""
    source = filepath.read_text(encoding="utf-8")
    tokens = tokenize(source, str(filepath))
    program = parse(tokens, str(filepath))

    # Warmup
    evaluate(program)

    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        result, trace = evaluate(program)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        times.append(elapsed)

    return {
        "file": filepath.name,
        "rules_evaluated": len(trace.rule_traces),
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }


if __name__ == "__main__":
    examples = Path(__file__).parent.parent / "examples"
    for sigil_file in sorted(examples.rglob("*.sigil")):
        try:
            result = bench_evaluator(sigil_file)
            print(f"{result['file']:40s} {result['rules_evaluated']:3d} rules  "
                  f"avg={result['avg_ms']:.3f}ms  min={result['min_ms']:.3f}ms")
        except Exception as e:
            print(f"{sigil_file.name:40s} SKIPPED ({e!r})")
