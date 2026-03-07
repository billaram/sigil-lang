"""Tests for sigil.logic standard library module."""

from __future__ import annotations

import pytest

from sigil.interpreter.trace import ProgramTrace
from sigil.interpreter.values import Record, Symbol
from sigil.stdlib._builtins import (
    STDLIB_LOGIC,
    stdlib_implies,
    stdlib_is_list,
    stdlib_is_number,
    stdlib_is_text,
    stdlib_nand,
    stdlib_type_of,
    stdlib_xor,
)


@pytest.fixture()
def trace():
    return ProgramTrace()


class TestLogicXor:
    def test_xor_tt(self, trace):
        assert stdlib_xor([True, True], trace) is False

    def test_xor_tf(self, trace):
        assert stdlib_xor([True, False], trace) is True

    def test_xor_ft(self, trace):
        assert stdlib_xor([False, True], trace) is True

    def test_xor_ff(self, trace):
        assert stdlib_xor([False, False], trace) is False


class TestLogicImplies:
    def test_implies_tt(self, trace):
        assert stdlib_implies([True, True], trace) is True

    def test_implies_tf(self, trace):
        assert stdlib_implies([True, False], trace) is False

    def test_implies_ft(self, trace):
        assert stdlib_implies([False, True], trace) is True

    def test_implies_ff(self, trace):
        assert stdlib_implies([False, False], trace) is True


class TestLogicNand:
    def test_nand_tt(self, trace):
        assert stdlib_nand([True, True], trace) is False

    def test_nand_tf(self, trace):
        assert stdlib_nand([True, False], trace) is True


class TestLogicTypeOf:
    def test_type_of_number_int(self, trace):
        result = stdlib_type_of([42], trace)
        assert isinstance(result, Symbol)
        assert result.name == "Number"

    def test_type_of_number_float(self, trace):
        result = stdlib_type_of([3.14], trace)
        assert isinstance(result, Symbol)
        assert result.name == "Number"

    def test_type_of_text(self, trace):
        result = stdlib_type_of(["hello"], trace)
        assert isinstance(result, Symbol)
        assert result.name == "Text"

    def test_type_of_bool(self, trace):
        result = stdlib_type_of([True], trace)
        assert isinstance(result, Symbol)
        assert result.name == "Boolean"

    def test_type_of_symbol(self, trace):
        result = stdlib_type_of([Symbol("active")], trace)
        assert isinstance(result, Symbol)
        assert result.name == "Symbol"

    def test_type_of_record(self, trace):
        result = stdlib_type_of([Record(None, {"x": 1})], trace)
        assert isinstance(result, Symbol)
        assert result.name == "Record"

    def test_type_of_list(self, trace):
        result = stdlib_type_of([[1, 2, 3]], trace)
        assert isinstance(result, Symbol)
        assert result.name == "List"

    def test_type_of_none(self, trace):
        result = stdlib_type_of([None], trace)
        assert isinstance(result, Symbol)
        assert result.name == "None"


class TestLogicTypeChecks:
    def test_is_number_true(self, trace):
        assert stdlib_is_number([42], trace) is True

    def test_is_number_false(self, trace):
        assert stdlib_is_number(["hello"], trace) is False

    def test_is_text_true(self, trace):
        assert stdlib_is_text(["hello"], trace) is True

    def test_is_text_false(self, trace):
        assert stdlib_is_text([42], trace) is False

    def test_is_list_true(self, trace):
        assert stdlib_is_list([[1, 2]], trace) is True

    def test_is_list_false(self, trace):
        assert stdlib_is_list([42], trace) is False


class TestLogicRegistry:
    def test_all_functions_registered(self):
        expected = {"xor", "implies", "nand", "type_of", "is_number", "is_text", "is_list"}
        assert set(STDLIB_LOGIC.keys()) == expected
