"""Tests for the NL-to-Sigil generator (mocked LLM backend)."""

from __future__ import annotations

from sigil.generator.generator import (
    GenerationResult,
    SigilGenerator,
    _clean_output,
)


class MockLLM:
    """Mock LLM that returns pre-configured Sigil code."""

    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[tuple[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self._response


class TestCleanOutput:
    def test_strips_markdown_fences(self):
        raw = "```sigil\ndefine X as 42\n```"
        assert _clean_output(raw) == "define X as 42\n"

    def test_strips_plain_fences(self):
        raw = "```\ndefine X as 42\n```"
        assert _clean_output(raw) == "define X as 42\n"

    def test_no_fences(self):
        raw = "define X as 42"
        assert _clean_output(raw) == "define X as 42\n"

    def test_trailing_whitespace(self):
        raw = "  define X as 42  \n  "
        result = _clean_output(raw)
        assert result.strip() == "define X as 42"


class TestSigilGenerator:
    def test_generate_valid_code(self):
        mock = MockLLM("define MAX_TEMP as 100\n")
        gen = SigilGenerator(backend=mock)
        result = gen.generate("a constant for max temperature")
        assert result.valid is True
        assert "define MAX_TEMP as 100" in result.code
        assert len(mock.calls) == 1

    def test_generate_with_context(self):
        mock = MockLLM("define X as 1\n")
        gen = SigilGenerator(backend=mock)
        gen.generate("a constant", context="for a math module")
        assert "math module" in mock.calls[0][1]

    def test_generate_invalid_code(self):
        mock = MockLLM("this is not valid sigil code {{{")
        gen = SigilGenerator(backend=mock)
        result = gen.generate("something")
        assert result.valid is False
        assert len(result.diagnostics) > 0

    def test_generate_strips_markdown(self):
        mock = MockLLM("```sigil\ndefine Y as 99\n```")
        gen = SigilGenerator(backend=mock)
        result = gen.generate("a constant Y")
        assert result.valid is True
        assert "define Y as 99" in result.code

    def test_refine_code(self):
        mock = MockLLM("define Z as 42\n")
        gen = SigilGenerator(backend=mock)
        result = gen.refine("define Z as ???\n", "parse error: invalid syntax")
        assert result.valid is True
        assert len(mock.calls) == 1

    def test_generation_result_fields(self):
        result = GenerationResult(
            code="define X as 1\n",
            valid=True,
            diagnostics=(),
            explanation="",
        )
        assert result.code == "define X as 1\n"
        assert result.valid is True
