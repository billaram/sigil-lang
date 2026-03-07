"""Tests for match expression evaluation."""

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


class TestMatchExpressionEvaluation:
    """Test match expression evaluation in the interpreter."""

    def test_match_literal_integer(self):
        src = """\
compute classify from x: Number returns Number:
  return match x:
    1 -> 10
    2 -> 20
    3 -> 30
    _ -> 0

main:
  given result as classify(2)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["20"]

    def test_match_literal_string(self):
        src = """\
compute greet from name: Text returns Text:
  return match name:
    "Alice" -> "Hello Alice!"
    "Bob" -> "Hey Bob!"
    _ -> "Hi there!"

main:
  given result as greet("Bob")
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["Hey Bob!"]

    def test_match_symbol(self):
        src = """\
compute label from level: Symbol returns Text:
  return match level:
    :high -> "High Priority"
    :medium -> "Medium Priority"
    :low -> "Low Priority"
    _ -> "Unknown"

main:
  given result as label(:high)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["High Priority"]

    def test_match_wildcard(self):
        src = """\
compute classify from x: Number returns Text:
  return match x:
    100 -> "perfect"
    _ -> "normal"

main:
  given result as classify(42)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["normal"]

    def test_match_identifier_binding(self):
        src = """\
compute describe from x: Number returns Text:
  return match x:
    100 -> "perfect"
    val -> "other"

main:
  given result as describe(42)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["other"]

    def test_match_first_wins(self):
        """When multiple patterns match, the first one wins."""
        src = """\
compute test from x: Number returns Number:
  return match x:
    _ -> 1
    _ -> 2
    _ -> 3

main:
  given result as test(42)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["1"]

    def test_match_no_match_error(self):
        src = """\
compute test from x: Number returns Text:
  return match x:
    1 -> "one"
    2 -> "two"

main:
  given result as test(42)
"""
        with pytest.raises(SigilRuntimeError, match="No matching pattern"):
            run(src)

    def test_match_in_compute_function_return(self):
        src = """\
compute score from level: Symbol returns Number:
  return match level:
    :critical -> 100
    :high -> 75
    :medium -> 50
    :low -> 25
    _ -> 0

main:
  given s as score(:medium)
  print(s)
"""
        result, trace = run(src)
        assert trace.output_lines == ["50"]

    def test_match_nested_expression_body(self):
        src = """\
compute calc from x: Number returns Number:
  return match x:
    1 -> 10 + 5
    2 -> 20 * 3
    _ -> 0

main:
  given result as calc(2)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["60"]

    def test_match_boolean_literal(self):
        src = """\
compute flag from b: Boolean returns Text:
  return match b:
    true -> "yes"
    false -> "no"

main:
  given result as flag(true)
  print(result)
"""
        result, trace = run(src)
        assert trace.output_lines == ["yes"]

    def test_match_multiple_symbols(self):
        src = """\
compute color_code from color: Symbol returns Number:
  return match color:
    :red -> 1
    :green -> 2
    :blue -> 3
    _ -> 0

main:
  given r as color_code(:red)
  given g as color_code(:green)
  given b as color_code(:blue)
  given u as color_code(:yellow)
  print(r)
  print(g)
  print(b)
  print(u)
"""
        result, trace = run(src)
        assert trace.output_lines == ["1", "2", "3", "0"]

    def test_match_used_inline_in_given(self):
        src = """\
main:
  given x as 42
  given label as match x:
    42 -> "the answer"
    _ -> "something else"
  print(label)
"""
        result, trace = run(src)
        assert trace.output_lines == ["the answer"]

    def test_match_with_string_patterns(self):
        src = """\
compute categorize from s: Text returns Symbol:
  return match s:
    "error" -> :bad
    "success" -> :good
    _ -> :unknown

main:
  given r as categorize("success")
  print(r)
"""
        result, trace = run(src)
        assert trace.output_lines == [":good"]

    def test_match_zero_and_negative(self):
        src = """\
compute sign from x: Number returns Text:
  return match x:
    0 -> "zero"
    _ -> "nonzero"

main:
  given r as sign(0)
  print(r)
"""
        result, trace = run(src)
        assert trace.output_lines == ["zero"]

    def test_match_float_literal(self):
        src = """\
compute check from x: Number returns Text:
  return match x:
    3.14 -> "pi"
    _ -> "other"

main:
  given r as check(3.14)
  print(r)
"""
        result, trace = run(src)
        assert trace.output_lines == ["pi"]
