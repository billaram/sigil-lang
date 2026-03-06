"""Shared test fixtures for Sigil tests."""

from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.fixture
def hello_source() -> str:
    return (EXAMPLES_DIR / "basics" / "hello.sigil").read_text()


@pytest.fixture
def temperature_source() -> str:
    return (EXAMPLES_DIR / "basics" / "temperature.sigil").read_text()


@pytest.fixture
def loan_source() -> str:
    return (EXAMPLES_DIR / "rules" / "loan_eligibility.sigil").read_text()


@pytest.fixture
def triage_source() -> str:
    return (EXAMPLES_DIR / "neuro_symbolic" / "medical_triage.sigil").read_text()


@pytest.fixture
def compliance_source() -> str:
    return (EXAMPLES_DIR / "neuro_symbolic" / "compliance_checker.sigil").read_text()
