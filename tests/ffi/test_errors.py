"""Tests for Python FFI error translation."""

from sigil.errors import SigilRuntimeError
from sigil.ffi.errors import translate_python_error


def test_translate_value_error():
    exc = ValueError("bad value")
    result = translate_python_error(exc, "calling sqrt")
    assert isinstance(result, SigilRuntimeError)
    assert "Python FFI error" in str(result)
    assert "ValueError" in str(result)
    assert "bad value" in str(result)
    assert "calling sqrt" in str(result)


def test_translate_preserves_cause():
    original = TypeError("wrong type")
    result = translate_python_error(original, "calling func")
    assert result.__cause__ is original


def test_translate_import_error():
    exc = ImportError("No module named 'foo'")
    result = translate_python_error(exc, "importing 'foo'")
    assert "ImportError" in str(result)
    assert "importing 'foo'" in str(result)


def test_translate_runtime_error():
    exc = RuntimeError("something broke")
    result = translate_python_error(exc, "doing something")
    assert "RuntimeError" in str(result)


def test_translate_generic_exception():
    exc = Exception("generic")
    result = translate_python_error(exc, "test")
    assert isinstance(result, SigilRuntimeError)
