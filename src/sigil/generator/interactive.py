"""Interactive multi-turn refinement loop for NL-to-Sigil generation."""

from __future__ import annotations

from sigil.generator.generator import GenerationResult, LLMBackend, SigilGenerator

MAX_REFINEMENT_ATTEMPTS = 3


def interactive_generate(
    description: str,
    backend: LLMBackend | None = None,
    max_attempts: int = MAX_REFINEMENT_ATTEMPTS,
) -> GenerationResult:
    """Generate Sigil code with automatic validation and refinement.

    Generates code, validates it, and if invalid, feeds errors back
    to the LLM for refinement up to max_attempts times.
    """
    generator = SigilGenerator(backend=backend)
    result = generator.generate(description)

    if result.valid:
        return result

    for _attempt in range(max_attempts):
        feedback = "\n".join(result.diagnostics)
        if not feedback:
            break

        result = generator.refine(result.code, feedback)
        if result.valid:
            return result

    return result
