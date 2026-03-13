"""Formal verification for Sigil rule sets.

Uses BDD-based analysis (via Rust core) to check completeness,
conflicts, dead rules, and termination.
"""

from sigil.verifier.wrapper import verify_file, verify_program, VerificationReport

__all__ = ["verify_file", "verify_program", "VerificationReport"]
