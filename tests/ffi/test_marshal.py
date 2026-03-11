"""Tests for Sigil ↔ Python type marshaling."""

import pytest

from sigil.errors import SigilRuntimeError
from sigil.ffi.marshal import python_to_sigil, sigil_to_python, wrap_python_callable
from sigil.interpreter.trace import ProgramTrace
from sigil.interpreter.values import Closure, Record, Symbol


# ------------------------------------------------------------------
# sigil_to_python
# ------------------------------------------------------------------


def test_marshal_none_to_python():
    assert sigil_to_python(None) is None


def test_marshal_bool_to_python():
    assert sigil_to_python(True) is True
    assert sigil_to_python(False) is False


def test_marshal_int_to_python():
    assert sigil_to_python(42) == 42


def test_marshal_float_to_python():
    assert sigil_to_python(3.14) == 3.14


def test_marshal_str_to_python():
    assert sigil_to_python("hello") == "hello"


def test_marshal_symbol_to_python():
    assert sigil_to_python(Symbol("active")) == "active"


def test_marshal_record_to_python():
    rec = Record(type_name="Person", fields={"name": "Alice", "age": 30})
    result = sigil_to_python(rec)
    assert result == {"name": "Alice", "age": 30}


def test_marshal_nested_record_to_python():
    inner = Record(type_name=None, fields={"x": 1, "y": 2})
    outer = Record(type_name=None, fields={"point": inner, "label": "origin"})
    result = sigil_to_python(outer)
    assert result == {"point": {"x": 1, "y": 2}, "label": "origin"}


def test_marshal_list_to_python():
    assert sigil_to_python([1, 2, 3]) == [1, 2, 3]


def test_marshal_nested_list_to_python():
    result = sigil_to_python([Symbol("a"), [1, 2]])
    assert result == ["a", [1, 2]]


def test_marshal_closure_to_python_raises():
    closure = Closure(params=("x",), body=(), env=None, name="f")  # type: ignore[arg-type]
    with pytest.raises(SigilRuntimeError, match="Cannot marshal Sigil closures"):
        sigil_to_python(closure)


# ------------------------------------------------------------------
# python_to_sigil
# ------------------------------------------------------------------


def test_marshal_none_from_python():
    assert python_to_sigil(None) is None


def test_marshal_bool_from_python():
    assert python_to_sigil(True) is True
    assert python_to_sigil(False) is False


def test_marshal_int_from_python():
    assert python_to_sigil(42) == 42


def test_marshal_float_from_python():
    assert python_to_sigil(3.14) == 3.14


def test_marshal_str_from_python():
    assert python_to_sigil("hello") == "hello"


def test_marshal_dict_from_python():
    result = python_to_sigil({"name": "Alice", "age": 30})
    assert isinstance(result, Record)
    assert result.fields == {"name": "Alice", "age": 30}
    assert result.type_name is None


def test_marshal_list_from_python():
    result = python_to_sigil([1, "two", 3.0])
    assert result == [1, "two", 3.0]


def test_marshal_tuple_from_python():
    result = python_to_sigil((1, 2, 3))
    assert result == [1, 2, 3]


def test_marshal_callable_from_python():
    def add(a, b):
        return a + b
    result = python_to_sigil(add)
    assert callable(result)


def test_marshal_unknown_type_to_string():
    """Unknown types get converted to their string representation."""
    result = python_to_sigil(set())
    assert isinstance(result, str)


# ------------------------------------------------------------------
# wrap_python_callable
# ------------------------------------------------------------------


def test_wrap_callable_basic():
    def add(a, b):
        return a + b
    wrapped = wrap_python_callable(add)
    result = wrapped([3, 4], ProgramTrace())
    assert result == 7


def test_wrap_callable_returns_record():
    def make_point(x, y):
        return {"x": x, "y": y}
    wrapped = wrap_python_callable(make_point)
    result = wrapped([1, 2], ProgramTrace())
    assert isinstance(result, Record)
    assert result.fields == {"x": 1, "y": 2}


def test_wrap_callable_marshals_symbol_arg():
    def identity(x):
        return x
    wrapped = wrap_python_callable(identity)
    result = wrapped([Symbol("test")], ProgramTrace())
    assert result == "test"


def test_wrap_callable_python_error():
    def boom():
        raise ValueError("bad value")
    wrapped = wrap_python_callable(boom)
    with pytest.raises(SigilRuntimeError, match="Python FFI error"):
        wrapped([], ProgramTrace())
