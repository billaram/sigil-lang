"""Tests for Sprint 4: Integration + CLI + Benchmarks."""

import subprocess
import sys
import time
from pathlib import Path

import pytest

from sigil.interpreter.values import Symbol, Record
from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.vm.compiler import VMCompiler
from sigil.vm.runner import compile_and_run


def _run(source: str, input_data=None):
    """Helper: compile and run, return (result, output_lines, bindings)."""
    tokens = tokenize(source)
    program = parse(tokens)
    result, output_lines, bindings = compile_and_run(program, input_data)
    return result, output_lines, bindings


def _parity(source: str, input_data=None):
    """Run with both tree-walker and VM, assert output matches."""
    from sigil.interpreter import evaluate

    tokens = tokenize(source)
    program = parse(tokens)
    tw_result, tw_trace = evaluate(program, input_data)
    vm_result, vm_output, vm_bindings = compile_and_run(program, input_data)
    assert tw_trace.output_lines == vm_output, (
        f"Parity mismatch:\n  tree-walker: {tw_trace.output_lines}\n  vm: {vm_output}"
    )
    return tw_trace.output_lines, vm_output


# --- CLI Integration ---


class TestCLIVMFlag:
    def test_cli_help_shows_vm_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "sigil.cli", "run", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--vm" in result.stdout

    def test_cli_vm_runs_hello(self):
        """Test sigil run --vm with getting_started/hello.sigil."""
        hello_file = Path(__file__).parent.parent.parent / "examples" / "getting_started" / "hello.sigil"
        if not hello_file.exists():
            pytest.skip("hello.sigil not found")

        result = subprocess.run(
            [sys.executable, "-m", "sigil.cli", "run", str(hello_file), "--vm"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Hello, Sigil!" in result.stdout

    def test_cli_vm_with_input(self):
        """Test sigil run --vm with input data."""
        import tempfile
        import json

        source = """\
rule check:
  when x exceeds 10
  then:
    print("high")

main:
  given x from input
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sigil", delete=False) as f:
            f.write(source)
            f.flush()
            result = subprocess.run(
                [
                    sys.executable, "-m", "sigil.cli", "run",
                    f.name, "--vm",
                    "--input", json.dumps({"x": 15}),
                ],
                capture_output=True,
                text=True,
            )
        assert result.returncode == 0
        assert "high" in result.stdout


# --- Example File Tests ---


class TestExampleFiles:
    """Test that the VM can compile and run key example files."""

    def test_getting_started_hello(self):
        """Test getting_started/hello.sigil with VM."""
        hello_file = Path(__file__).parent.parent.parent / "examples" / "getting_started" / "hello.sigil"
        if not hello_file.exists():
            pytest.skip("hello.sigil not found")

        source = hello_file.read_text()
        tokens = tokenize(source, str(hello_file))
        program = parse(tokens, str(hello_file))
        _, output, _ = compile_and_run(program)
        assert "Hello, Sigil!" in output
        assert "Done!" in output

    def test_getting_started_calculator(self):
        """Test calculator.sigil compiles (may not match due to string interpolation)."""
        calc_file = Path(__file__).parent.parent.parent / "examples" / "getting_started" / "calculator.sigil"
        if not calc_file.exists():
            pytest.skip("calculator.sigil not found")

        source = calc_file.read_text()
        tokens = tokenize(source, str(calc_file))
        program = parse(tokens, str(calc_file))
        compiler = VMCompiler()
        chunk = compiler.compile(program)
        assert len(chunk["code"]) > 0
        assert len(chunk["functions"]) >= 3  # add, multiply, square


# --- Advanced Feature Tests ---


class TestMatchExpressions:
    def test_match_parity_integer(self):
        _parity("""\
compute classify from x: Number returns Text:
  return match x:
    1 -> "one"
    2 -> "two"
    3 -> "three"
    _ -> "other"

main:
  print(classify(1))
  print(classify(2))
  print(classify(4))
""")

    def test_match_with_symbol(self):
        _parity("""\
compute status_label from s: Symbol returns Text:
  return match s:
    :active -> "Active"
    :inactive -> "Inactive"
    _ -> "Unknown"

main:
  print(status_label(:active))
  print(status_label(:unknown))
""")


class TestComplexPrograms:
    def test_fibonacci_parity(self):
        _parity("""\
compute fib from n: Number returns Number:
  if n is at most 1:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

main:
  print(fib(0))
  print(fib(1))
  print(fib(5))
  print(fib(10))
""")

    def test_factorial_parity(self):
        _parity("""\
compute factorial from n: Number returns Number:
  if n is at most 1:
    return 1
  else:
    return n * factorial(n - 1)

main:
  print(factorial(1))
  print(factorial(5))
  print(factorial(10))
""")

    def test_power_parity(self):
        _parity("""\
compute power from base: Number, exp: Number returns Number:
  if exp is 0:
    return 1
  else:
    return base * power(base, exp - 1)

main:
  print(power(2, 10))
""")

    def test_sum_of_squares_parity(self):
        _parity("""\
compute square from x: Number returns Number:
  return x * x

main:
  given items as [1, 2, 3, 4, 5]
  given total as 0
  for each item in items:
    given sq as square(item)
    print(sq)
""")


class TestRuleChaining:
    def test_multi_rule_chain(self):
        _, _, bindings = _run("""
rule step1:
  when x exceeds 0
  then y is x * 2

rule step2:
  when y exceeds 5
  then z is y + 10

rule step3:
  when z exceeds 15
  then status is :done
""", {"x": 5})
        assert bindings.get("y") == 10
        assert bindings.get("z") == 20
        assert bindings.get("status") is not None

    def test_rule_priority_chain(self):
        """Higher priority rules should fire first, then lower."""
        _, output, _ = _run("""
rule low with priority 1:
  when flag_on is true
  then:
    print("low")

rule high with priority 10:
  when flag_on is true
  then:
    print("high")
""", {"flag_on": True})
        assert output == ["high", "low"]


class TestRecordOperations:
    def test_record_field_arithmetic(self):
        _parity("""
main:
  given point as {x: 10, y: 20}
  given sum as point.x + point.y
  print(sum)
""")

    def test_nested_computation(self):
        _parity("""\
compute distance_sq from p1x: Number, p1y: Number, p2x: Number, p2y: Number returns Number:
  given dx as p2x - p1x
  given dy as p2y - p1y
  return dx * dx + dy * dy

main:
  given d as distance_sq(0.0, 0.0, 3.0, 4.0)
  print(d)
""")


# --- Benchmark Tests ---


class TestBenchmarks:
    """Performance comparison: tree-walker vs VM."""

    def _time_tree_walker(self, source, input_data=None, iterations=10):
        from sigil.interpreter import evaluate

        tokens = tokenize(source)
        program = parse(tokens)
        start = time.perf_counter()
        for _ in range(iterations):
            evaluate(program, input_data)
        return (time.perf_counter() - start) / iterations

    def _time_vm(self, source, input_data=None, iterations=10):
        tokens = tokenize(source)
        program = parse(tokens)
        # Include compile time in first iteration, then measure execution
        compiler = VMCompiler()
        chunk = compiler.compile(program)
        start = time.perf_counter()
        for _ in range(iterations):
            compile_and_run(program, input_data)
        return (time.perf_counter() - start) / iterations

    def test_benchmark_fibonacci(self):
        """Benchmark: fibonacci(10) — tree-walker vs VM."""
        source = """\
compute fib from n: Number returns Number:
  if n is at most 1:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

main:
  given result as fib(10)
"""
        tw_time = self._time_tree_walker(source)
        vm_time = self._time_vm(source)
        speedup = tw_time / vm_time if vm_time > 0 else float("inf")
        print(f"\n  Fibonacci(15): TW={tw_time*1000:.2f}ms, VM={vm_time*1000:.2f}ms, speedup={speedup:.1f}x")
        # VM should be faster (but we don't assert a specific speedup)

    def test_benchmark_factorial(self):
        """Benchmark: factorial(20) — tree-walker vs VM."""
        source = """\
compute factorial from n: Number returns Number:
  if n is at most 1:
    return 1
  else:
    return n * factorial(n - 1)

main:
  given result as factorial(20)
"""
        tw_time = self._time_tree_walker(source)
        vm_time = self._time_vm(source)
        speedup = tw_time / vm_time if vm_time > 0 else float("inf")
        print(f"\n  Factorial(20): TW={tw_time*1000:.2f}ms, VM={vm_time*1000:.2f}ms, speedup={speedup:.1f}x")

    def test_benchmark_rules(self):
        """Benchmark: 10 rules — tree-walker vs VM."""
        rules = []
        for i in range(10):
            rules.append(f"""
rule rule_{i}:
  when x exceeds {i * 10}
  then result_{i} is {i}
""")
        source = "\n".join(rules)

        tw_time = self._time_tree_walker(source, {"x": 100})
        vm_time = self._time_vm(source, {"x": 100})
        speedup = tw_time / vm_time if vm_time > 0 else float("inf")
        print(f"\n  10 rules: TW={tw_time*1000:.2f}ms, VM={vm_time*1000:.2f}ms, speedup={speedup:.1f}x")

    def test_benchmark_loop(self):
        """Benchmark: loop with 100 iterations — tree-walker vs VM."""
        source = """\
main:
  given items as [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  given total as 0
  for each item in items:
    given sq as item * item
"""
        tw_time = self._time_tree_walker(source, iterations=50)
        vm_time = self._time_vm(source, iterations=50)
        speedup = tw_time / vm_time if vm_time > 0 else float("inf")
        print(f"\n  Loop(10): TW={tw_time*1000:.2f}ms, VM={vm_time*1000:.2f}ms, speedup={speedup:.1f}x")
