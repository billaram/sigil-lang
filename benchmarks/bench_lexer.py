"""Benchmark: Sigil lexer tokenization speed."""

from __future__ import annotations

import time
from pathlib import Path

from sigil.lexer import tokenize


def bench_lexer(filepath: Path, iterations: int = 100) -> dict:
    """Benchmark tokenization of a single file."""
    source = filepath.read_text(encoding="utf-8")
    # Warmup
    tokenize(source, str(filepath))

    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        tokens = tokenize(source, str(filepath))
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        times.append(elapsed)

    return {
        "file": filepath.name,
        "tokens": len(tokens),
        "lines": source.count("\n") + 1,
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }


if __name__ == "__main__":
    examples = Path(__file__).parent.parent / "examples"
    for sigil_file in sorted(examples.rglob("*.sigil")):
        result = bench_lexer(sigil_file)
        print(f"{result['file']:40s} {result['tokens']:4d} tokens  "
              f"avg={result['avg_ms']:.3f}ms  min={result['min_ms']:.3f}ms")
