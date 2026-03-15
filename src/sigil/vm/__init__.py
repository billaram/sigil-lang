"""Sigil Bytecode VM — compile AST to bytecode, execute in Rust VM."""

from sigil.vm.compiler import VMCompiler
from sigil.vm.runner import compile_and_run

__all__ = ["VMCompiler", "compile_and_run"]
