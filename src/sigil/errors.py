"""Sigil error hierarchy and source location tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    """A position in source code."""

    file: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


class SigilError(Exception):
    """Base for all Sigil errors."""

    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.message = message
        self.location = location
        self.suggestion = suggestion
        super().__init__(self._format())

    def _format(self) -> str:
        loc = f"{self.location}: " if self.location else ""
        hint = f"\n  hint: {self.suggestion}" if self.suggestion else ""
        return f"{loc}{self.message}{hint}"


class SigilLexError(SigilError):
    """Error during tokenization."""


class SigilParseError(SigilError):
    """Error during parsing."""


class SigilParseErrors(SigilParseError):  # noqa: N818 — plural is intentional
    """Multiple parse errors collected via error recovery."""

    def __init__(self, errors: list[SigilParseError]) -> None:
        self.errors = tuple(errors)
        count = len(errors)
        messages = [str(e) for e in errors]
        combined = "\n".join(messages)
        # Use the first error's location for the composite error
        first_loc = errors[0].location if errors else None
        super().__init__(f"{count} parse error(s):\n{combined}", first_loc)


class SigilTypeError(SigilError):
    """Error during type checking."""


class SigilRuntimeError(SigilError):
    """Error during interpretation."""

    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        suggestion: str | None = None,
        call_stack: tuple[SourceLocation, ...] | None = None,
    ) -> None:
        self.call_stack = call_stack
        super().__init__(message, location, suggestion)

    def _format(self) -> str:
        parts: list[str] = []
        if self.call_stack:
            parts.append("Traceback (most recent call last):")
            for frame in self.call_stack:
                parts.append(f"  {frame}")
        loc = f"{self.location}: " if self.location else ""
        parts.append(f"{loc}{self.message}")
        if self.suggestion:
            parts.append(f"  hint: {self.suggestion}")
        return "\n".join(parts)


def format_traceback(
    error: SigilRuntimeError,
    call_stack: list[SourceLocation] | None = None,
) -> str:
    """Format a runtime error with its call stack as a Sigil traceback."""
    stack = call_stack or (list(error.call_stack) if error.call_stack else [])
    parts: list[str] = []
    if stack:
        parts.append("Traceback (most recent call last):")
        for frame in stack:
            parts.append(f"  {frame}")
    parts.append(str(error.message))
    if error.suggestion:
        parts.append(f"  hint: {error.suggestion}")
    return "\n".join(parts)
