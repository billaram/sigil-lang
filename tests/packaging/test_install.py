"""Tests that the sigil package imports and CLI entry points work."""

from __future__ import annotations


class TestImports:
    def test_import_sigil(self):
        import sigil  # noqa: F401

    def test_import_lexer(self):
        from sigil.lexer import tokenize  # noqa: F401

    def test_import_parser(self):
        from sigil.parser import parse  # noqa: F401

    def test_import_evaluator(self):
        from sigil.interpreter.evaluator import Evaluator  # noqa: F401

    def test_import_formatter(self):
        from sigil.formatter import format_program  # noqa: F401

    def test_import_linter(self):
        from sigil.linter import lint  # noqa: F401

    def test_import_generator(self):
        from sigil.generator import SigilGenerator  # noqa: F401

    def test_import_neural(self):
        from sigil.neural import ModelRegistry  # noqa: F401

    def test_import_ffi(self):
        from sigil.ffi.marshal import python_to_sigil  # noqa: F401


class TestCLIEntryPoint:
    def test_main_function_exists(self):
        from sigil.cli import main
        assert callable(main)
