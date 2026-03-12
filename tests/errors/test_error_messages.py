"""Tests for error message quality — suggestions, formatting, hints."""

from __future__ import annotations

from sigil.errors import (
    SigilError,
    SigilLexError,
    SigilParseError,
    SigilRuntimeError,
    SourceLocation,
    format_traceback,
)


class TestSuggestionInfrastructure:
    def test_error_with_suggestion(self):
        err = SigilError("bad thing", suggestion="try this instead")
        assert "hint: try this instead" in str(err)

    def test_error_without_suggestion(self):
        err = SigilError("bad thing")
        assert "hint" not in str(err)

    def test_error_with_location_and_suggestion(self):
        loc = SourceLocation("test.sigil", 5, 3)
        err = SigilParseError("expected X", loc, "add X here")
        msg = str(err)
        assert "test.sigil:5:3" in msg
        assert "expected X" in msg
        assert "hint: add X here" in msg

    def test_lex_error_with_suggestion(self):
        loc = SourceLocation("<stdin>", 1, 1)
        err = SigilLexError("Tabs not allowed", loc, "use spaces")
        assert "hint: use spaces" in str(err)

    def test_runtime_error_message_attribute(self):
        err = SigilRuntimeError("something failed")
        assert err.message == "something failed"
        assert err.suggestion is None

    def test_runtime_error_with_suggestion(self):
        err = SigilRuntimeError(
            "Undefined function: foo",
            suggestion="did you mean 'foobar'?",
        )
        assert "hint: did you mean 'foobar'?" in str(err)


class TestStackTraceFormatting:
    def test_runtime_error_with_call_stack(self):
        stack = (
            SourceLocation("test.sigil", 5, 1),
            SourceLocation("test.sigil", 10, 3),
        )
        err = SigilRuntimeError(
            "Division by zero", call_stack=stack,
        )
        msg = str(err)
        assert "Traceback" in msg
        assert "test.sigil:5:1" in msg
        assert "test.sigil:10:3" in msg
        assert "Division by zero" in msg

    def test_format_traceback_helper(self):
        err = SigilRuntimeError("oops")
        stack = [
            SourceLocation("a.sigil", 1, 1),
            SourceLocation("b.sigil", 2, 1),
        ]
        result = format_traceback(err, stack)
        assert "Traceback" in result
        assert "a.sigil:1:1" in result
        assert "oops" in result

    def test_format_traceback_no_stack(self):
        err = SigilRuntimeError("oops")
        result = format_traceback(err)
        assert "Traceback" not in result
        assert "oops" in result

    def test_format_traceback_with_suggestion(self):
        err = SigilRuntimeError("bad", suggestion="try this")
        result = format_traceback(err)
        assert "hint: try this" in result
