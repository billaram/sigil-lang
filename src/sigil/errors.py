"""Sigil error hierarchy and source location tracking."""

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

    def __init__(self, message: str, location: SourceLocation | None = None) -> None:
        self.location = location
        if location:
            super().__init__(f"{location}: {message}")
        else:
            super().__init__(message)


class SigilLexError(SigilError):
    """Error during tokenization."""


class SigilParseError(SigilError):
    """Error during parsing."""


class SigilTypeError(SigilError):
    """Error during type checking."""


class SigilRuntimeError(SigilError):
    """Error during interpretation."""
