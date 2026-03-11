"""Tests for sigil.text standard library module."""

from __future__ import annotations

import pytest

from sigil.interpreter.trace import ProgramTrace
from sigil.stdlib._builtins import (
    STDLIB_TEXT,
    stdlib_ends_with,
    stdlib_join,
    stdlib_length,
    stdlib_lowercase,
    stdlib_replace,
    stdlib_split,
    stdlib_starts_with,
    stdlib_substring,
    stdlib_trim,
    stdlib_uppercase,
)


@pytest.fixture()
def trace():
    return ProgramTrace()


class TestTextLength:
    def test_length_basic(self, trace):
        assert stdlib_length(["hello"], trace) == 5

    def test_length_empty(self, trace):
        assert stdlib_length([""], trace) == 0

    def test_length_with_spaces(self, trace):
        assert stdlib_length(["hello world"], trace) == 11


class TestTextSubstring:
    def test_substring_basic(self, trace):
        assert stdlib_substring(["hello world", 0, 5], trace) == "hello"

    def test_substring_middle(self, trace):
        assert stdlib_substring(["hello world", 6, 11], trace) == "world"


class TestTextSplit:
    def test_split_with_delimiter(self, trace):
        result = stdlib_split(["a,b,c", ","], trace)
        assert result == ["a", "b", "c"]

    def test_split_whitespace(self, trace):
        result = stdlib_split(["hello world"], trace)
        assert result == ["hello", "world"]


class TestTextJoin:
    def test_join_with_separator(self, trace):
        result = stdlib_join([["a", "b", "c"], ", "], trace)
        assert result == "a, b, c"

    def test_join_empty_separator(self, trace):
        result = stdlib_join([["a", "b"]], trace)
        assert result == "ab"


class TestTextCase:
    def test_lowercase(self, trace):
        assert stdlib_lowercase(["HELLO"], trace) == "hello"

    def test_uppercase(self, trace):
        assert stdlib_uppercase(["hello"], trace) == "HELLO"


class TestTextTrim:
    def test_trim_whitespace(self, trace):
        assert stdlib_trim(["  hello  "], trace) == "hello"


class TestTextReplace:
    def test_replace(self, trace):
        assert stdlib_replace(["hello world", "world", "sigil"], trace) == "hello sigil"


class TestTextStartsEndsWith:
    def test_starts_with_true(self, trace):
        assert stdlib_starts_with(["hello world", "hello"], trace) is True

    def test_starts_with_false(self, trace):
        assert stdlib_starts_with(["hello world", "world"], trace) is False

    def test_ends_with_true(self, trace):
        assert stdlib_ends_with(["hello world", "world"], trace) is True

    def test_ends_with_false(self, trace):
        assert stdlib_ends_with(["hello world", "hello"], trace) is False


class TestTextRegistry:
    def test_all_functions_registered(self):
        expected = {
            "length", "substring", "split", "join",
            "lowercase", "uppercase", "trim", "replace",
            "starts_with", "ends_with",
        }
        assert set(STDLIB_TEXT.keys()) == expected
