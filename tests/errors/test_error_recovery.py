"""Tests for parser error recovery — multiple errors collected."""

from __future__ import annotations

import pytest

from sigil.errors import SigilParseError, SigilParseErrors
from sigil.lexer import tokenize
from sigil.parser import parse


def parse_source(source: str) -> None:
    tokens = tokenize(source, "<test>")
    parse(tokens, "<test>")


class TestParserRecovery:
    def test_single_error_wrapped_in_parse_errors(self):
        """A single bad declaration raises SigilParseErrors with 1 error."""
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source("42\n")
        assert len(exc_info.value.errors) == 1

    def test_two_bad_declarations(self):
        """Parser recovers after first bad decl and catches second."""
        source = "42\n99\n"
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source(source)
        assert len(exc_info.value.errors) >= 1

    def test_bad_decl_then_good_decl(self):
        """Parser recovers from bad decl and continues to parse good ones."""
        source = "42\ndefine X as 10\n"
        # Should still raise because there's at least one error
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source(source)
        assert len(exc_info.value.errors) == 1

    def test_good_decl_then_bad_decl(self):
        """Error in second declaration doesn't affect first."""
        source = "define X as 10\n42\n"
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source(source)
        assert len(exc_info.value.errors) == 1

    def test_parse_errors_is_subclass_of_parse_error(self):
        """SigilParseErrors is catchable as SigilParseError."""
        with pytest.raises(SigilParseError):
            parse_source("42\n")

    def test_missing_colon_recovery(self):
        """Missing colon on rule recovers to next declaration."""
        source = (
            "rule bad_rule\n"
            "  when true\n"
            "  then alert\n"
            "define X as 10\n"
        )
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source(source)
        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "COLON" in str(errors[0])

    def test_multiple_bad_rules(self):
        """Multiple rules with errors — all collected."""
        source = (
            "rule a\n"
            "  when true\n"
            "rule b\n"
            "  when false\n"
        )
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source(source)
        assert len(exc_info.value.errors) >= 2

    def test_error_has_suggestion(self):
        """Top-level unexpected token includes a suggestion."""
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source("42\n")
        err = exc_info.value.errors[0]
        assert err.suggestion is not None
        assert "declarations must start with" in err.suggestion

    def test_colon_suggestion(self):
        """Missing colon gives helpful hint."""
        with pytest.raises(SigilParseErrors) as exc_info:
            parse_source("rule test\n  when true\n  then alert\n")
        err = exc_info.value.errors[0]
        assert err.suggestion is not None
        assert "':'" in err.suggestion

    def test_no_errors_on_valid_program(self):
        """Valid program doesn't raise."""
        source = "define X as 42\n"
        parse_source(source)  # Should not raise
