---
description: Module system patterns — loader, resolver, imports
globs: ["src/sigil/modules/**", "tests/modules/**"]
---

# Module System Development Guide

## Architecture

- `src/sigil/modules/resolver.py` — Module path resolution (stdlib, python, relative, project-relative)
- `src/sigil/modules/loader.py` — Module loading, caching, circular dependency detection
- Import evaluation in `evaluator.py` — selective, aliased, full import modes

## Import Modes

```sigil
import sigil.math                    -- full import (access as math.sqrt)
import sigil.math as m               -- aliased (access as m.sqrt)
from sigil.math import sqrt, floor   -- selective (access as sqrt, floor)
```

## Key Patterns

- `ExportDecl` AST node controls module visibility
- Loader caches modules after first load
- Circular dependency detection via loading set
- Dotted names accept keywords: `_expect_identifier_or_keyword()` allows `sigil.list`
- `list` is a keyword token — import paths like `sigil.list` need special handling

## Gotcha

Module tests use `Evaluator` directly (not `evaluate()`) for module loader config.

16 resolver tests, 17 loader tests, 16 import integration tests, 4 example tests.
