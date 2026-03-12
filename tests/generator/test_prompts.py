"""Tests for the generator prompt assembly."""

from __future__ import annotations

from sigil.generator.prompts import (
    EXAMPLES,
    SYNTAX_REFERENCE,
    build_refinement_prompt,
    build_system_prompt,
)


class TestPrompts:
    def test_system_prompt_includes_syntax(self):
        prompt = build_system_prompt()
        assert "rule" in prompt
        assert "compute" in prompt
        assert "neural" in prompt
        assert "define" in prompt

    def test_system_prompt_includes_examples(self):
        prompt = build_system_prompt()
        assert "MAX_TEMP" in prompt
        assert "confidence_threshold" in prompt

    def test_syntax_reference_covers_keywords(self):
        for keyword in ["rule", "when", "then", "compute", "neural", "define"]:
            assert keyword in SYNTAX_REFERENCE

    def test_examples_are_valid_looking(self):
        assert "define" in EXAMPLES
        assert "rule" in EXAMPLES
        assert "neural" in EXAMPLES
        assert "compute" in EXAMPLES

    def test_refinement_prompt_includes_code_and_errors(self):
        prompt = build_refinement_prompt(
            code="define X as ???",
            errors="parse error at line 1",
        )
        assert "define X as ???" in prompt
        assert "parse error at line 1" in prompt
