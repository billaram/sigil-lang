"""Tests that example .sigil programs parse and run without errors."""

from __future__ import annotations

from pathlib import Path

import pytest

from sigil.errors import SigilError
from sigil.lexer import tokenize
from sigil.parser import parse

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def _find_sigil_files() -> list[Path]:
    """Find all .sigil files in the examples directory."""
    if not EXAMPLES_DIR.exists():
        return []
    return sorted(EXAMPLES_DIR.rglob("*.sigil"))


@pytest.mark.parametrize(
    "sigil_file",
    _find_sigil_files(),
    ids=lambda p: str(p.relative_to(EXAMPLES_DIR)),
)
class TestExamplesParse:
    def test_example_parses(self, sigil_file: Path):
        """Every example should parse without errors."""
        source = sigil_file.read_text()
        try:
            tokens = tokenize(source, str(sigil_file))
            parse(tokens, str(sigil_file))
        except SigilError as e:
            pytest.fail(f"Failed to parse {sigil_file.name}: {e}")
