"""Validation pipeline for generated Sigil code."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating generated Sigil code."""

    valid: bool
    parse_errors: tuple[str, ...] = ()
    type_errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_generated(code: str) -> ValidationResult:
    """Validate generated Sigil code through parse and type-check stages."""
    from sigil.errors import SigilError, SigilParseErrors
    from sigil.lexer import tokenize
    from sigil.parser import parse
    from sigil.types.checker import Severity, check

    # Stage 1: Parse
    try:
        tokens = tokenize(code, "<generated>")
        program = parse(tokens, "<generated>")
    except SigilParseErrors as e:
        return ValidationResult(
            valid=False,
            parse_errors=tuple(str(err) for err in e.errors),
        )
    except SigilError as e:
        return ValidationResult(
            valid=False,
            parse_errors=(str(e),),
        )

    # Stage 2: Type check
    result = check(program)

    type_errors = tuple(
        f"{d.location}: {d.message}"
        for d in result.diagnostics
        if d.severity == Severity.ERROR
    )
    warnings = tuple(
        f"{d.location}: {d.message}"
        for d in result.diagnostics
        if d.severity == Severity.WARNING
    )

    return ValidationResult(
        valid=len(type_errors) == 0,
        type_errors=type_errors,
        warnings=warnings,
    )
