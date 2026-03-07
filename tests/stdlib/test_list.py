"""Tests for sigil.list standard library module."""

from __future__ import annotations

import pytest

from sigil.interpreter.trace import ProgramTrace
from sigil.interpreter.values import Record
from sigil.stdlib._builtins import (
    STDLIB_LIST,
    stdlib_count,
    stdlib_flatten,
    stdlib_range,
    stdlib_reverse,
    stdlib_sum,
    stdlib_unique,
    stdlib_zip_lists,
)


@pytest.fixture()
def trace():
    return ProgramTrace()


class TestListRange:
    def test_range_single_arg(self, trace):
        assert stdlib_range([5], trace) == [0, 1, 2, 3, 4]

    def test_range_two_args(self, trace):
        assert stdlib_range([2, 5], trace) == [2, 3, 4]

    def test_range_three_args(self, trace):
        assert stdlib_range([0, 10, 3], trace) == [0, 3, 6, 9]

    def test_range_empty(self, trace):
        assert stdlib_range([0], trace) == []


class TestListReverse:
    def test_reverse(self, trace):
        assert stdlib_reverse([[3, 1, 2]], trace) == [2, 1, 3]

    def test_reverse_empty(self, trace):
        assert stdlib_reverse([[]], trace) == []


class TestListFlatten:
    def test_flatten_nested(self, trace):
        assert stdlib_flatten([[[1, 2], [3, 4], [5]]], trace) == [1, 2, 3, 4, 5]

    def test_flatten_mixed(self, trace):
        assert stdlib_flatten([[[1, 2], 3, [4]]], trace) == [1, 2, 3, 4]

    def test_flatten_already_flat(self, trace):
        assert stdlib_flatten([[1, 2, 3]], trace) == [1, 2, 3]


class TestListUnique:
    def test_unique_integers(self, trace):
        assert stdlib_unique([[1, 2, 2, 3, 1]], trace) == [1, 2, 3]

    def test_unique_strings(self, trace):
        assert stdlib_unique([["a", "b", "a", "c"]], trace) == ["a", "b", "c"]

    def test_unique_no_duplicates(self, trace):
        assert stdlib_unique([[1, 2, 3]], trace) == [1, 2, 3]


class TestListZip:
    def test_zip_basic(self, trace):
        result = stdlib_zip_lists([[1, 2, 3], ["a", "b", "c"]], trace)
        assert len(result) == 3
        assert isinstance(result[0], Record)
        assert result[0].fields["first"] == 1
        assert result[0].fields["second"] == "a"

    def test_zip_unequal_length(self, trace):
        result = stdlib_zip_lists([[1, 2], ["a", "b", "c"]], trace)
        assert len(result) == 2


class TestListSum:
    def test_sum_integers(self, trace):
        assert stdlib_sum([[1, 2, 3, 4]], trace) == 10

    def test_sum_empty(self, trace):
        assert stdlib_sum([[]], trace) == 0


class TestListCount:
    def test_count(self, trace):
        assert stdlib_count([[1, 2, 3]], trace) == 3

    def test_count_empty(self, trace):
        assert stdlib_count([[]], trace) == 0


class TestListRegistry:
    def test_all_functions_registered(self):
        expected = {"range", "reverse", "flatten", "unique", "zip", "sum", "count", "length"}
        assert set(STDLIB_LIST.keys()) == expected
