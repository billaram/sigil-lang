"""Tests for Python FFI module importing and integration."""

import pytest

from sigil.errors import SigilRuntimeError
from sigil.ffi.python_interop import import_python_module, import_python_names
from sigil.interpreter.trace import ProgramTrace
from sigil.interpreter.values import Record
from sigil.lexer.lexer import tokenize
from sigil.parser.parser import parse


def run(source, input_data=None):
    """Helper: tokenize → parse → evaluate."""
    from sigil.interpreter.evaluator import evaluate
    tokens = tokenize(source)
    program = parse(tokens)
    return evaluate(program, input_data or {})


# ------------------------------------------------------------------
# import_python_module
# ------------------------------------------------------------------


def test_import_math_module():
    result = import_python_module("math")
    assert "sqrt" in result
    assert "pi" in result
    assert callable(result["sqrt"])


def test_import_json_module():
    result = import_python_module("json")
    assert "loads" in result
    assert "dumps" in result


def test_import_nonexistent_module():
    with pytest.raises(SigilRuntimeError, match="Cannot import Python module"):
        import_python_module("nonexistent_module_xyz_123")


def test_import_dotted_module():
    result = import_python_module("os.path")
    assert "join" in result


# ------------------------------------------------------------------
# import_python_names
# ------------------------------------------------------------------


def test_import_specific_names():
    result = import_python_names("math", ("sqrt", "pi"))
    assert "sqrt" in result
    assert "pi" in result
    assert len(result) == 2


def test_import_nonexistent_name():
    with pytest.raises(SigilRuntimeError, match="has no attribute"):
        import_python_names("math", ("nonexistent_func_xyz",))


# ------------------------------------------------------------------
# Calling imported Python functions
# ------------------------------------------------------------------


def test_call_imported_math_sqrt():
    bindings = import_python_module("math")
    sqrt = bindings["sqrt"]
    result = sqrt([144], ProgramTrace())
    assert result == 12.0


def test_call_imported_json_loads():
    bindings = import_python_module("json")
    loads = bindings["loads"]
    result = loads(['{"name": "sigil", "version": 1}'], ProgramTrace())
    assert isinstance(result, Record)
    assert result.fields["name"] == "sigil"
    assert result.fields["version"] == 1


def test_call_imported_json_dumps():
    bindings = import_python_module("json")
    dumps = bindings["dumps"]
    result = dumps([{"key": "value"}], ProgramTrace())
    assert isinstance(result, str)


# ------------------------------------------------------------------
# End-to-end: Sigil source with Python imports
# ------------------------------------------------------------------


def test_e2e_import_python_math():
    source = """
import python math

main:
  given result as math.sqrt(144)
  print(result)
"""
    result, trace = run(source)
    assert "12.0" in trace.output_lines


def test_e2e_import_python_json():
    source = """
import python json

main:
  given data as json.loads("{}")
  print(data)
"""
    result, trace = run(source)
    assert len(trace.output_lines) > 0


def test_e2e_from_python_import():
    source = """
from python math import sqrt, floor

main:
  given result as sqrt(144)
  print(result)
"""
    result, trace = run(source)
    assert "12.0" in trace.output_lines


def test_e2e_import_python_alias():
    source = """
import python math as m

main:
  given result as m.sqrt(25)
  print(result)
"""
    result, trace = run(source)
    assert "5.0" in trace.output_lines


def test_e2e_python_missing_module_graceful():
    """Missing Python modules bind an empty record — errors on use, not import."""
    source = """
import python nonexistent_module_xyz

main:
  print("reached")
"""
    result, trace = run(source)
    assert "reached" in trace.output_lines


def test_e2e_python_missing_module_errors_on_call():
    """Calling a function from a missing module raises at call time."""
    source = """
import python nonexistent_module_xyz

main:
  given x as nonexistent_module_xyz.func(1)
  print(x)
"""
    # Field access on empty record returns _UNBOUND, which isn't callable
    with pytest.raises(SigilRuntimeError):
        run(source)
