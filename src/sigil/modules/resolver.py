"""Module path resolution for the Sigil module system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResolvedModule:
    """Result of resolving a module path."""

    kind: str  # "sigil", "stdlib", "stdlib_builtin", "python"
    path: Path | None = None
    name: str | None = None


class ModuleNotFoundError(Exception):
    """Raised when a module cannot be resolved."""


class ModuleResolver:
    """Resolves module paths to file locations."""

    def __init__(self, project_root: Path, stdlib_root: Path) -> None:
        self.project_root = project_root
        self.stdlib_root = stdlib_root

    def resolve(self, module_path: str, importing_file: Path) -> ResolvedModule:
        """Resolve a module path to a file location.

        Resolution order:
        1. Standard library (sigil.*)
        2. Python import (python *)
        3. Relative import (./ or ../)
        4. Project-relative import (dotted path)
        """
        # 1. Standard library (sigil.*)
        if module_path.startswith("sigil."):
            stdlib_name = module_path.removeprefix("sigil.")
            stdlib_file = self.stdlib_root / f"{stdlib_name}.sigil"
            if stdlib_file.exists():
                return ResolvedModule(kind="stdlib", path=stdlib_file)
            return ResolvedModule(kind="stdlib_builtin", name=stdlib_name)

        # 2. Python import
        if module_path.startswith("python "):
            python_name = module_path.removeprefix("python ")
            return ResolvedModule(kind="python", name=python_name)

        # 3. Relative import
        if module_path.startswith("./") or module_path.startswith("../"):
            resolved = (importing_file.parent / module_path).with_suffix(".sigil")
            if resolved.exists():
                return ResolvedModule(kind="sigil", path=resolved.resolve())
            msg = f"Module not found: {module_path}"
            raise ModuleNotFoundError(msg)

        # 4. Project-relative import (dotted path)
        parts = module_path.split(".")
        resolved = self.project_root / Path(*parts).with_suffix(".sigil")
        if resolved.exists():
            return ResolvedModule(kind="sigil", path=resolved.resolve())

        msg = f"Module not found: {module_path}"
        raise ModuleNotFoundError(msg)
