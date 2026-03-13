"""NL-to-Sigil code generator using LLM backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationResult:
    """Result of generating Sigil code from natural language."""

    code: str
    valid: bool
    diagnostics: tuple[str, ...] = ()
    explanation: str = ""


class LLMBackend(Protocol):
    """Protocol for LLM backends used by the generator."""

    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class AnthropicLLM:
    """Anthropic Claude backend for code generation."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as err:
                msg = (
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
                raise ImportError(msg) from err
            self._client = anthropic.Anthropic()
        return self._client

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


class SigilGenerator:
    """Generates Sigil code from natural language descriptions."""

    def __init__(self, backend: LLMBackend | None = None) -> None:
        from sigil.generator.prompts import build_system_prompt

        self._backend = backend or AnthropicLLM()
        self._system_prompt = build_system_prompt()

    def generate(
        self, description: str, context: str | None = None,
    ) -> GenerationResult:
        """Generate Sigil code from a natural language description."""
        from sigil.generator.validator import validate_generated

        prompt = description
        if context:
            prompt = f"{description}\n\nContext:\n{context}"

        raw_code = self._backend.generate(self._system_prompt, prompt)
        code = _clean_output(raw_code)

        result = validate_generated(code)

        return GenerationResult(
            code=code,
            valid=result.valid,
            diagnostics=result.parse_errors + result.type_errors + result.warnings,
        )

    def refine(self, code: str, feedback: str) -> GenerationResult:
        """Refine previously generated code based on feedback."""
        from sigil.generator.prompts import build_refinement_prompt
        from sigil.generator.validator import validate_generated

        prompt = build_refinement_prompt(code, feedback)
        raw_code = self._backend.generate(self._system_prompt, prompt)
        refined = _clean_output(raw_code)

        result = validate_generated(refined)

        return GenerationResult(
            code=refined,
            valid=result.valid,
            diagnostics=result.parse_errors + result.type_errors + result.warnings,
        )


def _clean_output(text: str) -> str:
    """Strip markdown fences and leading/trailing whitespace from LLM output."""
    lines = text.strip().splitlines()

    # Remove markdown code fences
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines) + "\n"
