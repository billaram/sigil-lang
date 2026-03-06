"""Tests for Sigil runtime values."""

from sigil.interpreter.values import (
    Record,
    Symbol,
    Variant,
    format_value,
    values_equal,
)


class TestSymbol:
    def test_str(self):
        assert str(Symbol("active")) == ":active"

    def test_repr(self):
        assert repr(Symbol("active")) == "Symbol('active')"

    def test_equality(self):
        assert Symbol("active") == Symbol("active")

    def test_inequality(self):
        assert Symbol("active") != Symbol("inactive")

    def test_frozen(self):
        import pytest
        s = Symbol("test")
        with pytest.raises(AttributeError):
            s.name = "other"  # type: ignore[misc]


class TestRecord:
    def test_str_unnamed(self):
        r = Record(type_name=None, fields={"x": 1, "y": 2})
        assert str(r) == "record(x: 1, y: 2)"

    def test_str_named(self):
        r = Record(type_name="Point", fields={"x": 1, "y": 2})
        assert str(r) == "Point(x: 1, y: 2)"

    def test_empty_record(self):
        r = Record(type_name=None, fields={})
        assert str(r) == "record()"

    def test_nested_record(self):
        inner = Record(type_name=None, fields={"z": 3})
        outer = Record(type_name=None, fields={"inner": inner})
        assert "record(z: 3)" in str(outer)


class TestVariant:
    def test_str_no_fields(self):
        v = Variant(type_name="Color", variant_name="red", fields={})
        assert str(v) == "Color.red"

    def test_str_with_fields(self):
        v = Variant(type_name="Decision", variant_name="approved", fields={"rate": 4.5})
        assert str(v) == "Decision.approved(rate: 4.5)"


class TestFormatValue:
    def test_none(self):
        assert format_value(None) == "none"

    def test_true(self):
        assert format_value(True) == "true"

    def test_false(self):
        assert format_value(False) == "false"

    def test_int(self):
        assert format_value(42) == "42"

    def test_float(self):
        assert format_value(3.14) == "3.14"

    def test_string(self):
        assert format_value("hello") == '"hello"'

    def test_symbol(self):
        assert format_value(Symbol("active")) == ":active"

    def test_list(self):
        assert format_value([1, 2, 3]) == "[1, 2, 3]"

    def test_empty_list(self):
        assert format_value([]) == "[]"

    def test_nested_list(self):
        assert format_value([[1, 2], [3]]) == "[[1, 2], [3]]"


class TestValuesEqual:
    def test_symbols(self):
        assert values_equal(Symbol("a"), Symbol("a"))
        assert not values_equal(Symbol("a"), Symbol("b"))

    def test_records(self):
        r1 = Record(type_name=None, fields={"x": 1})
        r2 = Record(type_name=None, fields={"x": 1})
        r3 = Record(type_name=None, fields={"x": 2})
        assert values_equal(r1, r2)
        assert not values_equal(r1, r3)

    def test_variants(self):
        v1 = Variant("T", "a", {"x": 1})
        v2 = Variant("T", "a", {"x": 1})
        v3 = Variant("T", "b", {"x": 1})
        assert values_equal(v1, v2)
        assert not values_equal(v1, v3)

    def test_lists(self):
        assert values_equal([1, 2], [1, 2])
        assert not values_equal([1, 2], [1, 3])
        assert not values_equal([1], [1, 2])

    def test_primitives(self):
        assert values_equal(1, 1)
        assert not values_equal(1, 2)
        assert values_equal("a", "a")
        assert values_equal(True, True)
