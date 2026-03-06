# Sigil — Phase 2 Sprint 2: Module System + Standard Library

## Prerequisites

**Sprint 1 must be complete** (pattern matching, pipeline, closures — 450+ tests).

---

## Sprint 2 Goal

> **Deliver a working module system with import/export, file resolution, and circular dependency detection. Build the standard library (math, text, list, logic modules). Write examples using multi-file programs.**

### Sprint 2 Exit Criteria
- [ ] `import` statements resolve and load Sigil modules from the file system
- [ ] `from module import name` selectively imports declarations
- [ ] `export` controls visibility — only exported names are importable
- [ ] Circular dependency detection with clear error messages
- [ ] Module caching — each module loaded only once
- [ ] Standard library: `sigil.math`, `sigil.text`, `sigil.list`, `sigil.logic` modules
- [ ] Python FFI stubs: `import python module.name` resolves to Python callable
- [ ] 5+ new multi-file examples demonstrating module usage
- [ ] 70+ new tests → 520+ total
- [ ] All existing tests still pass (no regressions)

---

## What Must Be Built

### Module System Architecture

Currently:
- Parser produces `ModuleDecl` and `ImportDecl` AST nodes
- Evaluator ignores them entirely
- No file loading, no module resolution, no caching

Need:
1. **Module resolver**: Given a module path like `rules.eligibility`, find the .sigil file
2. **Module loader**: Lex → parse → type-check → evaluate a module file
3. **Module cache**: Don't re-load the same module twice
4. **Export tracking**: Only exported names are visible to importers
5. **Circular dependency detection**: Track loading stack, error on cycles
6. **Python import bridge**: `import python math` → wrap Python module as Sigil bindings

### Standard Library Architecture

The stdlib ships as .sigil files (for transparency and dogfooding) plus Python-backed builtins (for performance and system access).

Structure:
```
src/sigil/stdlib/
├── __init__.py          — stdlib module registry
├── _builtins.py         — Python-implemented builtin functions
├── math.sigil           — math module (wraps Python math)
├── text.sigil           — text/string operations
├── list.sigil            — list operations
└── logic.sigil           — boolean/logic operations
```

Some stdlib functions are implemented in Python (math.sqrt needs Python's math module), exposed as Sigil builtins. Others are pure Sigil.

---

## Step-by-Step Implementation Plan

### Step 1: Module Resolver

**File**: `src/sigil/modules/resolver.py` (NEW)

Module resolution rules (in order):
1. **Relative path**: `import ./helpers` → `./helpers.sigil` relative to importing file
2. **Project path**: `import rules.eligibility` → `<project_root>/rules/eligibility.sigil`
3. **Standard library**: `import sigil.math` → bundled stdlib module
4. **Python module**: `import python math` → Python import bridge

```python
from pathlib import Path

class ModuleResolver:
    """Resolves module paths to file locations."""

    def __init__(self, project_root: Path, stdlib_root: Path) -> None:
        self.project_root = project_root
        self.stdlib_root = stdlib_root

    def resolve(self, module_path: str, importing_file: Path) -> ResolvedModule:
        """Resolve a module path to a file location.

        Returns ResolvedModule with kind (sigil/python/stdlib) and path.
        """
        # 1. Standard library (sigil.*)
        if module_path.startswith("sigil."):
            stdlib_name = module_path.removeprefix("sigil.")
            stdlib_file = self.stdlib_root / f"{stdlib_name}.sigil"
            if stdlib_file.exists():
                return ResolvedModule(kind="stdlib", path=stdlib_file)
            # Fall through to Python-backed stdlib
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
            raise ModuleNotFoundError(f"Module not found: {module_path}")

        # 4. Project-relative import (dotted path)
        parts = module_path.split(".")
        resolved = self.project_root / Path(*parts).with_suffix(".sigil")
        if resolved.exists():
            return ResolvedModule(kind="sigil", path=resolved.resolve())

        raise ModuleNotFoundError(f"Module not found: {module_path}")

@dataclass
class ResolvedModule:
    kind: str              # "sigil", "stdlib", "stdlib_builtin", "python"
    path: Path | None = None
    name: str | None = None
```

### Step 2: Module Loader and Cache

**File**: `src/sigil/modules/loader.py` (NEW)

```python
class ModuleLoader:
    """Loads and caches Sigil modules."""

    def __init__(self, resolver: ModuleResolver) -> None:
        self.resolver = resolver
        self._cache: dict[Path, Module] = {}
        self._loading: set[Path] = set()  # cycle detection

    def load(self, module_path: str, importing_file: Path) -> Module:
        """Load a module by path. Returns cached if already loaded."""
        resolved = self.resolver.resolve(module_path, importing_file)

        if resolved.kind == "python":
            return self._load_python_module(resolved.name)

        if resolved.kind == "stdlib_builtin":
            return self._load_stdlib_builtin(resolved.name)

        # File-based module (sigil or stdlib)
        if resolved.path in self._cache:
            return self._cache[resolved.path]

        if resolved.path in self._loading:
            cycle = " -> ".join(str(p) for p in self._loading)
            raise SigilImportError(
                f"Circular dependency detected: {cycle} -> {resolved.path}"
            )

        return self._load_sigil_file(resolved.path)

    def _load_sigil_file(self, path: Path) -> Module:
        """Load a .sigil file as a module."""
        self._loading.add(path)
        try:
            source = path.read_text()
            tokens = tokenize(source, str(path))
            program = parse(tokens, str(path))

            # Type-check the module
            check_result = check(program)
            if check_result.has_errors:
                raise SigilImportError(
                    f"Type errors in module {path}: {check_result.error_count} errors"
                )

            # Evaluate the module (creates environment with declarations)
            evaluator = Evaluator()
            evaluator.module_loader = self  # for nested imports
            _, trace = evaluator.eval_program(program)

            # Build module from evaluator state
            module = Module(
                path=path,
                env=evaluator._module_env,
                exports=evaluator._exports,
                compute_funcs=evaluator._compute_funcs,
                type_defs=evaluator._type_defs,
            )

            self._cache[path] = module
            return module
        finally:
            self._loading.discard(path)

    def _load_python_module(self, name: str) -> Module:
        """Load a Python module and wrap its functions."""
        import importlib
        py_mod = importlib.import_module(name)
        # Wrap Python functions as Sigil builtins
        bindings: dict[str, Value] = {}
        for attr_name in dir(py_mod):
            if attr_name.startswith("_"):
                continue
            attr = getattr(py_mod, attr_name)
            if callable(attr):
                bindings[attr_name] = _wrap_python_callable(attr)
        return Module(path=None, env=Environment(bindings), exports=set(bindings))

    def _load_stdlib_builtin(self, name: str) -> Module:
        """Load a Python-backed stdlib module."""
        from sigil.stdlib import get_stdlib_module
        return get_stdlib_module(name)
```

### Step 3: Export System

**File**: `src/sigil/ast/nodes.py` — verify `ExportDecl` exists or add it

```python
@dataclass(frozen=True)
class ExportDecl(Node):
    """Export declaration: export name1, name2, ..."""
    names: tuple[str, ...]
```

**File**: `src/sigil/parser/parser.py` — parse `export` statements

If the parser doesn't already handle `export`, add:
```python
def _parse_export_decl(self) -> ast.ExportDecl:
    loc = self._loc()
    self._expect(TokenType.EXPORT)
    names = [self._expect(TokenType.IDENTIFIER).value]
    while self._match(TokenType.COMMA):
        names.append(self._expect(TokenType.IDENTIFIER).value)
    return ast.ExportDecl(location=loc, names=tuple(names))
```

**File**: `src/sigil/interpreter/evaluator.py` — track exports

```python
# In Evaluator.__init__:
self._exports: set[str] = set()
self._module_env: Environment = Environment()

# When processing export declarations:
if isinstance(decl, ast.ExportDecl):
    self._exports.update(decl.names)

# If no explicit exports, all top-level names are exported (default)
```

### Step 4: Import Evaluation

**File**: `src/sigil/interpreter/evaluator.py` — handle `ImportDecl`

```python
def _eval_import(self, decl: ast.ImportDecl, env: Environment) -> Environment:
    """Evaluate an import declaration."""
    if not self.module_loader:
        raise SigilRuntimeError("Module loading not available (no module loader configured)")

    module = self.module_loader.load(decl.source, Path(self.filename))

    if decl.names:
        # Selective import: from X import a, b, c
        for name in decl.names:
            if name not in module.exports:
                raise SigilImportError(f"'{name}' is not exported from module '{decl.source}'")
            val = module.env.get(name)
            env = env.set(name, val)
    elif decl.alias:
        # Aliased import: import X as Y
        # Bind the entire module as a record
        module_record = Record(type_name=decl.alias, fields=dict(module.env.bindings()))
        env = env.set(decl.alias, module_record)
    else:
        # Full import: import X
        # Bind exported names directly
        for name in module.exports:
            val = module.env.get(name)
            env = env.set(name, val)

    return env
```

### Step 5: Standard Library — math module

**File**: `src/sigil/stdlib/_builtins.py` (NEW)

Python-implemented math functions:

```python
import math as _math
from sigil.interpreter.values import Value

def stdlib_sqrt(args: list[Value], _trace) -> Value:
    return _math.sqrt(args[0])

def stdlib_abs(args: list[Value], _trace) -> Value:
    return abs(args[0])

def stdlib_floor(args: list[Value], _trace) -> Value:
    return _math.floor(args[0])

def stdlib_ceil(args: list[Value], _trace) -> Value:
    return _math.ceil(args[0])

def stdlib_round(args: list[Value], _trace) -> Value:
    if len(args) == 2:
        return round(args[0], int(args[1]))
    return round(args[0])

def stdlib_pow(args: list[Value], _trace) -> Value:
    return args[0] ** args[1]

def stdlib_log(args: list[Value], _trace) -> Value:
    return _math.log(args[0])

def stdlib_sin(args: list[Value], _trace) -> Value:
    return _math.sin(args[0])

def stdlib_cos(args: list[Value], _trace) -> Value:
    return _math.cos(args[0])

# Registry
STDLIB_MATH = {
    "sqrt": stdlib_sqrt,
    "abs": stdlib_abs,
    "floor": stdlib_floor,
    "ceil": stdlib_ceil,
    "round": stdlib_round,
    "pow": stdlib_pow,
    "log": stdlib_log,
    "sin": stdlib_sin,
    "cos": stdlib_cos,
    "max": builtin_max,   # from builtins.py
    "min": builtin_min,
    "PI": _math.pi,
    "E": _math.e,
}
```

**File**: `src/sigil/stdlib/__init__.py` — stdlib module registry

```python
from sigil.stdlib._builtins import STDLIB_MATH, STDLIB_TEXT, STDLIB_LIST, STDLIB_LOGIC

def get_stdlib_module(name: str) -> Module:
    """Get a stdlib module by name."""
    registry = {
        "math": STDLIB_MATH,
        "text": STDLIB_TEXT,
        "list": STDLIB_LIST,
        "logic": STDLIB_LOGIC,
    }
    if name not in registry:
        raise SigilImportError(f"Unknown stdlib module: sigil.{name}")
    return Module.from_builtins(name, registry[name])
```

### Step 6: Standard Library — text module

**File**: `src/sigil/stdlib/_builtins.py` — add text functions

```python
def stdlib_length(args, _trace):
    return len(args[0])

def stdlib_substring(args, _trace):
    s, start, end = args[0], int(args[1]), int(args[2])
    return s[start:end]

def stdlib_split(args, _trace):
    return args[0].split(args[1]) if len(args) > 1 else args[0].split()

def stdlib_join(args, _trace):
    return args[1].join(str(x) for x in args[0])

def stdlib_lowercase(args, _trace):
    return args[0].lower()

def stdlib_uppercase(args, _trace):
    return args[0].upper()

def stdlib_trim(args, _trace):
    return args[0].strip()

def stdlib_replace(args, _trace):
    return args[0].replace(args[1], args[2])

def stdlib_starts_with(args, _trace):
    return args[0].startswith(args[1])

def stdlib_ends_with(args, _trace):
    return args[0].endswith(args[1])

STDLIB_TEXT = {
    "length": stdlib_length,
    "substring": stdlib_substring,
    "split": stdlib_split,
    "join": stdlib_join,
    "lowercase": stdlib_lowercase,
    "uppercase": stdlib_uppercase,
    "trim": stdlib_trim,
    "replace": stdlib_replace,
    "starts_with": stdlib_starts_with,
    "ends_with": stdlib_ends_with,
}
```

### Step 7: Standard Library — list module

```python
def stdlib_range(args, _trace):
    if len(args) == 1:
        return list(range(int(args[0])))
    if len(args) == 2:
        return list(range(int(args[0]), int(args[1])))
    return list(range(int(args[0]), int(args[1]), int(args[2])))

def stdlib_reverse(args, _trace):
    return list(reversed(args[0]))

def stdlib_flatten(args, _trace):
    result = []
    for item in args[0]:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result

def stdlib_unique(args, _trace):
    seen = []
    result = []
    for item in args[0]:
        if not any(values_equal(item, s) for s in seen):
            seen.append(item)
            result.append(item)
    return result

def stdlib_zip_lists(args, _trace):
    return [Record(None, {"first": a, "second": b}) for a, b in zip(args[0], args[1])]

def stdlib_sum(args, _trace):
    return sum(args[0])

def stdlib_count(args, _trace):
    return len(args[0])

STDLIB_LIST = {
    "range": stdlib_range,
    "reverse": stdlib_reverse,
    "flatten": stdlib_flatten,
    "unique": stdlib_unique,
    "zip": stdlib_zip_lists,
    "sum": stdlib_sum,
    "count": stdlib_count,
    "length": stdlib_length,  # shared with text
}
```

### Step 8: Standard Library — logic module

```python
def stdlib_xor(args, _trace):
    return bool(args[0]) != bool(args[1])

def stdlib_implies(args, _trace):
    return not bool(args[0]) or bool(args[1])

def stdlib_nand(args, _trace):
    return not (bool(args[0]) and bool(args[1]))

def stdlib_type_of(args, _trace):
    v = args[0]
    if isinstance(v, bool):
        return Symbol("Boolean")
    if isinstance(v, int):
        return Symbol("Number")
    if isinstance(v, float):
        return Symbol("Number")
    if isinstance(v, str):
        return Symbol("Text")
    if isinstance(v, Symbol):
        return Symbol("Symbol")
    if isinstance(v, Record):
        return Symbol("Record")
    if isinstance(v, list):
        return Symbol("List")
    if v is None:
        return Symbol("None")
    return Symbol("Unknown")

def stdlib_is_number(args, _trace):
    return isinstance(args[0], (int, float))

def stdlib_is_text(args, _trace):
    return isinstance(args[0], str)

def stdlib_is_list(args, _trace):
    return isinstance(args[0], list)

STDLIB_LOGIC = {
    "xor": stdlib_xor,
    "implies": stdlib_implies,
    "nand": stdlib_nand,
    "type_of": stdlib_type_of,
    "is_number": stdlib_is_number,
    "is_text": stdlib_is_text,
    "is_list": stdlib_is_list,
}
```

### Step 9: Multi-File Example Programs

**File**: `examples/modules/math_utils.sigil`

```sigil
-- Reusable math utilities
module math_utils

export percentage, clamp, interpolate

compute percentage from value: Number, total: Number returns Number:
  return (value / total) * 100

compute clamp from value: Number, low: Number, high: Number returns Number:
  if value is below low:
    return low
  if value exceeds high:
    return high
  return value

compute interpolate from a: Number, b: Number, t: Number returns Number:
  return a + (b - a) * t
```

**File**: `examples/modules/scoring.sigil`

```sigil
-- Risk scoring module using math utilities
module scoring

import math_utils

export calculate_risk_score, risk_category

compute calculate_risk_score from age: Number, income: Number, debt: Number returns Number:
  given age_factor as clamp(age, 18, 65) / 65 * 30
  given income_factor as clamp(income, 0, 200000) / 200000 * 40
  given debt_factor as (1 - clamp(debt, 0, 100) / 100) * 30
  return age_factor + income_factor + debt_factor

compute risk_category from score: Number returns Symbol:
  return match score:
    _ -> :unknown
```

**File**: `examples/modules/main_scoring.sigil`

```sigil
-- Main entry point that imports modules
from scoring import calculate_risk_score, risk_category

main:
  given score as calculate_risk_score(35, 85000, 28)
  given category as risk_category(score)
  print(score)
  print(category)
```

Additional module examples:
- `examples/modules/validators.sigil` — shared validation rules
- `examples/modules/formatters.sigil` — output formatting
- `examples/modules/main_validation.sigil` — imports and uses validators

### Step 10: Tests

**Test files:**

```
tests/modules/test_resolver.py         — 15+ tests for module path resolution
tests/modules/test_loader.py           — 15+ tests for module loading and caching
tests/modules/test_imports.py          — 15+ tests for import evaluation
tests/modules/test_circular.py         — 5+ tests for circular dependency detection
tests/stdlib/test_math.py              — 10+ tests for math stdlib
tests/stdlib/test_text.py              — 10+ tests for text stdlib
tests/stdlib/test_list.py              — 10+ tests for list stdlib
tests/stdlib/test_logic.py             — 5+ tests for logic stdlib
tests/integration/test_module_examples.py — 5+ integration tests for multi-file examples
```

Target: **70+ new tests** → 520+ total

---

## Files to Create/Modify

### New files (15+)
```
src/sigil/modules/__init__.py
src/sigil/modules/resolver.py        — Module path resolution
src/sigil/modules/loader.py          — Module loading, caching, cycle detection
src/sigil/stdlib/_builtins.py        — Python-backed stdlib functions
tests/modules/__init__.py
tests/modules/test_resolver.py
tests/modules/test_loader.py
tests/modules/test_imports.py
tests/modules/test_circular.py
tests/stdlib/__init__.py
tests/stdlib/test_math.py
tests/stdlib/test_text.py
tests/stdlib/test_list.py
tests/stdlib/test_logic.py
tests/integration/test_module_examples.py
examples/modules/math_utils.sigil
examples/modules/scoring.sigil
examples/modules/main_scoring.sigil
examples/modules/validators.sigil
examples/modules/main_validation.sigil
```

### Modified files (5)
```
src/sigil/ast/nodes.py               — ExportDecl node (if not present)
src/sigil/parser/parser.py           — Parse export statements
src/sigil/interpreter/evaluator.py   — Import evaluation, module_loader integration
src/sigil/stdlib/__init__.py         — Stdlib registry
src/sigil/cli.py                     — Configure module loader in run/check commands
```

---

## Implementation Order

### Phase A: Module Infrastructure (Steps 1–4)

1. Module resolver (path → file)
2. Module loader with caching and cycle detection
3. Export tracking in evaluator
4. Import evaluation in evaluator

**PAUSE — test with simple two-file import**

### Phase B: Standard Library (Steps 5–8)

5. Math stdlib (sqrt, abs, floor, ceil, round, pow, log, sin, cos, PI, E)
6. Text stdlib (length, substring, split, join, lowercase, uppercase, trim, replace)
7. List stdlib (range, reverse, flatten, unique, zip, sum, count)
8. Logic stdlib (xor, implies, nand, type_of, is_number, is_text, is_list)

**PAUSE — test stdlib functions in REPL**

### Phase C: Examples + Tests + Polish (Steps 9–10)

9. Multi-file example programs
10. Full test suite (70+ new tests)

**DONE — Sprint 2 complete**

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Module resolution rules are complex | Medium | Medium | Start with 3 rules (stdlib, project, relative), add more later |
| Circular dependencies hard to debug | Medium | Medium | Clear error message showing the dependency chain |
| Python FFI type marshaling edge cases | Medium | Low | Defer complex types, start with numbers/strings/lists |
| Stdlib scope creep | High | Medium | Fixed set: math, text, list, logic for Sprint 2. time, io, trace = Sprint 3 |
| Module caching invalidation | Low | Low | Cache by file path, no invalidation (restart to reload) |
| Import * (wildcard) namespace pollution | Low | Low | Don't support wildcard imports — always explicit |

---

## Definition of Done (Sprint 2)

```bash
# All of these must work:
sigil run examples/modules/main_scoring.sigil              # multi-file import works
sigil run examples/features/pattern_matching.sigil          # Sprint 1 still works
sigil run examples/basics/hello.sigil                       # Phase 1 still works
sigil check examples/modules/scoring.sigil                  # type check on module
pytest tests/ -v                                            # 520+ tests, all passing
ruff check src/ tests/                                      # clean
mypy src/sigil/ --ignore-missing-imports                    # clean
```
