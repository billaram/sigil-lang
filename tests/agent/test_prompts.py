"""Tests for the Sigil Code agent system prompt."""

from __future__ import annotations

from sigil.agent.prompts import (
    CRITICAL_CONSTRAINTS,
    SIGIL_SYNTAX_GUIDE,
    VALIDATED_EXAMPLES,
    build_agent_system_prompt,
)


class TestPromptContent:
    def test_prompt_includes_identity(self) -> None:
        prompt = build_agent_system_prompt()
        assert "Sigil Code" in prompt
        assert "AI coding assistant" in prompt

    def test_prompt_includes_syntax_guide(self) -> None:
        prompt = build_agent_system_prompt()
        assert "rule" in prompt
        assert "compute" in prompt
        assert "neural" in prompt
        assert "define" in prompt

    def test_prompt_includes_constraints(self) -> None:
        prompt = build_agent_system_prompt()
        assert "No ** Operator" in prompt
        assert "2 spaces" in prompt
        assert "pow()" in prompt

    def test_prompt_includes_examples(self) -> None:
        prompt = build_agent_system_prompt()
        assert "Temperature monitoring" in prompt or "compound_interest" in prompt

    def test_prompt_includes_workflow(self) -> None:
        prompt = build_agent_system_prompt()
        assert "validate" in prompt.lower()
        assert "write_file" in prompt or "write" in prompt.lower()


class TestConstraints:
    def test_valid_units_listed(self) -> None:
        assert "degrees" in CRITICAL_CONSTRAINTS
        assert "percent" in CRITICAL_CONSTRAINTS
        assert "seconds" in CRITICAL_CONSTRAINTS
        assert "milliseconds" in CRITICAL_CONSTRAINTS
        assert "dollars" in CRITICAL_CONSTRAINTS
        assert "confidence" in CRITICAL_CONSTRAINTS
        assert "years" in CRITICAL_CONSTRAINTS

    def test_no_double_star(self) -> None:
        # The prompt should mention ** as something NOT to use
        assert "**" in CRITICAL_CONSTRAINTS
        assert "pow" in CRITICAL_CONSTRAINTS

    def test_condition_operators(self) -> None:
        assert "exceeds" in CRITICAL_CONSTRAINTS
        assert "is below" in CRITICAL_CONSTRAINTS

    def test_indentation_rule(self) -> None:
        assert "2 spaces" in CRITICAL_CONSTRAINTS
        assert "NEVER 4" in CRITICAL_CONSTRAINTS


class TestSyntaxGuide:
    def test_keywords_listed(self) -> None:
        assert "rule" in SIGIL_SYNTAX_GUIDE
        assert "when" in SIGIL_SYNTAX_GUIDE
        assert "then" in SIGIL_SYNTAX_GUIDE
        assert "compute" in SIGIL_SYNTAX_GUIDE

    def test_stdlib_modules(self) -> None:
        assert "sigil.math" in SIGIL_SYNTAX_GUIDE
        assert "sigil.text" in SIGIL_SYNTAX_GUIDE
        assert "sigil.list" in SIGIL_SYNTAX_GUIDE


class TestExamples:
    def test_examples_use_valid_units(self) -> None:
        # Ensure examples don't use invalid unit suffixes
        invalid_units = ["days", "meters", "items", "minutes"]
        for unit in invalid_units:
            # Check that no number is immediately followed by invalid unit
            lines = VALIDATED_EXAMPLES.splitlines()
            for line in lines:
                # Skip comment lines
                if line.strip().startswith("--"):
                    continue
                words = line.split()
                for i, word in enumerate(words):
                    if word == unit and i > 0:
                        # Check if previous word is a number
                        try:
                            float(words[i - 1])
                            msg = f"Invalid unit suffix '{unit}' in example: {line}"
                            raise AssertionError(msg)
                        except ValueError:
                            pass

    def test_examples_no_double_star(self) -> None:
        assert "**" not in VALIDATED_EXAMPLES
