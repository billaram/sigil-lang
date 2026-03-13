"""Tests for the Sigil code generation validator."""

from __future__ import annotations

from sigil.generator.validator import validate_generated


class TestValidateGenerated:
    def test_valid_code(self):
        code = "define X as 42\n"
        result = validate_generated(code)
        assert result.valid is True
        assert len(result.parse_errors) == 0
        assert len(result.type_errors) == 0

    def test_valid_rule(self):
        code = (
            "define x as 150\n\n"
            "rule check:\n"
            "  when x exceeds 100\n"
            "  then alert\n"
        )
        result = validate_generated(code)
        assert result.valid is True

    def test_invalid_syntax(self):
        code = "rule check\n  missing colon\n"
        result = validate_generated(code)
        assert result.valid is False
        assert len(result.parse_errors) > 0

    def test_valid_compute(self):
        code = (
            "compute add from a: Number, b: Number returns Number:\n"
            "  return a + b\n"
        )
        result = validate_generated(code)
        assert result.valid is True

    def test_valid_neural(self):
        code = (
            "neural classify from text: Text:\n"
            '  model "hf:model"\n'
            "  returns Symbol\n"
            "  confidence_threshold 0.8\n"
            "  fallback to :unknown\n"
        )
        result = validate_generated(code)
        assert result.valid is True

    def test_empty_code(self):
        result = validate_generated("\n")
        assert result.valid is True
