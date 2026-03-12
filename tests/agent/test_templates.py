"""Tests for Sigil Code agent project templates."""

from __future__ import annotations

import pytest

from sigil.agent.templates import TEMPLATES, get_template, list_templates
from sigil.generator.validator import validate_generated


class TestTemplateRegistry:
    def test_list_templates(self) -> None:
        names = list_templates()
        assert "basic" in names
        assert "rules" in names
        assert "neural" in names
        assert "full" in names

    def test_get_existing(self) -> None:
        template = get_template("basic")
        assert template is not None
        assert template.name == "basic"

    def test_get_nonexistent(self) -> None:
        assert get_template("nonexistent") is None

    def test_all_templates_have_files(self) -> None:
        for name, template in TEMPLATES.items():
            assert len(template.files) > 0, f"{name} has no files"
            assert template.description, f"{name} has no description"


class TestTemplateValidation:
    """Validate that all .sigil files in templates pass the Sigil toolchain."""

    @pytest.mark.parametrize("template_name", list_templates())
    def test_template_sigil_files_valid(self, template_name: str) -> None:
        template = get_template(template_name)
        assert template is not None
        for tf in template.files:
            if not tf.path.endswith(".sigil"):
                continue
            result = validate_generated(tf.content)
            assert result.valid, (
                f"Template '{template_name}' file '{tf.path}' failed "
                f"validation:\n"
                f"  parse_errors: {result.parse_errors}\n"
                f"  type_errors: {result.type_errors}"
            )
