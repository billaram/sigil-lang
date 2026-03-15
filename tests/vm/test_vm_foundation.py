"""Tests for Sprint 1: VM Foundation — opcodes, expressions, basic VM."""

import pytest

from sigil.lexer import tokenize
from sigil.parser import parse
from sigil.vm.compiler import VMCompiler
from sigil.vm.runner import compile_and_run


def _compile(source: str) -> dict:
    """Helper: parse source and compile to bytecode chunk."""
    tokens = tokenize(source)
    program = parse(tokens)
    compiler = VMCompiler()
    return compiler.compile(program)


def _run(source: str, input_data=None):
    """Helper: compile and run, return (result, output_lines)."""
    tokens = tokenize(source)
    program = parse(tokens)
    result, output_lines, bindings = compile_and_run(program, input_data)
    return result, output_lines, bindings


# --- Compiler Unit Tests ---


class TestCompilerBasics:
    def test_compile_empty_program(self):
        chunk = _compile("")
        assert "code" in chunk
        assert "strings" in chunk
        assert chunk["code"][-1][0] == "Halt"

    def test_compile_const_int(self):
        chunk = _compile("define MAX as 100")
        # Should have PushInt(100) and Store
        opcodes = [op[0] for op in chunk["code"]]
        assert "PushInt" in opcodes
        assert "Store" in opcodes

    def test_compile_const_float(self):
        chunk = _compile("define PI as 3.14")
        has_float = any(op[0] == "PushFloat" and op[1] == 3.14 for op in chunk["code"])
        assert has_float

    def test_compile_const_string(self):
        chunk = _compile('define GREETING as "hello"')
        has_string = any(op[0] == "PushString" for op in chunk["code"])
        assert has_string
        assert "hello" in chunk["strings"]

    def test_compile_const_bool(self):
        chunk = _compile("define FLAG as true")
        has_bool = any(op[0] == "PushBool" and op[1] is True for op in chunk["code"])
        assert has_bool

    def test_compile_symbol(self):
        chunk = _compile("define STATUS as :active")
        has_symbol = any(op[0] == "PushSymbol" for op in chunk["code"])
        assert has_symbol
        assert "active" in chunk["strings"]


class TestCompilerExpressions:
    def test_compile_addition(self):
        chunk = _compile("""
compute add from a: Number, b: Number returns Number:
  return a + b
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Add" in opcodes
        assert "Return" in opcodes

    def test_compile_subtraction(self):
        chunk = _compile("""
compute sub from a: Number, b: Number returns Number:
  return a - b
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Sub" in opcodes

    def test_compile_multiplication(self):
        chunk = _compile("""
compute mul from a: Number, b: Number returns Number:
  return a * b
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Mul" in opcodes

    def test_compile_division(self):
        chunk = _compile("""
compute div from a: Number, b: Number returns Number:
  return a / b
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Div" in opcodes

    def test_compile_negation(self):
        chunk = _compile("""
compute neg from a: Number returns Number:
  return -a
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Neg" in opcodes

    def test_compile_list_literal(self):
        chunk = _compile("""
main:
  given x as [1, 2, 3]
  print(x)
""")
        has_list = any(op[0] == "PushList" and op[1] == 3 for op in chunk["code"])
        assert has_list

    def test_compile_empty_list(self):
        chunk = _compile("""
main:
  given x as empty list
  print(x)
""")
        has_empty_list = any(op[0] == "PushList" and op[1] == 0 for op in chunk["code"])
        assert has_empty_list

    def test_compile_record(self):
        chunk = _compile("""
main:
  given p as {name: "Alice", age: 30}
  print(p)
""")
        has_record = any(op[0] == "PushRecord" for op in chunk["code"])
        assert has_record

    def test_compile_field_access(self):
        chunk = _compile("""
main:
  given p as {name: "Alice"}
  print(p.name)
""")
        has_field = any(op[0] == "LoadField" for op in chunk["code"])
        assert has_field


class TestCompilerFunctions:
    def test_compile_compute_function(self):
        chunk = _compile("""
compute square from x: Number returns Number:
  return x * x
""")
        assert "square" in chunk["functions"]
        func = chunk["functions"]["square"]
        assert func["param_count"] == 1
        assert func["param_names"] == ["x"]

    def test_compile_multi_param_function(self):
        chunk = _compile("""
compute add from a: Number, b: Number returns Number:
  return a + b
""")
        assert "add" in chunk["functions"]
        func = chunk["functions"]["add"]
        assert func["param_count"] == 2

    def test_compile_function_call(self):
        chunk = _compile("""
compute double from x: Number returns Number:
  return x * 2

main:
  given result as double(5)
  print(result)
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Call" in opcodes


class TestCompilerStatements:
    def test_compile_given_as(self):
        chunk = _compile("""
main:
  given x as 42
  print(x)
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Store" in opcodes

    def test_compile_if_statement(self):
        chunk = _compile("""
compute check from x: Number returns Number:
  if x exceeds 10:
    return 1
  else:
    return 0
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "JumpIfFalse" in opcodes

    def test_compile_for_loop(self):
        chunk = _compile("""
main:
  given items as [1, 2, 3]
  for each item in items:
    print(item)
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Jump" in opcodes
        assert "IndexAccess" in opcodes

    def test_compile_return(self):
        chunk = _compile("""
compute identity from x: Number returns Number:
  return x
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Return" in opcodes

    def test_compile_becomes(self):
        chunk = _compile("""
main:
  given x as 1
  x becomes 2
  print(x)
""")
        opcodes = [op[0] for op in chunk["code"]]
        assert "Mutate" in opcodes


class TestCompilerRules:
    def test_compile_simple_rule(self):
        chunk = _compile("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
""")
        assert len(chunk["rules"]) == 1
        rule = chunk["rules"][0]
        assert rule["name"] == "high_temp"
        assert rule["priority"] == 0

    def test_compile_rule_with_priority(self):
        chunk = _compile("""
rule high_temp with priority 10:
  when temperature exceeds 100
  then status is :hot
""")
        assert chunk["rules"][0]["priority"] == 10

    def test_compile_rule_with_explain(self):
        chunk = _compile("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
  explain "Temperature exceeded threshold"
""")
        rule = chunk["rules"][0]
        assert rule["explain_idx"] is not None

    def test_compile_multiple_rules(self):
        chunk = _compile("""
rule hot:
  when temperature exceeds 100
  then status is :hot

rule cold:
  when temperature is below 0
  then status is :cold
""")
        assert len(chunk["rules"]) == 2


# --- VM Execution Tests ---


class TestVMArithmetic:
    def test_add_integers(self):
        result, output, _ = _run("""
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given x as add(3, 4)
  print(x)
""")
        assert output == ["7"]

    def test_subtract(self):
        result, output, _ = _run("""
compute sub from a: Number, b: Number returns Number:
  return a - b

main:
  given x as sub(10, 3)
  print(x)
""")
        assert output == ["7"]

    def test_multiply(self):
        result, output, _ = _run("""
compute mul from a: Number, b: Number returns Number:
  return a * b

main:
  given x as mul(6, 7)
  print(x)
""")
        assert output == ["42"]

    def test_divide(self):
        result, output, _ = _run("""
compute div from a: Number, b: Number returns Number:
  return a / b

main:
  given x as div(10, 2)
  print(x)
""")
        assert output == ["5"]

    def test_float_arithmetic(self):
        result, output, _ = _run("""
main:
  given x as 3.14 * 2.0
  print(x)
""")
        assert output == ["6.28"]

    def test_complex_expression(self):
        result, output, _ = _run("""
compute calc from a: Number, b: Number, c: Number returns Number:
  return a + b * c

main:
  given x as calc(1, 2, 3)
  print(x)
""")
        assert output == ["7"]

    def test_negation(self):
        result, output, _ = _run("""
main:
  given x as -5
  print(x)
""")
        assert output == ["-5"]

    def test_mixed_int_float(self):
        result, output, _ = _run("""
main:
  given x as 3 + 2.5
  print(x)
""")
        assert output == ["5.5"]


class TestVMVariables:
    def test_define_and_use_constant(self):
        result, output, _ = _run("""
define MAX as 100

main:
  print(MAX)
""")
        assert output == ["100"]

    def test_given_as_binding(self):
        result, output, _ = _run("""
main:
  given x as 42
  print(x)
""")
        assert output == ["42"]

    def test_multiple_bindings(self):
        result, output, _ = _run("""
main:
  given x as 10
  given y as 20
  given z as x + y
  print(z)
""")
        assert output == ["30"]

    def test_string_binding(self):
        result, output, _ = _run("""
main:
  given name as "Alice"
  print(name)
""")
        assert output == ["Alice"]


class TestVMComputeFunctions:
    def test_simple_function(self):
        result, output, _ = _run("""
compute square from x: Number returns Number:
  return x * x

main:
  given y as square(5)
  print(y)
""")
        assert output == ["25"]

    def test_two_param_function(self):
        result, output, _ = _run("""
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given y as add(3, 4)
  print(y)
""")
        assert output == ["7"]

    def test_function_calling_function(self):
        result, output, _ = _run("""
compute double from x: Number returns Number:
  return x * 2

compute quadruple from x: Number returns Number:
  return double(double(x))

main:
  given y as quadruple(3)
  print(y)
""")
        assert output == ["12"]

    def test_recursive_function(self):
        result, output, _ = _run("""
compute factorial from n: Number returns Number:
  if n is at most 1:
    return 1
  else:
    return n * factorial(n - 1)

main:
  given y as factorial(5)
  print(y)
""")
        assert output == ["120"]

    def test_fibonacci(self):
        result, output, _ = _run("""
compute fib from n: Number returns Number:
  if n is at most 1:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

main:
  given y as fib(10)
  print(y)
""")
        assert output == ["55"]


class TestVMControlFlow:
    def test_if_true(self):
        result, output, _ = _run("""
main:
  given x as 15
  if x exceeds 10:
    print("big")
""")
        assert output == ["big"]

    def test_if_false(self):
        result, output, _ = _run("""
main:
  given x as 5
  if x exceeds 10:
    print("big")
  else:
    print("small")
""")
        assert output == ["small"]

    def test_for_loop(self):
        result, output, _ = _run("""
main:
  given items as [1, 2, 3]
  for each item in items:
    print(item)
""")
        assert output == ["1", "2", "3"]

    def test_becomes(self):
        result, output, _ = _run("""
main:
  given x as 1
  x becomes 2
  print(x)
""")
        assert output == ["2"]


class TestVMBuiltins:
    def test_print_string(self):
        result, output, _ = _run("""
main:
  print("hello world")
""")
        assert output == ["hello world"]

    def test_print_number(self):
        result, output, _ = _run("""
main:
  print(42)
""")
        assert output == ["42"]

    def test_len_list(self):
        result, output, _ = _run("""
main:
  given x as len([1, 2, 3])
  print(x)
""")
        assert output == ["3"]

    def test_max_two(self):
        result, output, _ = _run("""
main:
  given x as max(3, 7)
  print(x)
""")
        assert output == ["7"]

    def test_min_two(self):
        result, output, _ = _run("""
main:
  given x as min(3, 7)
  print(x)
""")
        assert output == ["3"]

    def test_abs(self):
        result, output, _ = _run("""
main:
  given x as abs(-5)
  print(x)
""")
        assert output == ["5"]


class TestVMLists:
    def test_list_literal(self):
        result, output, _ = _run("""
main:
  given x as [10, 20, 30]
  print(x)
""")
        assert output == ["[10, 20, 30]"]

    def test_empty_list(self):
        result, output, _ = _run("""
main:
  given x as empty list
  print(len(x))
""")
        assert output == ["0"]

    def test_list_index_access(self):
        result, output, _ = _run("""
main:
  given x as [10, 20, 30]
  print(x[1])
""")
        assert output == ["20"]


class TestVMRecords:
    def test_record_literal(self):
        result, output, bindings = _run("""
main:
  given p as {name: "Alice", age: 30}
  print(p.name)
""")
        assert output == ["Alice"]

    def test_record_field_access(self):
        result, output, _ = _run("""
main:
  given p as {x: 10, y: 20}
  given sum as p.x + p.y
  print(sum)
""")
        assert output == ["30"]


class TestVMSymbols:
    def test_symbol_literal(self):
        result, output, _ = _run("""
main:
  given s as :active
  print(s)
""")
        assert output == [":active"]


class TestVMInputData:
    def test_input_number(self):
        result, output, _ = _run("""
main:
  given x from input
  print(x)
""", {"x": 42})
        assert output == ["42"]

    def test_input_string(self):
        result, output, _ = _run("""
main:
  given name from input
  print(name)
""", {"name": "Bob"})
        assert output == ["Bob"]


class TestVMRules:
    def test_simple_rule_fires(self):
        result, output, bindings = _run("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
""", {"temperature": 150})
        # Status should be set by the rule
        status = bindings.get("status")
        assert status is not None

    def test_rule_does_not_fire(self):
        result, output, bindings = _run("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
""", {"temperature": 50})
        # Status should NOT be set
        status = bindings.get("status")
        assert status is None

    def test_multiple_rules_priority(self):
        result, output, bindings = _run("""
rule warm with priority 5:
  when temperature exceeds 50
  then alert is :warm

rule hot with priority 10:
  when temperature exceeds 100
  then alert is :hot
""", {"temperature": 150})
        # Both rules should fire (different targets)
        alert = bindings.get("alert")
        assert alert is not None

    def test_rule_with_explain(self):
        """Explain strings are recorded in trace, not output."""
        result, output, bindings = _run("""
rule high_temp:
  when temperature exceeds 100
  then status is :hot
  explain "Temperature exceeded threshold"
""", {"temperature": 150})
        assert bindings.get("status") is not None


class TestVMConditions:
    def test_exceeds(self):
        result, output, bindings = _run("""
rule test_rule:
  when x exceeds 10
  then result is :yes
""", {"x": 15})
        assert bindings.get("result") is not None

    def test_below(self):
        result, output, bindings = _run("""
rule test_rule:
  when x is below 10
  then result is :yes
""", {"x": 5})
        assert bindings.get("result") is not None

    def test_is_comparison(self):
        from sigil.interpreter.values import Symbol
        result, output, bindings = _run("""
rule test_rule:
  when status is :active
  then result is :matched
""", {"status": Symbol("active")})
        assert bindings.get("result") is not None

    def test_between(self):
        result, output, bindings = _run("""
rule test_rule:
  when x is between 10 and 20
  then result is :yes
""", {"x": 15})
        assert bindings.get("result") is not None


# --- Parity Tests (VM vs tree-walker) ---


class TestParity:
    def _run_both(self, source, input_data=None):
        """Run with both tree-walker and VM, return both results."""
        from sigil.interpreter import evaluate

        tokens = tokenize(source)
        program = parse(tokens)

        # Tree-walker
        tw_result, tw_trace = evaluate(program, input_data)

        # VM
        vm_result, vm_output, vm_bindings = compile_and_run(program, input_data)

        return tw_trace.output_lines, vm_output

    def test_parity_simple_arithmetic(self):
        tw_out, vm_out = self._run_both("""
compute add from a: Number, b: Number returns Number:
  return a + b

main:
  given x as add(3, 4)
  print(x)
""")
        assert tw_out == vm_out

    def test_parity_constant(self):
        tw_out, vm_out = self._run_both("""
define MAX as 100

main:
  print(MAX)
""")
        assert tw_out == vm_out

    def test_parity_if_else(self):
        tw_out, vm_out = self._run_both("""
main:
  given x as 5
  if x exceeds 10:
    print("big")
  else:
    print("small")
""")
        assert tw_out == vm_out

    def test_parity_for_loop(self):
        tw_out, vm_out = self._run_both("""
main:
  given items as [1, 2, 3]
  for each item in items:
    print(item)
""")
        assert tw_out == vm_out

    def test_parity_fibonacci(self):
        tw_out, vm_out = self._run_both("""
compute fib from n: Number returns Number:
  if n is at most 1:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

main:
  given y as fib(10)
  print(y)
""")
        assert tw_out == vm_out

    def test_parity_factorial(self):
        tw_out, vm_out = self._run_both("""
compute factorial from n: Number returns Number:
  if n is at most 1:
    return 1
  else:
    return n * factorial(n - 1)

main:
  given y as factorial(6)
  print(y)
""")
        assert tw_out == vm_out

    def test_parity_list_operations(self):
        tw_out, vm_out = self._run_both("""
main:
  given items as [10, 20, 30]
  print(len(items))
  print(items[0])
  print(items[2])
""")
        assert tw_out == vm_out
