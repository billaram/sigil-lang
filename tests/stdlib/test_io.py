"""Tests for sigil.io standard library module."""

from __future__ import annotations

import json

import pytest

from sigil.interpreter.trace import ProgramTrace
from sigil.interpreter.values import Record
from sigil.stdlib._builtins import (
    stdlib_file_exists,
    stdlib_parse_json,
    stdlib_read_file,
    stdlib_to_json,
    stdlib_write_file,
)


@pytest.fixture()
def trace():
    return ProgramTrace()


class TestReadFile:
    def test_read_existing_file(self, trace, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = stdlib_read_file([str(f)], trace)
        assert result == "hello world"

    def test_read_nonexistent_file(self, trace, tmp_path):
        with pytest.raises(FileNotFoundError):
            stdlib_read_file([str(tmp_path / "nope.txt")], trace)


class TestWriteFile:
    def test_write_creates_file(self, trace, tmp_path):
        f = tmp_path / "output.txt"
        stdlib_write_file([str(f), "data"], trace)
        assert f.read_text() == "data"

    def test_write_overwrites_existing(self, trace, tmp_path):
        f = tmp_path / "output.txt"
        f.write_text("old")
        stdlib_write_file([str(f), "new"], trace)
        assert f.read_text() == "new"


class TestFileExists:
    def test_file_exists_true(self, trace, tmp_path):
        f = tmp_path / "exists.txt"
        f.write_text("hi")
        assert stdlib_file_exists([str(f)], trace) is True

    def test_file_exists_false(self, trace, tmp_path):
        assert stdlib_file_exists([str(tmp_path / "nope.txt")], trace) is False


class TestParseJson:
    def test_parse_object(self, trace):
        result = stdlib_parse_json(['{"name": "Alice", "age": 30}'], trace)
        assert isinstance(result, Record)
        assert result.fields["name"] == "Alice"
        assert result.fields["age"] == 30

    def test_parse_list(self, trace):
        result = stdlib_parse_json(["[1, 2, 3]"], trace)
        assert result == [1, 2, 3]

    def test_parse_nested(self, trace):
        result = stdlib_parse_json(['{"items": [1, 2]}'], trace)
        assert isinstance(result, Record)
        assert result.fields["items"] == [1, 2]


class TestToJson:
    def test_to_json_number(self, trace):
        result = stdlib_to_json([42], trace)
        assert result == "42"

    def test_to_json_string(self, trace):
        result = stdlib_to_json(["hello"], trace)
        assert result == '"hello"'

    def test_to_json_record(self, trace):
        rec = Record(None, {"x": 1, "y": 2})
        result = stdlib_to_json([rec], trace)
        data = json.loads(result)
        assert data == {"x": 1, "y": 2}
