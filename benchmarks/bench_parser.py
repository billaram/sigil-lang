"""Benchmark: Sigil parser speed."""

from __future__ import annotations

import time
from pathlib import Path

from sigil.lexer import tokenize
from sigil.parser import parse


def bench_parser(filepath: Path, iterations: int = 100) -> dict:
    """Benchmark parsing of a single file."""
    source = filepath.read_text(encoding="utf-8")
    tokens = tokenize(source, str(filepath))

    # Warmup
    parse(tokens, str(filepath))

    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        program = parse(tokens, str(filepath))
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        times.append(elapsed)

    return {
        "file": filepath.name,
        "declarations": len(program.declarations),
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }


if __name__ == "__main__":
    examples = Path(__file__).parent.parent / "examples"
    for sigil_file in sorted(examples.rglob("*.sigil")):
        result = bench_parser(sigil_file)
        print(f"{result['file']:40s} {result['declarations']:3d} decls  "
              f"avg={result['avg_ms']:.3f}ms  min={result['min_ms']:.3f}ms")
