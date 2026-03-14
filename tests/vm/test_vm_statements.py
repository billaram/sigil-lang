"""Tests for Sprint 2: Statements + Control Flow + Builtins."""

import pytest

from sigil.interpreter.values import Symbol
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


# --- If/Elif/Else ---


class TestIfElif:
    def test_elif_chain(self):
        result, output, _ = _run("""
compute classify from x: Number returns Text:
  if x exceeds 100:
    return "hot"
  else:
    if x exceeds 50:
      return "warm"
    else:
      return "cold"

main:
  print(classify(150))
  print(classify(75))
  print(classify(25))
""")
        assert output == ["hot", "warm", "cold"]

    def test_nested_if(self):
        result, output, _ = _run("""
main:
  given x as 10
  given y as 20
  if x exceeds 5:
    if y exceeds 15:
      print("both")
    else:
      print("only x")
  else:
    print("neither")
""")
        assert output == ["both"]

    def test_if_with_compound_condition(self):
        _parity("""
main:
  given x as 15
  given y as 25
  if x exceeds 10:
    if y exceeds 20:
      print("both high")
""")


# --- For Loops ---


class TestForLoops:
    def test_for_each_accumulator(self):
        result, output, _ = _run("""
main:
  given items as [1, 2, 3, 4, 5]
  given total as 0
  for each item in items:
    total becomes total + item
  print(total)
""")
        assert output == ["15"]

    def test_for_nested_loops(self):
        result, output, _ = _run("""
main:
  given rows as [1, 2]
  given cols as [10, 20]
  for each r in rows:
    for each c in cols:
      given product as r * c
      print(product)
""")
        assert output == ["10", "20", "20", "40"]

    def test_for_empty_list(self):
        result, output, _ = _run("""
main:
  given items as empty list
  for each item in items:
    print(item)
  print("done")
""")
        assert output == ["done"]

    def test_for_with_if(self):
        result, output, _ = _run("""
main:
  given items as [1, 2, 3, 4, 5]
  for each item in items:
    if item exceeds 3:
      print(item)
""")
        assert output == ["4", "5"]


# --- Given Bindings ---


class TestGivenBindings:
    def test_given_from_input(self):
        result, output, _ = _run("""
main:
  given temp from input
  print(temp)
""", {"temp": 98.6})
        assert output == ["98.6"]

    def test_given_as_expression(self):
        result, output, _ = _run("""
main:
  given x as 10
  given y as x * 2
  print(y)
""")
        assert output == ["20"]

    def test_given_from_preserves_existing(self):
        """given from input should keep existing bound value."""
        result, output, _ = _run("""
main:
  given x from input
  print(x)
""", {"x": 42})
        assert output == ["42"]


# --- Becomes (Mutation) ---


class TestBecomes:
    def test_becomes_counter(self):
        result, output, _ = _run("""
main:
  given counter as 0
  counter becomes counter + 1
  counter becomes counter + 1
  counter becomes counter + 1
  print(counter)
""")
        assert output == ["3"]

    def test_becomes_string(self):
        result, output, _ = _run("""
main:
  given name as "hello"
  name becomes "world"
  print(name)
""")
        assert output == ["world"]


# --- Builtins ---


class TestBuiltins:
    def test_print_multiple_types(self):
        result, output, _ = _run("""
main:
  print("text")
  print(42)
  print(3.14)
  print(true)
  print(:active)
""")
        assert len(output) == 5
        assert output[0] == "text"
        assert output[1] == "42"
        assert output[2] == "3.14"
        assert output[3] == "true"
        assert output[4] == ":active"

    def test_len_string(self):
        result, output, _ = _run("""
main:
  given x as len("hello")
  print(x)
""")
        assert output == ["5"]

    def test_max_list(self):
        result, output, _ = _run("""
main:
  given x as max([3, 7, 1, 5])
  print(x)
""")
        assert output == ["7"]

    def test_min_list(self):
        result, output, _ = _run("""
main:
  given x as min([3, 7, 1, 5])
  print(x)
""")
        assert output == ["1"]

    def test_abs_negative(self):
        result, output, _ = _run("""
main:
  print(abs(-10))
  print(abs(5))
""")
        assert output == ["10", "5"]

    def test_sqrt(self):
        result, output, _ = _run("""
main:
  given x as sqrt(16.0)
  print(x)
""")
        assert output == ["4.0"]

    def test_round(self):
        result, output, _ = _run("""
main:
  given x as round(3.7)
  print(x)
""")
        assert output == ["4"]

    def test_floor_ceil(self):
        result, output, _ = _run("""
main:
  print(floor(3.7))
  print(ceil(3.2))
""")
        assert output == ["3", "4"]


# --- Functions ---


class TestFunctions:
    def test_function_with_if(self):
        result, output, _ = _run("""
compute abs_val from x: Number returns Number:
  if x is below 0:
    return -x
  else:
    return x

main:
  print(abs_val(-5))
  print(abs_val(3))
""")
        assert output == ["5", "3"]

    def test_function_local_vars(self):
        result, output, _ = _run("""
compute calc from x: Number returns Number:
  given y as x * 2
  given z as y + 1
  return z

main:
  print(calc(5))
""")
        assert output == ["11"]

    def test_early_return(self):
        result, output, _ = _run("""
compute check from x: Number returns Text:
  if x exceeds 100:
    return "high"
  return "low"

main:
  print(check(150))
  print(check(50))
""")
        assert output == ["high", "low"]

    def test_multiple_functions(self):
        result, output, _ = _run("""
compute square from x: Number returns Number:
  return x * x

compute cube from x: Number returns Number:
  return x * square(x)

main:
  print(square(3))
  print(cube(3))
""")
        assert output == ["9", "27"]


# --- Match Expressions ---


class TestMatch:
    def test_match_number(self):
        result, output, _ = _run("""\
compute classify from x: Number returns Number:
  return match x:
    1 -> 10
    2 -> 20
    3 -> 30
    _ -> 0

main:
  print(classify(2))
""")
        assert output == ["20"]

    def test_match_string(self):
        result, output, _ = _run("""\
compute greet from name: Text returns Text:
  return match name:
    "Alice" -> "Hello Alice!"
    "Bob" -> "Hi Bob!"
    _ -> "Hey there!"

main:
  print(greet("Alice"))
  print(greet("Charlie"))
""")
        assert output == ["Hello Alice!", "Hey there!"]


# --- Edge Cases ---


class TestEdgeCases:
    def test_division_result_types(self):
        """Integer division that yields integer."""
        result, output, _ = _run("""
main:
  given x as 10 / 2
  print(x)
""")
        assert output == ["5"]

    def test_float_division(self):
        result, output, _ = _run("""
main:
  given x as 10 / 3
  print(x)
""")
        # Should be float
        assert "3.3333" in output[0]

    def test_string_concatenation(self):
        result, output, _ = _run("""
main:
  given greeting as "hello" + " " + "world"
  print(greeting)
""")
        assert output == ["hello world"]

    def test_boolean_logic(self):
        result, output, _ = _run("""
main:
  given x as true
  given y as false
  if x is true:
    if y is false:
      print("correct")
""")
        assert output == ["correct"]

    def test_nested_function_calls(self):
        result, output, _ = _run("""
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given x as add(add(1, 2), add(3, 4))
  print(x)
""")
        assert output == ["10"]

    def test_list_of_lists(self):
        result, output, _ = _run("""
main:
  given matrix as [[1, 2], [3, 4]]
  print(len(matrix))
""")
        assert output == ["2"]


# --- Parity Tests ---


class TestParitySprint2:
    def test_parity_counter_loop(self):
        _parity("""
main:
  given items as [10, 20, 30]
  for each item in items:
    print(item)
""")

    def test_parity_nested_if(self):
        _parity("""
main:
  given x as 15
  if x exceeds 10:
    if x is below 20:
      print("in range")
""")

    def test_parity_multiple_functions(self):
        _parity("""
compute double from x: Number returns Number:
  return x * 2

compute triple from x: Number returns Number:
  return x * 3

main:
  print(double(5))
  print(triple(5))
  print(double(triple(2)))
""")

    def test_parity_match(self):
        _parity("""\
compute classify from x: Number returns Number:
  return match x:
    1 -> 10
    2 -> 20
    _ -> 0

main:
  print(classify(2))
""")

    def test_parity_string_ops(self):
        _parity("""
main:
  given a as "hello"
  given b as " world"
  given c as a + b
  print(c)
  print(len(c))
""")

    def test_parity_recursive_sum(self):
        _parity("""
compute sum_to from n: Number returns Number:
  if n is at most 0:
    return 0
  else:
    return n + sum_to(n - 1)

main:
  print(sum_to(10))
""")

    def test_parity_builtin_max_min(self):
        _parity("""
main:
  print(max(3, 7))
  print(min(3, 7))
""")
