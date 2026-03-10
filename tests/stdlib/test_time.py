"""Tests for sigil.time standard library module."""

from __future__ import annotations

import time

import pytest

from sigil.interpreter.trace import ProgramTrace
from sigil.stdlib._builtins import (
    stdlib_duration_seconds,
    stdlib_elapsed,
    stdlib_format_timestamp,
    stdlib_now,
    stdlib_now_ms,
)


@pytest.fixture()
def trace():
    return ProgramTrace()


class TestTimeNow:
    def test_now_returns_timestamp(self, trace):
        result = stdlib_now([], trace)
        assert isinstance(result, float)
        assert result > 0

    def test_now_close_to_real_time(self, trace):
        before = time.time()
        result = stdlib_now([], trace)
        after = time.time()
        assert before <= result <= after


class TestTimeNowMs:
    def test_now_ms_returns_milliseconds(self, trace):
        result = stdlib_now_ms([], trace)
        assert isinstance(result, float)
        assert result > 1_000_000_000_000  # post-2001 in ms


class TestFormatTimestamp:
    def test_format_unix_epoch(self, trace):
        result = stdlib_format_timestamp([0], trace)
        assert "1970-01-01" in result

    def test_format_returns_iso_string(self, trace):
        result = stdlib_format_timestamp([1709251200], trace)
        assert isinstance(result, str)
        assert "T" in result  # ISO 8601 has T separator


class TestElapsed:
    def test_elapsed_positive(self, trace):
        result = stdlib_elapsed([100.0, 200.0], trace)
        assert result == 100.0

    def test_elapsed_zero(self, trace):
        result = stdlib_elapsed([50.0, 50.0], trace)
        assert result == 0.0


class TestDurationSeconds:
    def test_duration_seconds(self, trace):
        result = stdlib_duration_seconds([30], trace)
        assert result == 30.0
