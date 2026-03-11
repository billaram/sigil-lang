"""Tests for closures and higher-order functions."""

from __future__ import annotations

import pytest

from sigil.errors import SigilRuntimeError
from sigil.interpreter.evaluator import evaluate
from sigil.lexer import tokenize
from sigil.parser import parse


def run(source: str, input_data=None):
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


class TestClosures:
    """Test closure creation and calling."""

    def test_closure_from_compute(self):
        """Compute functions should be accessible as closure values."""
        src = """\
compute double from x: Number returns Number:
  return x * 2

main:
  given result as double(5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["10"]

    def test_pass_function_as_argument(self):
        src = """\
compute apply from f, x: Number returns Number:
  return f(x)

compute double from x: Number returns Number:
  return x * 2

main:
  given result as apply(double, 5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["10"]

    def test_pass_function_as_argument_increment(self):
        src = """\
compute apply from f, x: Number returns Number:
  return f(x)

compute increment from x: Number returns Number:
  return x + 1

main:
  given result as apply(increment, 5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["6"]

    def test_compose_functions(self):
        src = """\
compute compose from f, g, x: Number returns Number:
  return f(g(x))

compute double from x: Number returns Number:
  return x * 2

compute increment from x: Number returns Number:
  return x + 1

main:
  given result as compose(double, increment, 5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["12"]

    def test_closure_wrong_arity(self):
        src = """\
compute double from x: Number returns Number:
  return x * 2

compute apply from f, x: Number, y: Number returns Number:
  return f(x, y)

main:
  given result as apply(double, 5, 10)
"""
        with pytest.raises(SigilRuntimeError, match="expects 1 args, got 2"):
            run(src)

    def test_recursive_compute(self):
        src = """\
compute factorial from n: Number returns Number:
  if n is 1:
    return 1
  return n * factorial(n - 1)

main:
  given result as factorial(5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["120"]

    def test_lambda_expression_inline(self):
        src = """\
compute apply from f, x: Number returns Number:
  return f(x)

main:
  given result as apply(compute from x: Number returns Number: x * 3, 4)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["12"]

    def test_lambda_in_given(self):
        src = """\
main:
  given doubler as compute from x: Number returns Number: x * 2
  given result as doubler(7)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["14"]

    def test_lambda_passed_to_higher_order(self):
        src = """\
compute apply from f, x: Number returns Number:
  return f(x)

main:
  given result as apply(compute from n: Number returns Number: n + 10, 5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["15"]

    def test_closure_captures_environment(self):
        """Closures should capture variables from their definition scope."""
        src = """\
compute make_adder from n: Number returns Number:
  given adder as compute from x: Number returns Number: x + n
  return adder

main:
  given add5 as make_adder(5)
  given result as add5(10)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["15"]

    def test_return_function_from_compute(self):
        src = """\
compute make_multiplier from factor: Number returns Number:
  given mul as compute from x: Number returns Number: x * factor
  return mul

main:
  given triple as make_multiplier(3)
  given result as triple(7)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["21"]

    def test_multiple_higher_order_calls(self):
        src = """\
compute apply from f, x: Number returns Number:
  return f(x)

compute double from x: Number returns Number:
  return x * 2

compute square from x: Number returns Number:
  return x * x

main:
  given a as apply(double, 5)
  given b as apply(square, 5)
  print(a)
  print(b)
"""
        result, trace = run(src)
        assert trace.output_lines == ["10", "25"]

    def test_closure_with_match(self):
        src = """\
compute classify from x: Number returns Symbol:
  return match x:
    1 -> :one
    2 -> :two
    _ -> :other

compute apply_sym from f, x: Number returns Symbol:
  return f(x)

main:
  given result as apply_sym(classify, 2)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == [":two"]

    def test_lambda_no_params(self):
        src = """\
main:
  given greeter as compute: "hello"
  given result as greeter()
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["hello"]

    def test_nested_function_calls(self):
        src = """\
compute add from a: Number, b: Number returns Number:
  return a + b

compute mul from a: Number, b: Number returns Number:
  return a * b

main:
  given result as add(mul(2, 3), mul(4, 5))
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["26"]

    def test_closure_in_pipeline_map(self):
        src = """\
compute double from x: Number returns Number:
  return x * 2

main:
  given nums as [1, 2, 3]
  given result as nums |> map to double(it)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["[2, 4, 6]"]

    def test_lambda_with_return_keyword(self):
        src = """\
main:
  given fn as compute from x: Number returns Number: return x + 100
  given result as fn(5)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["105"]

    def test_multiple_lambdas(self):
        src = """\
compute apply from f, x: Number returns Number:
  return f(x)

main:
  given a as apply(compute from x: Number: x + 1, 10)
  given b as apply(compute from x: Number: x * 10, 10)
  print(a)
  print(b)
"""
        result, trace = run(src)
        assert trace.output_lines == ["11", "100"]
