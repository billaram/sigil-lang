"""Tests for the interactive refinement loop."""

from __future__ import annotations

from sigil.generator.interactive import interactive_generate


class _MockLLM:
    """Mock LLM that returns different responses on successive calls."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._call_count = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]


class TestInteractiveGenerate:
    def test_valid_on_first_try(self):
        mock = _MockLLM(["define X as 42\n"])
        result = interactive_generate("a constant", backend=mock)
        assert result.valid is True
        assert mock._call_count == 1

    def test_refines_invalid_code(self):
        mock = _MockLLM([
            "this is broken {{{",  # First try: invalid
            "define X as 42\n",    # Refinement: valid
        ])
        result = interactive_generate("a constant", backend=mock)
        assert result.valid is True
        assert mock._call_count == 2

    def test_max_attempts_reached(self):
        mock = _MockLLM([
            "broken {{{",
            "still broken {{{",
            "also broken {{{",
            "forever broken {{{",
        ])
        result = interactive_generate("impossible", backend=mock, max_attempts=2)
        assert result.valid is False

    def test_returns_best_effort_on_failure(self):
        mock = _MockLLM(["not valid sigil at all {{{"])
        result = interactive_generate("something", backend=mock, max_attempts=0)
        assert result.valid is False
        assert len(result.code) > 0
