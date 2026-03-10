"""Run all Sigil benchmarks and report results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from benchmarks.bench_evaluator import bench_evaluator
from benchmarks.bench_lexer import bench_lexer
from benchmarks.bench_parser import bench_parser


def main() -> None:
    examples_dir = ROOT / "examples"
    sigil_files = sorted(examples_dir.rglob("*.sigil"))

    results: dict[str, list[dict]] = {"lexer": [], "parser": [], "evaluator": []}

    print("=" * 70)
    print("Sigil Performance Benchmarks")
    print("=" * 70)

    # Lexer benchmarks
    print("\n--- Lexer ---")
    print(f"{'File':<40s} {'Tokens':>6s} {'Avg(ms)':>10s} {'Min(ms)':>10s}")
    for f in sigil_files:
        r = bench_lexer(f)
        results["lexer"].append(r)
        print(f"{r['file']:<40s} {r['tokens']:>6d} {r['avg_ms']:>10.3f} {r['min_ms']:>10.3f}")

    # Parser benchmarks
    print("\n--- Parser ---")
    print(f"{'File':<40s} {'Decls':>6s} {'Avg(ms)':>10s} {'Min(ms)':>10s}")
    for f in sigil_files:
        r = bench_parser(f)
        results["parser"].append(r)
        print(f"{r['file']:<40s} {r['declarations']:>6d} {r['avg_ms']:>10.3f} {r['min_ms']:>10.3f}")

    # Evaluator benchmarks
    print("\n--- Evaluator ---")
    print(f"{'File':<40s} {'Rules':>6s} {'Avg(ms)':>10s} {'Min(ms)':>10s}")
    for f in sigil_files:
        try:
            r = bench_evaluator(f)
            results["evaluator"].append(r)
            print(f"{r['file']:<40s} {r['rules_evaluated']:>6d} "
                  f"{r['avg_ms']:>10.3f} {r['min_ms']:>10.3f}")
        except Exception as e:
            print(f"{f.name:<40s} SKIPPED ({type(e).__name__})")

    # Save JSON
    output_path = ROOT / "benchmarks" / "results.json"
    with open(output_path, "w") as fp:
        json.dump(results, fp, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
