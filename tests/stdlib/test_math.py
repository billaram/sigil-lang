"""Tests for sigil.math standard library module."""

from __future__ import annotations

import math

import pytest

from sigil.interpreter.trace import ProgramTrace
from sigil.stdlib._builtins import (
    STDLIB_MATH,
    stdlib_abs,
    stdlib_ceil,
    stdlib_cos,
    stdlib_floor,
    stdlib_log,
    stdlib_pow,
    stdlib_round,
    stdlib_sin,
    stdlib_sqrt,
)


@pytest.fixture()
def trace():
    return ProgramTrace()


class TestMathSqrt:
    def test_sqrt_perfect_square(self, trace):
        assert stdlib_sqrt([25], trace) == 5.0

    def test_sqrt_non_perfect_square(self, trace):
        result = stdlib_sqrt([2], trace)
        assert abs(result - math.sqrt(2)) < 1e-10

    def test_sqrt_zero(self, trace):
        assert stdlib_sqrt([0], trace) == 0.0


class TestMathAbs:
    def test_abs_negative(self, trace):
        assert stdlib_abs([-5], trace) == 5

    def test_abs_positive(self, trace):
        assert stdlib_abs([5], trace) == 5

    def test_abs_zero(self, trace):
        assert stdlib_abs([0], trace) == 0

    def test_abs_float(self, trace):
        assert stdlib_abs([-3.14], trace) == 3.14


class TestMathFloorCeil:
    def test_floor(self, trace):
        assert stdlib_floor([3.7], trace) == 3

    def test_floor_negative(self, trace):
        assert stdlib_floor([-3.2], trace) == -4

    def test_ceil(self, trace):
        assert stdlib_ceil([3.2], trace) == 4

    def test_ceil_negative(self, trace):
        assert stdlib_ceil([-3.7], trace) == -3


class TestMathRound:
    def test_round_no_decimals(self, trace):
        assert stdlib_round([3.7], trace) == 4

    def test_round_with_decimals(self, trace):
        assert stdlib_round([3.14159, 2], trace) == 3.14


class TestMathPow:
    def test_pow_integer(self, trace):
        assert stdlib_pow([2, 3], trace) == 8

    def test_pow_fractional(self, trace):
        result = stdlib_pow([4, 0.5], trace)
        assert abs(result - 2.0) < 1e-10


class TestMathLog:
    def test_log_e(self, trace):
        result = stdlib_log([math.e], trace)
        assert abs(result - 1.0) < 1e-10


class TestMathTrig:
    def test_sin_zero(self, trace):
        assert abs(stdlib_sin([0], trace)) < 1e-10

    def test_cos_zero(self, trace):
        assert abs(stdlib_cos([0], trace) - 1.0) < 1e-10

    def test_sin_pi_half(self, trace):
        assert abs(stdlib_sin([math.pi / 2], trace) - 1.0) < 1e-10


class TestMathConstants:
    def test_pi(self):
        assert STDLIB_MATH["PI"] == math.pi

    def test_e(self):
        assert STDLIB_MATH["E"] == math.e


class TestMathRegistry:
    def test_all_functions_registered(self):
        expected = {"sqrt", "abs", "floor", "ceil", "round", "pow", "log", "sin", "cos", "PI", "E"}
        assert set(STDLIB_MATH.keys()) == expected
